"""One bounded, offline development experiment; file I/O and publication live here."""

import argparse
import hashlib
import importlib.metadata
import json
import math
import multiprocessing
import os
import platform
import re
import resource
import signal
import subprocess
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from reprolab.experiment import (
    evaluate_predictions,
    fit_predict,
    load_concrete,
    remove_duplicates,
    select_features_target,
    split_data,
)
from reprolab.manifest import LockedManifest, canonical_json, development_manifest, fingerprint


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _safe_path(value, *, directory=False):
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Paths must be absolute and contain no parent traversal")
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlink paths are unsupported")
    if not (path.is_dir() if directory else path.is_file()):
        raise FileNotFoundError("Required regular file or directory is missing")
    return path


def _unique_fields(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("Duplicate manifest JSON fields are unsupported")
    return result


def _load_manifest(source, expected, lock):
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Expected fingerprint must be a lowercase SHA-256")
    if source == "development":
        manifest = development_manifest(_digest(lock))
    else:
        path = _safe_path(source)
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("Manifest exceeds the 1 MiB limit")
        raw = path.read_bytes()
        json.loads(raw, object_pairs_hook=_unique_fields)
        manifest = LockedManifest.model_validate_json(raw)
    if fingerprint(manifest) != expected:
        raise ValueError("Manifest fingerprint differs from the explicitly approved fingerprint")
    if manifest.environment.uv_lock_sha256 != _digest(lock):
        raise ValueError("Environment lockfile SHA-256 mismatch")
    return manifest


def _environment(manifest, lock):
    """Compare actual runtime, every installed distribution, and the offline lock."""
    uv = subprocess.run(["uv", "--version"], capture_output=True, text=True, check=True, timeout=10)
    versions = {
        d.metadata["Name"].lower().replace("_", "-"): d.version
        for d in importlib.metadata.distributions()
    }
    expected = {
        p["name"]: p["version"]
        for p in tomllib.loads(lock.decode())["package"]
        if p["name"] != "reprolab" and not (p["name"] == "colorama" and os.name != "nt")
    }
    env = manifest.environment
    if (
        versions != expected
        or platform.python_version() != env.python
        or uv.stdout.split()[:2] != ["uv", env.uv]
        or versions.get("scikit-learn") != env.sklearn
        or versions.get("pydantic") != env.pydantic
    ):
        raise ValueError("Actual software versions differ from the manifest/lock")
    checked = subprocess.run(
        ["uv", "lock", "--check", "--offline"], capture_output=True, timeout=10
    )
    if checked.returncode:
        raise ValueError("Offline dependency-lock validation failed")
    return {
        "python": platform.python_version(),
        "uv": env.uv,
        "packages": versions,
        "system": platform.system(),
        "machine": platform.machine(),
        "threads": {
            name: os.environ[name]
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "uv_lock_sha256": _digest(lock),
    }


def _execute(args):
    """Worker reads approved inputs and computes; it never writes run artifacts."""
    lock = _safe_path("/app/uv.lock").read_bytes()
    manifest = _load_manifest(args.manifest, args.expected_manifest_sha256, lock)
    environment = _environment(manifest, lock)
    raw = load_concrete(_safe_path(args.input))
    clean, duplicate_of = remove_duplicates(raw, expected_rows=manifest.preprocessing.expected_rows)
    train, test = split_data(clean, seed=manifest.split.seed.value)
    params = {
        name: getattr(manifest.model, name).value
        for name in ("fit_intercept", "positive", "copy_X", "n_jobs")
    }
    predictions = fit_predict(train, test, **params)
    _, targets = select_features_target(test)
    protocols = {m.name: m for m in manifest.metrics}
    metrics = evaluate_predictions(
        targets,
        predictions,
        mape_zero_policy=protocols["MAPE"].zero_target_policy.value,
        nrmse_ddof=protocols["nRMSE"].ddof.value,
    )
    for name, measured in metrics.items():
        protocol = protocols[name]
        measured["definition"] = protocol.definition.model_dump(mode="json")
        if name == "nRMSE":
            measured["ddof_provenance"] = protocol.ddof.model_dump(mode="json")
        if name == "MAPE":
            measured["zero_policy_provenance"] = protocol.zero_target_policy.model_dump(mode="json")

    sources = {p.name: _digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob("*.py"))}
    git_commit = os.environ.get("REPROLAB_GIT_COMMIT")
    if git_commit is not None and not re.fullmatch(r"[0-9a-f]{40}", git_commit):
        raise ValueError("Caller-supplied Git revision must be a full lowercase SHA")
    usage = resource.getrusage(resource.RUSAGE_SELF)
    results = {
        "results_schema_version": 1,
        "run_id": args.run_id,
        "execution_status": "COMPLETED",
        "experiment_classification": "INDEPENDENT_REIMPLEMENTATION",
        "reproduction_status": "INCONCLUSIVE",
        "protocol_limitations": [
            "Published holdout seed and final LR settings are unresolved",
            "Seed 123 is author-code-derived; LR parameters are human-selected development choices",
            "Exact approved PDF bytes/version are unresolved; no verified PDF hash",
            "nRMSE ddof=0 and MAPE retained-term policy are author-code-derived",
            "Development Python/NumPy/SciPy environment differs from historical declarations",
        ],
        "manifest_sha256": fingerprint(manifest),
        # load_concrete verified these exact bytes and parsed the same in-memory bytes.
        "dataset_sha256": manifest.dataset.sha256.value,
        "split": {
            "seed": manifest.split.seed.value,
            "raw_rows": len(raw.rows),
            "cleaned_rows": len(clean.rows),
            "duplicates_removed": len(duplicate_of),
            "train_rows": len(train.rows),
            "test_rows": len(test.rows),
            "row_ids_sha256": _digest(
                _json({"train": train.row_ids, "test": test.row_ids}).encode()
            ),
        },
        "model": {"name": manifest.model.name, "parameters": params},
        "metrics": metrics,
        "environment": environment,
        "source": {
            "base_git_commit": git_commit,
            "git_revision_origin": "caller_supplied" if git_commit else "unavailable",
            "files_sha256": sources,
            "sha256": _digest(_json(sources).encode()),
        },
        "resources": {
            "execution_limit_seconds": args.max_seconds,
            "automatic_retries": 0,
            "paid_calls": 0,
            "worker_cpu_seconds": usage.ru_utime + usage.ru_stime,
            "worker_peak_rss_kib": usage.ru_maxrss,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    # Reject nonfinite output before it can reach the publisher.
    _json(results)
    return {"manifest": canonical_json(manifest), "results": results}


def _failure(exc):
    if isinstance(exc, ValidationError):
        return {
            "execution_status": "BLOCKED",
            "error_type": "ValidationError",
            "message": "Manifest validation failed",
        }
    if isinstance(exc, (ValueError, OSError)):
        # Expected validation messages are locally defined; never echo unknown exceptions.
        message = str(exc)[:240] if isinstance(exc, ValueError) else "Required file access failed"
        return {"execution_status": "BLOCKED", "error_type": type(exc).__name__, "message": message}
    return {
        "execution_status": "FAILED",
        "error_type": type(exc).__name__,
        "message": "Execution failed; no completed results published",
    }


def _worker(sender, args):
    os.setsid()  # The supervisor can also terminate any short-lived uv subprocess.
    try:
        sender.send({"ok": True, "payload": _execute(args)})
    except Exception as exc:
        sender.send({"ok": False, "error": _failure(exc)})
    finally:
        sender.close()


def _supervise(args, deadline):
    """Spawn isolates computation; timeout kills even a native-library fit."""
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(sender, args))
    try:
        process.start()
        sender.close()
        if not receiver.poll(max(0, deadline - time.monotonic())):
            raise TimeoutError("Execution deadline exceeded")
        message = receiver.recv()
        process.join(max(0, deadline - time.monotonic()))
        if process.is_alive() or time.monotonic() >= deadline:
            raise TimeoutError("Execution deadline exceeded")
        if process.exitcode != 0:
            raise RuntimeError("Worker exited unsuccessfully")
        return message
    finally:
        if process.is_alive():
            try:
                if os.getpgid(process.pid) == process.pid:
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            process.join(2)
        sender.close()
        receiver.close()
        if process.exitcode is not None:
            process.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="development or an absolute JSON path")
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-root", default="/app/runs")
    parser.add_argument(
        "--max-seconds", type=float, default=os.environ.get("REPROLAB_MAX_SECONDS", "300")
    )
    args = parser.parse_args(argv)
    if not math.isfinite(args.max_seconds) or not 0 < args.max_seconds <= 300:
        parser.error("max-seconds must be finite, positive, and at most 300")
    started = time.monotonic()
    deadline = started + args.max_seconds
    owned = None
    created = []
    completed = False
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)

    def expired(signum, frame):
        raise TimeoutError("Execution deadline exceeded")

    try:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.run_id):
            raise ValueError("run-id must be 1-64 ASCII letters/digits/underscores/hyphens")
        root = _safe_path(args.output_root, directory=True)
        run = root / args.run_id
        run.mkdir()  # Exclusive reservation; never reuse or overwrite an existing run.
        owned = run
        if time.monotonic() >= deadline:
            raise TimeoutError("Execution deadline exceeded")
        # Bound parent-side file publication as well as native work in the child.
        signal.signal(signal.SIGALRM, expired)
        signal.setitimer(signal.ITIMER_REAL, max(0.000001, deadline - time.monotonic()))
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ[name] = "1"
        message = _supervise(args, deadline)
        if not message["ok"]:
            print(_json(message["error"]), file=sys.stderr)
            return 2 if message["error"]["execution_status"] == "BLOCKED" else 1
        payload = message["payload"]
        payload["results"]["resources"]["wall_seconds"] = time.monotonic() - started
        encoded = _json(payload["results"])
        if time.monotonic() >= deadline:
            raise TimeoutError("Execution deadline exceeded")
        _safe_path(run, directory=True)
        for name, content in (("manifest.json", payload["manifest"]), ("results.json", encoded)):
            path = run / name
            with path.open("x", encoding="utf-8") as stream:
                created.append(path)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        if time.monotonic() >= deadline:
            raise TimeoutError("Execution deadline exceeded")
        signal.setitimer(signal.ITIMER_REAL, 0)
        completed = True
        try:
            print(
                _json(
                    {
                        "execution_status": "COMPLETED",
                        "run_id": args.run_id,
                        "results": str(run / "results.json"),
                    }
                )
            )
        except BrokenPipeError:
            pass
        return 0
    except TimeoutError:
        print(
            _json(
                {
                    "execution_status": "FAILED",
                    "error_type": "TimeoutError",
                    "message": "Execution limit exceeded; no completed results published",
                }
            ),
            file=sys.stderr,
        )
        return 124
    except Exception as exc:
        error = _failure(exc)
        print(_json(error), file=sys.stderr)
        return 2 if error["execution_status"] == "BLOCKED" else 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(
                signal.ITIMER_REAL,
                max(0.000001, previous_timer[0] - (time.monotonic() - started)),
                previous_timer[1],
            )
        if not completed and owned is not None:
            for path in reversed(created):
                path.unlink(missing_ok=True)
            try:
                owned.rmdir()
            except OSError:
                pass  # Never remove unrelated files created by another actor.


if __name__ == "__main__":
    raise SystemExit(main())
