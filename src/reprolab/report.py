"""Validate saved execution evidence, compare deterministically, and render Markdown.

No file I/O, fitting, source extraction, or implicit approval. Arithmetic display
agreement and paper-protocol compatibility are separate outputs.
"""

import hashlib
import html
import json
import math
import re
import tomllib
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictFloat, StrictInt, StrictStr, model_validator

from reprolab.manifest import (
    SHA256,
    Fact,
    FrozenModel,
    LockedManifest,
    Revision,
    Seed,
    Text,
    fingerprint,
)

METRICS = ("RMSE", "MAE", "R2", "MAPE", "nRMSE")
TOLERANCES = MappingProxyType(
    {name: Decimal("0.0005" if name == "R2" else "0.005") for name in METRICS}
)
_PositiveInt = Annotated[StrictInt, Field(gt=0)]
_NonnegativeFloat = Annotated[StrictFloat, Field(ge=0)]


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class _Measurement(FrozenModel):
    value: StrictFloat | None
    unit: Literal["MPa", "dimensionless", "percent"]
    status: Literal["COMPUTED", "NOT_COMPARABLE"]
    reason: Text | None
    denominator: dict[StrictStr, StrictInt | StrictFloat]
    definition: Fact[StrictStr]
    ddof_provenance: Fact[StrictInt] | None = None
    zero_policy_provenance: Fact[StrictStr] | None = None

    @model_validator(mode="after")
    def check_value(self):
        if self.status == "COMPUTED":
            if self.value is None or self.reason is not None:
                raise ValueError("Computed measurements need finite values and no undefined reason")
        elif self.value is not None or self.reason is None:
            raise ValueError("Undefined measurements require null values and reasons")
        return self


class _Split(FrozenModel):
    seed: Seed
    raw_rows: _PositiveInt
    cleaned_rows: _PositiveInt
    duplicates_removed: Annotated[StrictInt, Field(ge=0)]
    train_rows: _PositiveInt
    test_rows: _PositiveInt
    row_ids_sha256: SHA256


class _Parameters(FrozenModel):
    fit_intercept: StrictBool
    positive: StrictBool
    copy_X: StrictBool
    n_jobs: _PositiveInt


class _Model(FrozenModel):
    name: Literal["sklearn.linear_model.LinearRegression"]
    parameters: _Parameters


class _Environment(FrozenModel):
    python: Text
    uv: Text
    packages: dict[StrictStr, Text]
    system: Literal["Linux"]
    machine: Text
    threads: dict[StrictStr, Literal["1"]]
    uv_lock_sha256: SHA256


class _Source(FrozenModel):
    base_git_commit: Revision | None
    git_revision_origin: Literal["caller_supplied", "unavailable"]
    files_sha256: dict[StrictStr, SHA256]
    sha256: SHA256

    @model_validator(mode="after")
    def check_source(self):
        if (self.base_git_commit is None) != (self.git_revision_origin == "unavailable"):
            raise ValueError("Base revision and provenance disagree")
        if (
            not {"__init__.py", "cli.py", "experiment.py", "manifest.py"}
            <= self.files_sha256.keys()
        ):
            raise ValueError("Required runtime source hashes are missing")
        if any(not re.fullmatch(r"[a-z_][a-z0-9_]*\.py", name) for name in self.files_sha256):
            raise ValueError("Unsafe source provenance filename")
        if hashlib.sha256(_json(self.files_sha256).encode()).hexdigest() != self.sha256:
            raise ValueError("Source mapping checksum mismatch")
        return self


class _Resources(FrozenModel):
    execution_limit_seconds: Annotated[StrictFloat, Field(gt=0, le=300)]
    automatic_retries: Annotated[StrictInt, Field(ge=0, le=0)]
    paid_calls: Annotated[StrictInt, Field(ge=0, le=0)]
    worker_cpu_seconds: _NonnegativeFloat
    worker_peak_rss_kib: _PositiveInt
    wall_seconds: _NonnegativeFloat


class _Results(FrozenModel):
    results_schema_version: Annotated[StrictInt, Field(ge=1, le=1)]
    run_id: Annotated[StrictStr, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$", max_length=64)]
    execution_status: Literal["COMPLETED"]
    experiment_classification: Literal["INDEPENDENT_REIMPLEMENTATION"]
    reproduction_status: Literal["INCONCLUSIVE"]
    protocol_limitations: Annotated[tuple[Text, ...], Field(min_length=1)]
    manifest_sha256: SHA256
    dataset_sha256: SHA256
    split: _Split
    model: _Model
    metrics: dict[StrictStr, _Measurement]
    environment: _Environment
    source: _Source
    resources: _Resources
    created_at_utc: Text


def validate_results(
    manifest: LockedManifest, results: dict | _Results, *, lock_bytes: bytes, split_identity: str
) -> _Results:
    """Validate S09 v1 evidence against approved config, lock, and audited split IDs.

    Caller supplies independently checked lock bytes/split identity. Current code
    bytes are deliberately not substituted for historical source hashes. File-byte
    integrity is separately pinned by the CLI's expected-results SHA-256.
    """
    manifest = LockedManifest.model_validate(manifest)
    # JSON mode accepts immutable tuple fields from an artifact's JSON arrays.
    result = (
        _Results.model_validate_json(_json(results))
        if isinstance(results, dict)
        else _Results.model_validate(results)
    )
    if (
        result.manifest_sha256 != fingerprint(manifest)
        or result.dataset_sha256 != manifest.dataset.sha256.value
    ):
        raise ValueError("Result manifest/dataset identity mismatch")
    if (
        not re.fullmatch(r"[0-9a-f]{64}", split_identity)
        or result.split.row_ids_sha256 != split_identity
    ):
        raise ValueError("Recorded split identity differs from the independently audited split")
    split = result.split
    test_rows = math.ceil(manifest.preprocessing.expected_rows * manifest.split.test_fraction.value)
    if (
        split.seed,
        split.raw_rows,
        split.cleaned_rows,
        split.duplicates_removed,
        split.train_rows,
        split.test_rows,
    ) != (
        manifest.split.seed.value,
        manifest.dataset.raw_rows,
        manifest.preprocessing.expected_rows,
        manifest.dataset.raw_rows - manifest.preprocessing.expected_rows,
        manifest.preprocessing.expected_rows - test_rows,
        test_rows,
    ):
        raise ValueError("Recorded split/preprocessing counts or seed mismatch")
    parameters = {
        name: getattr(manifest.model, name).value
        for name in ("fit_intercept", "positive", "copy_X", "n_jobs")
    }
    if (
        result.model.name != manifest.model.name
        or result.model.parameters.model_dump() != parameters
    ):
        raise ValueError("Recorded model configuration mismatch")
    env = result.environment
    expected_packages = {
        p["name"]: p["version"]
        for p in tomllib.loads(lock_bytes.decode())["package"]
        if p["name"] not in {"reprolab", "colorama"}
    }
    if (
        hashlib.sha256(lock_bytes).hexdigest() != manifest.environment.uv_lock_sha256
        or env.uv_lock_sha256 != manifest.environment.uv_lock_sha256
        or (env.python, env.uv) != (manifest.environment.python, manifest.environment.uv)
        or env.packages != expected_packages
        or env.packages.get("scikit-learn") != manifest.environment.sklearn
        or env.packages.get("pydantic") != manifest.environment.pydantic
        or set(env.threads) != {"OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"}
    ):
        raise ValueError("Recorded environment differs from approved lock/versions")
    saved_time = datetime.fromisoformat(result.created_at_utc)
    if saved_time.tzinfo is None or saved_time.utcoffset() != timedelta(0):
        raise ValueError("Saved timestamp must be timezone-aware UTC")
    if result.resources.wall_seconds > result.resources.execution_limit_seconds:
        raise ValueError("Saved execution exceeded its declared limit")
    if set(result.metrics) != set(METRICS):
        raise ValueError("Exactly five reviewed measurements are required")

    protocols = {p.name: p for p in manifest.metrics}
    n = split.test_rows
    denominator_keys = {
        "RMSE": {"count"},
        "MAE": {"count"},
        "R2": {"count", "target_deviation_l2"},
        "MAPE": {"retained_count", "excluded_zero_count"},
        "nRMSE": {"count", "test_std", "ddof"},
    }
    for name, metric in result.metrics.items():
        protocol = protocols[name]
        if metric.unit != protocol.unit or metric.definition.model_dump(
            mode="json"
        ) != protocol.definition.model_dump(mode="json"):
            raise ValueError("Metric unit/definition/provenance mismatch")
        d = metric.denominator
        if set(d) != denominator_keys[name] or any(x < 0 for x in d.values()):
            raise ValueError("Invalid metric denominator fields")
        for key in ("count", "retained_count", "excluded_zero_count", "ddof"):
            if key in d and type(d[key]) is not int:
                raise ValueError("Denominator counts/ddof must be strict integers")
        if "count" in d and d["count"] != n:
            raise ValueError("Metric population differs from the test count")
        if metric.value is not None and (metric.value < 0 if name != "R2" else metric.value > 1):
            raise ValueError("Metric outside mathematical range")
        if name != "nRMSE" and metric.ddof_provenance is not None:
            raise ValueError("Unexpected ddof provenance")
        if name != "MAPE" and metric.zero_policy_provenance is not None:
            raise ValueError("Unexpected zero-policy provenance")
        undefined = False
        if name == "MAPE":
            if (
                d["retained_count"] + d["excluded_zero_count"] != n
                or metric.zero_policy_provenance != protocol.zero_target_policy
            ):
                raise ValueError("MAPE population/zero policy mismatch")
            undefined = d["retained_count"] == 0
        elif name == "nRMSE":
            if d["ddof"] != protocol.ddof.value or metric.ddof_provenance != protocol.ddof:
                raise ValueError("nRMSE normalization provenance mismatch")
            undefined = d["test_std"] == 0
        elif name == "R2":
            undefined = n < 2 or d["target_deviation_l2"] == 0
        if (metric.status == "NOT_COMPARABLE") != undefined:
            raise ValueError("Measurement undefined status contradicts its denominator")

    # Check identities supported by the saved sufficient statistics, without fitting.
    rmse, mae = (result.metrics[name].value for name in ("RMSE", "MAE"))
    if mae > rmse and not math.isclose(mae, rmse, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("MAE exceeds RMSE")
    target_norm = result.metrics["R2"].denominator["target_deviation_l2"]
    std = result.metrics["nRMSE"].denominator["test_std"]
    if (std == 0) != (target_norm == 0):
        raise ValueError("Zero/nonzero normalization statistics disagree")
    try:
        expected = {
            "nRMSE": 100 * (rmse / std) if std else None,
            "R2": 1 - (rmse * math.sqrt(n) / target_norm) ** 2 if target_norm and n >= 2 else None,
        }
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("Nonfinite saved normalization arithmetic") from exc
    if not math.isclose(std, target_norm / math.sqrt(n), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("Test normalization statistics disagree")
    for name, value in expected.items():
        observed = result.metrics[name].value
        if value is not None and (
            not math.isfinite(value)
            or not math.isclose(observed, value, rel_tol=1e-12, abs_tol=1e-12)
        ):
            raise ValueError("Metric arithmetic differs from saved normalization statistics")
    return result


def compare_run(
    manifest: LockedManifest, results: dict | _Results, *, lock_bytes: bytes, split_identity: str
) -> dict:
    """Separate arithmetic display diagnostics from verified metric/protocol match."""
    result = validate_results(
        manifest, results, lock_bytes=lock_bytes, split_identity=split_identity
    )
    findings = [
        dict(
            item="Dataset/reference",
            status="MATCH",
            explanation="Identity, checksum, schema and counts match the approved UCI reference; no publisher-signed historical hash.",
        ),
        dict(
            item="Recorded preprocessing",
            status="MATCH",
            explanation="Approved full-row first-occurrence policy, raw counts, and independently re-created split identity are consistent.",
        ),
        dict(
            item="Recorded holdout split",
            status="MATCH",
            explanation="70/30 counts, explicit seed, shuffled unstratified settings, and ordered original-ID hash agree with the independently re-created split.",
        ),
        dict(
            item="Published holdout membership",
            status="UNKNOWN",
            explanation="Published split membership/row IDs are unavailable; a development seed does not identify the historical Table 6 test set.",
        ),
        dict(
            item="Published preprocessing details",
            status="UNKNOWN",
            explanation="Paper removal count is supported; exact row/order/default policies are partly author-code-derived.",
        ),
        dict(
            item="Model family",
            status="MATCH",
            explanation="The reviewed family is LinearRegression; final settings are assessed separately.",
        ),
        dict(
            item="Recorded model configuration",
            status="MATCH",
            explanation="All four recorded constructor parameters equal the approved manifest; human-selected choices do not resolve published final settings.",
        ),
        dict(
            item="Recorded environment",
            status="MATCH",
            explanation="Saved packages and lock bytes match the approved development environment.",
        ),
        dict(
            item="Published environment equivalence",
            status="UNKNOWN",
            explanation="A verified historical lock/environment mapping is unavailable; development versions differ from historical declarations.",
        ),
        dict(
            item="Exact PDF identity",
            status="MATCH" if manifest.paper.exact_pdf_sha256.value else "UNKNOWN",
            explanation="Verified PDF artifact hash recorded."
            if manifest.paper.exact_pdf_sha256.value
            else "Exact approved PDF bytes/version remain unresolved; no hash is invented.",
        ),
    ]

    def setting(label, fact, execution_value):
        known = (
            fact.value is not None and fact.origin == "paper_reported" and fact.status == "reported"
        )
        findings.append(
            dict(
                item=label,
                status=("MATCH" if fact.value == execution_value else "MISMATCH")
                if known
                else "UNKNOWN",
                explanation=(
                    f"Published {fact.value}; execution {execution_value}."
                    if known
                    else f"Published value remains {fact.status}; execution {execution_value} does not fill it. {fact.explanation or ''}"
                ),
            )
        )

    setting("Published holdout seed", manifest.research.holdout_seed, manifest.split.seed.value)
    for name in ("fit_intercept", "positive", "copy_X", "n_jobs"):
        setting(
            "Published LR " + name,
            getattr(manifest.research, "final_" + name),
            getattr(manifest.model, name).value,
        )
    rows = []
    protocols = {p.name: p for p in manifest.metrics}
    with localcontext() as context:
        context.prec = 40
        context.rounding = ROUND_HALF_EVEN
        for name in METRICS:
            measured, protocol = result.metrics[name], protocols[name]
            compatibility = "MATCH" if protocol.definition.origin == "paper_reported" else "UNKNOWN"
            explanation = "Reviewed paper formula and test-population units are consistent."
            if name == "MAPE":
                compatibility = (
                    "MATCH" if measured.denominator["excluded_zero_count"] == 0 else "UNKNOWN"
                )
                explanation = (
                    "Author-code retained-term averaging; all test targets are nonzero, so masking leaves the reviewed mean denominator unchanged."
                    if compatibility == "MATCH"
                    else "Paper's n after zero exclusion is ambiguous; code-derived retained-term averaging cannot establish equivalence."
                )
            if name == "nRMSE":
                fact = manifest.research.nrmse_ddof
                known = (
                    fact.value is not None
                    and fact.origin == "paper_reported"
                    and fact.status == "reported"
                )
                compatibility = (
                    ("MATCH" if fact.value == protocol.ddof.value else "MISMATCH")
                    if known
                    else "UNKNOWN"
                )
                explanation = f"Paper specifies test std but published ddof is {fact.status}; execution ddof={protocol.ddof.value} is {protocol.ddof.origin}."
            if measured.value is None:
                compatibility = "UNKNOWN"
                explanation = measured.reason
            published = Decimal(str(protocol.published_claim.value))
            observed = Decimal(str(measured.value)) if measured.value is not None else None
            delta = abs(observed - published) if observed is not None else None
            relative = (
                100 * delta / abs(published)
                if delta is not None and published > 0 and name != "R2"
                else None
            )
            display = (
                ("WITHIN" if delta <= TOLERANCES[name] else "OUTSIDE")
                if delta is not None
                else "UNDEFINED"
            )
            agreement = (
                display if compatibility == "MATCH" and observed is not None else "NOT_COMPARABLE"
            )
            rows.append(
                dict(
                    name=name,
                    published=protocol.published_claim.value,
                    observed=measured.value,
                    unit=measured.unit,
                    absolute_difference=delta,
                    relative_difference_percent=relative,
                    tolerance=TOLERANCES[name],
                    display_check=display,
                    agreement=agreement,
                    compatibility=compatibility,
                    explanation=explanation,
                )
            )
            findings.append(
                dict(item="Metric " + name, status=compatibility, explanation=explanation)
            )
    # This manifest version does not establish complete published protocol equivalence.
    return dict(
        scientific_verdict="INCONCLUSIVE",
        experiment_classification=result.experiment_classification,
        execution_status=result.execution_status,
        findings=findings,
        metrics=rows,
    )


def render_markdown(
    manifest: LockedManifest,
    results: dict | _Results,
    *,
    lock_bytes: bytes,
    split_identity: str,
    results_sha256: str,
) -> str:
    """Render from saved evidence only; no new timestamp or artifact mutation."""
    if not re.fullmatch(r"[0-9a-f]{64}", results_sha256):
        raise ValueError("A verified result-file SHA-256 is required")
    result = validate_results(
        manifest, results, lock_bytes=lock_bytes, split_identity=split_identity
    )
    comparison = compare_run(manifest, result, lock_bytes=lock_bytes, split_identity=split_identity)

    def cell(value):
        if value is None:
            return "N/A"
        with localcontext() as context:
            context.rounding = ROUND_HALF_EVEN
            text = format(value, ".12g") if isinstance(value, Decimal) else str(value)
        return (
            html.escape(text, quote=False)
            .replace("|", r"\|")
            .replace("`", "&#96;")
            .replace("\n", "<br>")
            .replace("\r", "")
        )

    lines = [
        f"# Experiment report — {cell(result.run_id)}",
        "",
        f"**Paper:** {cell(manifest.paper.title)}  ",
        f"**DOI:** {cell(manifest.paper.doi)}  ",
        f"**Saved execution timestamp (UTC):** {cell(result.created_at_utc)}  ",
        f"**Execution:** {result.execution_status}  ",
        f"**Classification:** {result.experiment_classification}  ",
        "**Scientific verdict: INCONCLUSIVE**",
        "",
        "## Configuration",
        "",
        f"UCI {manifest.dataset.uci_id}; {result.split.raw_rows} raw rows, {result.split.cleaned_rows} cleaned; {result.split.duplicates_removed} full-row duplicates removed, first occurrence retained, original order/IDs preserved.",
        f"Eight unscaled features and strength target in MPa. Shuffled unstratified 70/30 allocation: {result.split.train_rows} training / {result.split.test_rows} testing. Execution seed {result.split.seed} ({cell(manifest.split.seed.origin)}); published holdout seed remains {cell(manifest.research.holdout_seed.value)} ({cell(manifest.research.holdout_seed.status)}).",
        "",
        "| LR parameter | Execution | Origin | Published value / status |",
        "|---|---:|---|---|",
    ]
    for name in ("fit_intercept", "positive", "copy_X", "n_jobs"):
        chosen, fact = getattr(manifest.model, name), getattr(manifest.research, "final_" + name)
        lines.append(
            f"| {name} | {cell(chosen.value)} | {cell(chosen.origin)} | {cell(fact.value)} / {cell(fact.status)} |"
        )
    lines += [
        "",
        "## Numerical comparison",
        "",
        "Arithmetic differences and display checks below are descriptive, including when a definition is unresolved. Only the separate eligible-agreement column can express comparable numerical agreement. Neither establishes scientific reproduction.",
        "",
        "| Metric | Published | Observed | Unit | Absolute arithmetic Δ (MPa / pp / unitless) | Relative Δ (%) | Abs tolerance | Display check | Definition compatibility | Eligible agreement |",
        "|---|---:|---:|---|---:|---:|---:|---|---|---|",
    ]
    for row in comparison["metrics"]:
        lines.append(
            "| "
            + " | ".join(
                cell(row[k])
                for k in (
                    "name",
                    "published",
                    "observed",
                    "unit",
                    "absolute_difference",
                    "relative_difference_percent",
                    "tolerance",
                    "display_check",
                    "compatibility",
                    "agreement",
                )
            )
            + " |"
        )
    lines += [
        "",
        "### Tolerance and denominator policy",
        "",
        "Human-selected S10 display-precision bounds: RMSE/MAE 0.005 MPa; R² 0.0005; MAPE/nRMSE 0.005 percentage points. Relative tolerance rtol=0. Inclusive absolute comparisons use full decimal values before formatting. These are half-last-printed-digit diagnostics, not paper-reported scientific acceptance thresholds.",
        "Relative Δ = 100 × absolute Δ / absolute published value for positive error references; zero references and R² use N/A. A percentage-point difference between percentage metrics is distinct from this relative percentage.",
        f"MAPE retained count: {result.metrics['MAPE'].denominator['retained_count']}; excluded zero count: {result.metrics['MAPE'].denominator['excluded_zero_count']}. Execution zero policy is author-code-derived. nRMSE test std: {result.metrics['nRMSE'].denominator['test_std']} MPa, ddof={result.metrics['nRMSE'].denominator['ddof']} (author-code-derived). The published ddof remains {cell(manifest.research.nrmse_ddof.value)} ({cell(manifest.research.nrmse_ddof.status)}).",
        "nRMSE's display check is arithmetic only when published normalization is unresolved; its eligible comparison then remains NOT_COMPARABLE regardless of closeness. Undefined measurements use N/A and reasons; no epsilon or fabricated measurement is substituted.",
        "",
        "## Compatibility and uncertainties",
        "",
        "| Check | Status | Explanation |",
        "|---|---|---|",
    ]
    for finding in comparison["findings"]:
        lines.append(
            "| " + " | ".join(cell(finding[k]) for k in ("item", "status", "explanation")) + " |"
        )
    lines += [
        "",
        "## Provenance",
        "",
        f"- Dataset SHA-256: `{result.dataset_sha256}`",
        f"- Canonical manifest SHA-256: `{result.manifest_sha256}`",
        f"- Result file SHA-256: `{results_sha256}`",
        f"- Environment lock SHA-256: `{result.environment.uv_lock_sha256}`",
        f"- Ordered split-ID SHA-256: `{result.split.row_ids_sha256}`",
        f"- Exact PDF SHA-256: {cell(manifest.paper.exact_pdf_sha256.value)}",
        f"- Historical base Git revision: {cell(result.source.base_git_commit)} ({cell(result.source.git_revision_origin)})",
        f"- Recorded runtime source-map SHA-256: `{result.source.sha256}`",
        "- The base Git revision provides context; it does not identify then-uncommitted execution code. Recorded file hashes cover the saved runtime snapshot, not the whole worktree or an independently attested execution. Current reporter source is allowed to differ. Expected file checksums are caller-supplied trust anchors, not signatures.",
        "",
        "| Recorded runtime file | SHA-256 |",
        "|---|---|",
    ]
    for name, digest in sorted(result.source.files_sha256.items()):
        lines.append(f"| {cell(name)} | {digest} |")
    lines += [
        "",
        f"Environment: Python {cell(result.environment.python)}, uv {cell(result.environment.uv)}, {cell(result.environment.system)}/{cell(result.environment.machine)}. Numerical threads: {cell(_json(result.environment.threads))}.",
        "",
        "| Saved package | Version |",
        "|---|---|",
    ]
    for name, version in sorted(result.environment.packages.items()):
        lines.append(f"| {cell(name)} | {cell(version)} |")
    lines += ["", "### Claim and definition evidence", ""]
    for protocol in manifest.metrics:
        for label, fact in (
            ("published claim", protocol.published_claim),
            ("execution definition", protocol.definition),
        ):
            for evidence in fact.evidence:
                lines.append(
                    f"- {cell(protocol.name)} {label} ({cell(fact.origin)}): {cell(evidence.reference)}; {cell(evidence.location)}; revision {cell(evidence.revision)}."
                )
    lines += [
        "",
        "## Limitations and conclusion",
        "",
        "Artifact checks establish consistency with the approved local configuration and independently re-created data split. Saved predictions are unavailable, so every metric cannot be independently recomputed without retraining; the pinned result-file digest prevents unnoticed artifact changes. Source-map consistency is not proof of historical execution. The full paper environment and historical split/final LR settings remain unverified.",
    ]
    lines.extend("- " + cell(reason) for reason in result.protocol_limitations)
    lines += [
        "",
        "The experiment completed. Display-precision similarity is insufficient to establish paper-protocol equivalence. The scientific verdict remains **INCONCLUSIVE**; no REPRODUCED claim is made.",
        "",
    ]
    return "\n".join(lines)
