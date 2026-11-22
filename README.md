# ReproLab

An evidence-driven research reproducibility agent, planned to reconstruct an ML paper's experimental protocol, run a human-approved experiment, and compare observed metrics with published claims. Missing evidence and incompatible protocols must remain visible in the result.

## Current state

This repository contains paper evidence, verified UCI dataset provenance, a pinned Docker development environment, and a small module for validated loading, duplicate handling, feature selection, and reproducible splitting. There is no runnable CLI or model experiment yet.

| Step | State | Evidence |
|---|---|---|
| S00 — Paper feasibility spike | Human-approved **CONDITIONAL**, 2026-11-21 | [Paper evidence and uncertainties](docs/p01_ground_truth.md) |
| S01 — Repository hygiene | Human-approved, 2026-11-21; reported checks rerun successfully | This README, `.gitignore`, local Git initialization, and [approval record](docs/progress.md) |
| S02 — Reproducible Python environment and checks | Human-approved, 2026-11-21, after review of reported checks | `pyproject.toml`, `uv.lock`, and [approval record](docs/progress.md) |
| S03 — Development Docker image | Human-approved, 2026-11-22, based on successful Docker verification | `Dockerfile` and `.dockerignore`; results in [progress](docs/progress.md) |
| S04 — One-service Compose setup | Human-approved, 2026-11-22 | `compose.yaml`; results in [progress](docs/progress.md) |
| S05 — Dataset acquisition and provenance | Human-approved, 2026-11-22, based on successful dataset verification | Ignored raw inputs; [source identity, schema, units, license, and discrepancies](docs/p01_ground_truth.md#8-s05-acquisition-and-provenance--observed-2026-11-22) |
| S06 — Data loader, duplicate handling, and split | Human-approved, 2026-11-22, based on successful verification | [Data functions](src/reprolab/experiment.py); verification commands below |

[Human-verified progress](docs/progress.md) is authoritative for approvals. Each step requires explicit review; committing and pushing require a separate instruction.

## First candidate

The candidate is the [2025 concrete-strength paper by Olvera-Mayorga et al.](https://doi.org/10.3390/app152312383), using **Yeh / UCI Concrete Compressive Strength** and scikit-learn **LinearRegression**. Its Table 6 metrics and source references are recorded in [the S00 ground-truth document](docs/p01_ground_truth.md). They are published claims; no local reproduction result exists.

Two material protocol uncertainties remain:

- The paper states a common seed of 42, while the inspected author notebook explicitly uses 123 for the holdout split. The seed that generated Table 6 remains unknown.
- The paper describes a standard Linear Regression baseline, while the notebook searches intercept and positivity settings. The final settings associated with the published row remain unknown.

The candidate's conditional approval retains these uncertainties. A similar score alone cannot establish a matched reproduction.

## Start here

1. Read [AGENTS.md](AGENTS.md) for working rules and approval boundaries.
2. Read [docs/progress.md](docs/progress.md) for the active step and human decisions.
3. Read only the active step in [docs/roadmap.md](docs/roadmap.md).
4. Review that step's files and observable checks before approving it.

The planned first implementation is a fixed, human-approved manifest → data validation → local model run → metrics → comparison report. Only the data loading/preparation functions exist so far. Paper parsing and orchestration come later.

The ground-truth document is a human reference. Future extraction code and its model/tool access must not read `docs/` or receive these answer keys during evaluation.

## S02 environment and verification

Use **Python 3.12.16** and **uv 0.13.8**. The project enforces both versions in [pyproject.toml](pyproject.toml). Direct dependencies are scikit-learn **1.6.1** and, since S06, xlrd **2.0.2**, with pytest **9.2.0** and Ruff **0.17.6** in the default development group. [uv.lock](uv.lock) records the resolved transitive dependencies and artifact hashes. Compose imports source through `PYTHONPATH=/app/src`; no packaging backend is needed yet.

S02 permitted the initial one-time host uv bootstrap before Docker existed. The following records that step's checks; now use the Docker commands below for development verification rather than installing project packages on the host:

```bash
uv --version
uv sync --locked
uv run ruff check .
uv run python -c 'import sklearn; print(sklearn.__version__)'
uv run python --version
uv run pytest --version
uv run ruff --version
```

`uv sync --locked` creates or synchronizes the selected environment and fails if the manifest and lockfile disagree. Ruff checks Python code without executing it; S02 had no source, while S06 adds the first module. Pytest is configured but no application test files exist yet; S06 uses the explicit assertions below. Use Docker for project execution as required by `AGENTS.md`.

The environment is a development baseline, not a reconstruction of the author's full environment. The paper declares Python 3.12.12; S02 pins the available 3.12.16 interpreter. NumPy/SciPy versions are resolved in the lockfile and are not constrained to the paper's declared versions. Preserve these differences in any later experiment comparison.

## S03 Docker development image

Prerequisite: a running Docker daemon. From this repository root:

```bash
docker build -t reprolab-dev .
docker run --rm reprolab-dev python --version
docker run --rm reprolab-dev uv --version
docker run --rm reprolab-dev python -c 'import sklearn; print(sklearn.__version__)'
docker run --rm reprolab-dev id -u
docker run --rm reprolab-dev ruff check .
docker run --rm reprolab-dev pytest --version
```

Expected versions are Python **3.12.16**, uv **0.13.8**, sklearn **1.6.1**, and pytest **9.2.0**; the runtime UID is **10001**. These image-only commands do not mount S06 source; use Compose below to lint it. Each `--rm` command removes its transient container on exit. The `reprolab-dev` image remains available locally for verification. No ports, host mounts, Docker socket, privileged mode, or additional service are required. This is a development environment; executing untrusted author code requires a separate approved runner design.

| Dockerfile instruction | What it does |
|---|---|
| `FROM python:3.12.16-slim-bookworm@sha256:...` | Selects the exact Python release and immutable Debian Bookworm slim image index. |
| `COPY --from=ghcr.io/astral-sh/uv:0.13.8@sha256:...` | Copies the pinned official uv executable into the image; no installer script is run. |
| `ENV` | Places the image's `/opt/venv/bin` first on PATH, selects `/opt/venv` for uv, disables interpreter downloads, and configures Python output/bytecode behavior. |
| First `RUN` | Creates user/group `reprolab` with UID/GID 10001, its home, and writable `/app`, `/opt/venv`, and checkpoint mount directory `/var/lib/reprolab`. |
| `WORKDIR /app` | Sets the working directory for later build instructions and runtime commands. |
| Project `COPY --chown=...` | Copies only `pyproject.toml`, `uv.lock`, and this README, owned by the unprivileged user. |
| `USER reprolab:reprolab` | Runs subsequent build instructions and containers without root privileges. |
| Final `RUN` | Uses `uv sync --locked --no-cache --no-build` to install existing locked dependencies, including development tools, then prints Python/uv versions. Downloads use uv's temporary cache; source distributions are not compiled. |
| `CMD ["python", "--version"]` | Prints the effective Python version when no command is supplied; there is no application entry point yet. |

The Python and uv references include registry-verified multi-platform digests in [Dockerfile](Dockerfile). These pin the selected image content; platform and system-library differences still matter for experiments. Dependencies are installed inside the image and do not reuse the host `.venv`.

[.dockerignore](.dockerignore) starts by excluding everything, then permits only the three project files required by this image. Docker still receives its build instructions as metadata. This keeps `.env`, secret files, `.venv`, `.git`, `docs/` answer keys, local datasets, run outputs, and unrelated files out of the build context. S06 exposes source and the approved XLS through selective runtime mounts; they remain excluded from the image.

## S04 Compose development commands

[compose.yaml](compose.yaml) defines exactly one service, `app`, using the existing Dockerfile and non-root user. It uses the stable project name `reprolab`. From the repository root:

```bash
docker compose config --services
docker compose build
docker compose run --rm app python --version
docker compose run --rm app uv run ruff check .
docker compose run --rm app id -u
docker compose ps -a
```

Expect only `app` in the service listing, Python **3.12.16**, Ruff success, UID **10001**, and no leftover verification containers. Ruff now checks the S06 source module as well. Compose runs commands in disposable containers; the named checkpoint volume persists after those containers exit.

| Configuration | Purpose |
|---|---|
| `build: .`, `image: reprolab-dev` | Builds and uses the pinned development image. |
| Five read-only bind mounts | Expose `pyproject.toml`, `uv.lock`, README, `src/`, and only the approved `inputs/Concrete_Data.xls`. S06 adds the last two mounts; host edits are visible without copying the whole checkout. |
| `create_host_path: false` | Fails for a missing source file instead of silently creating a host directory. |
| `UV_LOCKED=1` | Makes `uv run` reject manifest/lock drift; it must not rewrite the mounted lockfile. |
| `PYTHONPATH=/app/src` | Imports the mounted S06 package without adding a build backend or installing source on the host. |
| `checkpoint_state:/var/lib/reprolab` | Reserves Docker-managed storage for future SQLite checkpoints; no database is created in S04. The image pre-creates this path for UID/GID 10001 so a new volume can be used without root. |

Dependencies remain inside `/opt/venv`, outside the bind mounts. `.env`, host `.venv`, `.git`, `docs/` answer keys, other input files, and run artifacts are not exposed by Compose. Build-context exclusions and runtime mount selection are separate controls. No Docker socket, privileged mode, ports, or additional service is configured.

On macOS/Windows, bind-mounted SQLite files may lock or perform poorly. Keep future state at `/var/lib/reprolab/state.sqlite` in the named volume, not under a source mount or `runs/`. With the default project name, Docker calls this volume `reprolab_checkpoint_state`. It is intentionally retained; avoid `docker compose down -v` or volume pruning when preserving checkpoints.

To verify non-root persistence across two containers, run this in the same shell. It creates an exclusive, uniquely named marker and removes only that marker after confirming its contents:

```bash
export S04_PROBE_NAME=".s04-verify-$(date +%s)-$$"
docker compose run --rm -T -e S04_PROBE_NAME app python - <<'PY'
import os
from pathlib import Path
assert os.getuid() == os.getgid() == 10001
p = Path('/var/lib/reprolab') / os.environ['S04_PROBE_NAME']
with p.open('x') as f:
    f.write('s04-persistence-ok\n')
print('non-root write passed')
PY
docker compose run --rm -T -e S04_PROBE_NAME app python - <<'PY'
import os
from pathlib import Path
assert os.getuid() == os.getgid() == 10001
p = Path('/var/lib/reprolab') / os.environ['S04_PROBE_NAME']
assert p.read_text() == 's04-persistence-ok\n'
p.unlink()
print('persistence and marker cleanup passed')
PY
unset S04_PROBE_NAME
docker compose ps -a
```

## S05 dataset acquisition and verification

Provenance connects the data used locally to an identifiable source: official URL → unchanged downloaded bytes → checksum → inspected schema. A hash pins the file snapshot; it does not establish the paper's historical training split. The [S05 evidence](docs/p01_ground_truth.md#8-s05-acquisition-and-provenance--observed-2026-11-22) records the source, exact headers, units, license, and observed metadata discrepancies.

From this repository root with Docker running and `reprolab-dev` built, the following acquisition command is optional if the two verified files are already present. It uses `docker run` so initial acquisition can work before S06's required XLS bind source exists. It downloads only the official UCI archive, validates every member before writing, and refuses to overwrite a different local file. It has a 60-second network socket timeout, a 1 MB response limit, and no automatic retries. It retains only the original XLS and official README; the ZIP is scoped to container `/tmp` and cleaned even on failure. No host Python packages are installed.

```bash
mkdir -p inputs
docker run --rm -i --mount "type=bind,source=$PWD/inputs,target=/app/inputs" reprolab-dev python - <<'PY'
import hashlib
import tempfile
import urllib.request
import zipfile
from pathlib import Path

url = 'https://archive.ics.uci.edu/static/public/165/concrete%2Bcompressive%2Bstrength.zip'
expected = {
    'Concrete_Data.xls': (124928, '710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4'),
    'Concrete_Readme.txt': (3808, '5cd3cdb31d3cfd68287daa6b22ed0541d6932113e83ee0980ced63641af3441d'),
}
with tempfile.TemporaryDirectory(prefix='reprolab-s05-', dir='/tmp') as scratch:
    archive = Path(scratch) / 'uci.zip'
    with urllib.request.urlopen(url, timeout=60) as response:
        blob = response.read(1_000_001)
    assert len(blob) == 34444, f'Unexpected ZIP size: {len(blob)}'
    assert hashlib.sha256(blob).hexdigest() == 'dad85d14de8aee4e07479daa774e6b569a313715b71a3b92c95a07cf91c2c9a7'
    archive.write_bytes(blob)
    with zipfile.ZipFile(archive) as z:
        assert sorted(z.namelist()) == sorted(expected), z.namelist()
        payloads = {}
        for name, (size, digest) in expected.items():
            assert z.getinfo(name).file_size == size
            data = z.read(name)
            assert hashlib.sha256(data).hexdigest() == digest, name
            payloads[name] = data
        # Check every file before writing; preserve any different local file.
        for name, data in payloads.items():
            destination = Path('/app/inputs') / name
            if destination.exists():
                assert destination.read_bytes() == data, f'Refusing to overwrite {name}'
        for name, data in payloads.items():
            destination = Path('/app/inputs') / name
            if not destination.exists():
                with destination.open('xb') as f:
                    f.write(data)
            print(name, len(data), hashlib.sha256(data).hexdigest())
assert not Path(scratch).exists()
print('Acquisition PASS; temporary ZIP removed.')
PY
```

Run this read-only verification command, including when reusing existing files. `xlrd==2.0.2` reads the legacy binary XLS in a disposable uv environment; `--with` adds no project dependency and does not update `uv.lock`. `--no-cache` uses temporary package storage, and `--rm` removes the container. Only `inputs/` is added as a read-only mount; no `docs/` answer key is exposed. Each invocation needs public PyPI access for the pinned reader; HTTP retries are disabled and each request has a 60-second timeout.

```bash
docker compose run --rm -T --volume "$PWD/inputs:/app/inputs:ro" \
  --env UV_HTTP_TIMEOUT=60 --env UV_HTTP_RETRIES=0 \
  app uv run --locked --no-cache --no-build --with xlrd==2.0.2 python - <<'PY'
import hashlib
import math
import os
from pathlib import Path
import xlrd

root = Path('/app/inputs')
expected = {
    'Concrete_Data.xls': (124928, '710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4'),
    'Concrete_Readme.txt': (3808, '5cd3cdb31d3cfd68287daa6b22ed0541d6932113e83ee0980ced63641af3441d'),
}
assert os.getuid() == os.getgid() == 10001
assert os.statvfs(root).f_flag & os.ST_RDONLY, 'Input mount must be read-only'
assert xlrd.__version__ == '2.0.2'
for name, (size, digest) in expected.items():
    data = (root / name).read_bytes()
    assert len(data) == size and hashlib.sha256(data).hexdigest() == digest, name
    print(name, 'SHA-256 PASS', digest)
path = root / 'Concrete_Data.xls'
raw = path.read_bytes()
assert raw[:8].hex() == 'd0cf11e0a1b11ae1'
# An altered byte must not satisfy the approved file identity.
assert hashlib.sha256(raw[:-1] + bytes([raw[-1] ^ 1])).hexdigest() != expected[path.name][1]
headers = [
    'Cement (component 1)(kg in a m^3 mixture)',
    'Blast Furnace Slag (component 2)(kg in a m^3 mixture)',
    'Fly Ash (component 3)(kg in a m^3 mixture)',
    'Water  (component 4)(kg in a m^3 mixture)',
    'Superplasticizer (component 5)(kg in a m^3 mixture)',
    'Coarse Aggregate  (component 6)(kg in a m^3 mixture)',
    'Fine Aggregate (component 7)(kg in a m^3 mixture)',
    'Age (day)',
    'Concrete compressive strength(MPa, megapascals) ',
]
with xlrd.open_workbook(path, on_demand=True) as workbook:
    assert workbook.biff_version == 80
    assert [(s.name, s.nrows, s.ncols) for s in workbook.sheets()] == [
        ('Sheet1', 1031, 9), ('Sheet2', 0, 0), ('Sheet3', 0, 0),
    ]
    sheet = workbook.sheet_by_name('Sheet1')
    assert sheet.row_values(0) == headers
    rows = [tuple(sheet.row_values(r)) for r in range(1, 1031)]
    assert all(sheet.cell_type(r, c) == xlrd.XL_CELL_NUMBER
               for r in range(1, 1031) for c in range(9))
    assert all(math.isfinite(v) for row in rows for v in row)
    assert len(rows) == 1030 and len(set(rows)) == 1005
    assert all(row[7].is_integer() and 1 <= row[7] <= 365 for row in rows)
    assert sum(not row[1].is_integer() for row in rows) == 303
    assert (min(row[8] for row in rows), max(row[8] for row in rows)) == (2.331807832, 82.5992248)
    for index, header in enumerate(headers, 1):
        print(index, repr(header))
metadata = (root / 'Concrete_Readme.txt').read_text()
for description in ('kg in a m3 mixture -- Input Variable',
                    'Day (1~365) -- Input Variable', 'MPa -- Output Variable'):
    assert description in metadata
assert path.read_bytes() == raw
print('S05 PASS: 1030 rows, 8 predictors + target; 9270 finite numeric cells.')
print('Units: seven ingredients kg/m^3; age days; target strength MPa.')
print('25 repeated full rows retained; 303 fractional slag values retained; no training.')
PY
git check-ignore -v inputs/Concrete_Data.xls inputs/Concrete_Readme.txt
git ls-files -- inputs/
git diff --exit-code -- pyproject.toml uv.lock Dockerfile compose.yaml .dockerignore .gitignore
git diff --cached --name-only
git diff --check
docker compose ps -a
```

Expected: `S05 PASS`, both input paths ignored by `/inputs/`, no tracked inputs or staged files, unchanged environment/configuration, no whitespace errors, and no remaining project containers. All 1,030 rows remain in the original file; counting duplicates does not remove them. No application tests exist yet, and this command does not train a model.

Manually open the [UCI record](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) to compare the eight feature roles, target, units, and CC BY 4.0 license with the provenance table. Attribution: **Yeh, I. (1998). Concrete Compressive Strength [Dataset]. UCI Machine Learning Repository. [DOI 10.24432/C5PK67](https://doi.org/10.24432/C5PK67)**, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Raw files are unmodified; the bundled attribution notice is retained. Review the documented page/README donation-date difference and the slag integer-label discrepancy. If any hash or schema assertion fails, stop for source review; do not resave the workbook or change the reference hash to suppress the failure.

Review questions: What does the checksum establish about the source file? Why should slag retain fractional values? Why does verifying 25 duplicates leave the paper's seed and LR settings unresolved?

## S06 data preparation and verification

[experiment.py](src/reprolab/experiment.py) has one file-I/O boundary, `load_concrete(path)`. It hashes the bytes before parsing those same bytes with pinned xlrd, checks the original workbook structure/cell types, and calls the pure `validate_concrete(headers, rows)` function for the exact schema, 1,030 rows, nine columns, and finite numeric values. The checksum and schema are human-approved development fixtures; the module does not read `docs/` or extract paper settings.

`ConcreteData` holds immutable tuples of numeric rows and aligned **original Excel row numbers 2–1031**, with the header excluded. `remove_duplicates` compares all nine values, keeps the first occurrence without sorting, and returns both the cleaned data and a `duplicate_of` mapping from each removed row ID to its retained first occurrence. The default expected cleaned count is 1,005; a mismatch raises `ValueError`. The XLS is never rewritten.

`select_features_target` returns eight-feature rows and the strength targets in the supplied order, retaining the original precision and units. `split_data(cleaned, seed=123)` splits complete rows and IDs together, using an explicit integer seed, 30% test allocation, shuffling, and no stratification. It rejects data that still contains duplicate full rows. Select features/target on the returned partitions to preserve alignment. No scaler, estimator, tuning, or metrics are involved. Deduplicating first prevents identical full rows appearing across the holdout boundary; it does not guarantee independence of related mixtures or resolve historical experimental provenance.

**Seed 123 is an author-code-derived development choice, not a verified configuration for the published results.** The seed argument has no default. Repeatability also depends on identical source bytes, retained row order, and the pinned environment. The paper's seed and final LR settings remain unresolved.

Only `xlrd==2.0.2` is added; existing versions are retained in the lock. Lock resolution was performed inside Docker using copies of the manifest, lock, and README scoped to container `/tmp`, with temporary storage cleaned afterward. No host dependency installation, pandas, or new build backend is required. The Dockerfile and `.dockerignore` remain unchanged: runtime Compose mounts expose the source and approved XLS read-only.

From the repository root, build and check the locked environment. The image was rebuilt for the S06 handoff; skip the build command when reusing that image with the same dependency files. The host Python command below only puts a configurable timeout around Docker; it does not import or install project packages:

```bash
python3 - <<'PY'
import os
import subprocess
subprocess.run(['docker', 'compose', 'build'], check=True,
               timeout=int(os.environ.get('REPROLAB_S06_BUILD_TIMEOUT_SECONDS', '900')))
PY
docker compose config --services
docker compose run --rm -T app uv sync --locked --offline --no-cache --no-build
docker compose run --rm -T app uv lock --check --offline
docker compose run --rm -T app uv run --offline ruff check --no-cache .
docker compose run --rm -T app ruff format --check src
```

Run the following data and failure-case checks. They create no repository artifacts; the altered-checksum fixture is scoped to container `/tmp` and removed afterward:

```bash
docker compose run --rm -T app python - <<'PY'
import hashlib
import os
import tempfile
from pathlib import Path
from reprolab.experiment import (
    CONCRETE_COLUMNS, CONCRETE_SHA256, ConcreteData, load_concrete,
    remove_duplicates, select_features_target, split_data, validate_concrete,
)

assert os.getuid() == os.getgid() == 10001
for mount in ('/app/src', '/app/inputs/Concrete_Data.xls', '/app/pyproject.toml',
              '/app/uv.lock', '/app/README.md'):
    assert os.statvfs(mount).f_flag & os.ST_RDONLY, mount
assert not Path('/app/docs').exists() and not Path('/app/.git').exists()
assert os.access('/var/lib/reprolab', os.W_OK)
path = Path('/app/inputs/Concrete_Data.xls')
original_bytes = path.read_bytes()
raw = load_concrete(path)
assert len(raw.rows) == 1030 and all(len(row) == 9 for row in raw.rows)
assert raw.row_ids == tuple(range(2, 1032))
cleaned, duplicate_of = remove_duplicates(raw)
assert len(cleaned.rows) == 1005 and len(duplicate_of) == 25
assert set(cleaned.row_ids).isdisjoint(duplicate_of)
assert set(cleaned.row_ids) | set(duplicate_of) == set(raw.row_ids)
assert list(cleaned.row_ids) == sorted(cleaned.row_ids)
for row_id, row in zip(cleaned.row_ids, cleaned.rows, strict=True):
    assert raw.rows.index(row) + 2 == row_id  # First source occurrence retained.
for removed, retained in duplicate_of.items():
    assert retained in cleaned.row_ids and retained < removed
    assert raw.rows[removed - 2] == raw.rows[retained - 2]
X, y = select_features_target(cleaned)
assert len(X) == len(y) == 1005 and all(len(row) == 8 for row in X)
assert tuple(x + (target,) for x, target in zip(X, y, strict=True)) == cleaned.rows
train, test = split_data(cleaned, seed=123)
assert len(train.rows) == 703 and len(test.rows) == 302
assert (train, test) == split_data(cleaned, seed=123)
assert set(train.row_ids).isdisjoint(test.row_ids)
assert set(train.rows).isdisjoint(test.rows)
assert set(train.row_ids) | set(test.row_ids) == set(cleaned.row_ids)
assert set(train.row_ids) | set(test.row_ids) | set(duplicate_of) == set(raw.row_ids)
for part in (train, test):
    features, targets = select_features_target(part)
    for row_id, row, x, target in zip(part.row_ids, part.rows, features, targets, strict=True):
        assert row == raw.rows[row_id - 2] == x + (target,)

def expect_error(label, call, message, error=ValueError):
    try:
        call()
    except error as exc:
        assert message in str(exc), (label, str(exc))
        print('Rejected:', label)
    else:
        raise AssertionError('Unexpected acceptance: ' + label)

expect_error('reordered headers', lambda: validate_concrete(CONCRETE_COLUMNS[::-1], raw.rows), 'schema')
expect_error('wrong row count', lambda: validate_concrete(CONCRETE_COLUMNS, raw.rows[:-1]), '1030')
expect_error('missing target', lambda: validate_concrete(CONCRETE_COLUMNS, [r[:8] for r in raw.rows]), '9 columns')
for bad in (None, '', '1.0', True, float('nan'), float('inf')):
    malformed = ((bad,) + raw.rows[0][1:],) + raw.rows[1:]
    expect_error(repr(bad), lambda: validate_concrete(CONCRETE_COLUMNS, malformed), 'finite number')
expect_error('duplicate IDs', lambda: select_features_target(ConcreteData(raw.rows, (2,) * 1030)), 'unique')
expect_error('misaligned IDs', lambda: select_features_target(ConcreteData(raw.rows, raw.row_ids[:-1])), 'equal lengths')
expect_error('cleaned count mismatch', lambda: remove_duplicates(raw, expected_rows=1004), '1004')
expect_error('split before deduplication', lambda: split_data(raw, seed=123), 'duplicate full rows')
for bad_seed in (None, True, -1, 2**32, 1.5, '123'):
    expect_error('seed=' + repr(bad_seed), lambda: split_data(cleaned, seed=bad_seed), 'seed')
expect_error('missing seed', lambda: split_data(cleaned), 'seed', TypeError)
with tempfile.TemporaryDirectory(prefix='reprolab-s06-', dir='/tmp') as scratch:
    altered = Path(scratch) / 'altered.xls'
    altered.write_bytes(original_bytes[:-1] + bytes([original_bytes[-1] ^ 1]))
    expect_error('altered XLS checksum', lambda: load_concrete(altered), 'SHA-256 mismatch')
assert not Path(scratch).exists()
assert path.read_bytes() == original_bytes
assert hashlib.sha256(original_bytes).hexdigest() == CONCRETE_SHA256
digest = hashlib.sha256(repr((train.row_ids, test.row_ids)).encode()).hexdigest()
print('Split identifier digest:', digest)
print('S06 PASS: raw 1030 x 9; cleaned 1005; train 703; test 302; removed IDs 25.')
print('All source IDs accounted for; repeatable disjoint split; failure cases rejected.')
print('UID/GID 10001; read-only mounts; XLS unchanged; scratch removed; no training.')
PY
```

Check that a stale lock is rejected rather than rewritten. This changes only a temporary manifest copy, never the project files. The negative probe needs public PyPI metadata because uv must re-resolve the changed project; offline failure with an empty metadata cache would not prove lock-drift rejection. Registry metadata/cache is scoped to container `/tmp`, HTTP timeout is 60 seconds, retries are disabled, and the probe has a 150-second cap. No packages are installed by this probe:

```bash
docker compose run --rm -T app python - <<'PY'
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix='reprolab-s06-drift-', dir='/tmp') as scratch:
    root = Path(scratch)
    for name in ('pyproject.toml', 'uv.lock', 'README.md'):
        shutil.copyfile(Path('/app') / name, root / name)
    before = (root / 'uv.lock').read_bytes()
    manifest = root / 'pyproject.toml'
    manifest.write_text(manifest.read_text().replace('version = "0.0.0"', 'version = "0.0.1"', 1))
    env = dict(os.environ, UV_CACHE_DIR=str(root / 'cache'),
               UV_HTTP_TIMEOUT='60', UV_HTTP_RETRIES='0')
    result = subprocess.run(['uv', 'lock', '--check', '--project', scratch], env=env,
                            capture_output=True, text=True, timeout=150)
    assert result.returncode != 0 and 'needs to be updated' in result.stderr, result.stderr
    assert (root / 'uv.lock').read_bytes() == before
assert not root.exists()
print('Lock drift rejected; lock unchanged; temporary copy removed.')
PY
git diff --check
git diff --cached --name-only
git ls-files -- inputs/
git check-ignore -v inputs/Concrete_Data.xls inputs/Concrete_Readme.txt
docker compose ps -a
```

Expected: only service `app`, locked dependency checks and Ruff pass, `S06 PASS`, explicit rejection of invalid inputs and stale lock, no staged/tracked input files, and no remaining project containers. Keep `reprolab_checkpoint_state`; these checks do not create a database or delete the volume. These are S06 smoke assertions, not a persistent pytest suite or an experiment. No model is trained, and no reproduction metrics are generated.

Understanding checks: Why remove identical full rows before splitting? How do retained IDs plus `duplicate_of` account for every original row? Why does seed 123 provide a repeatable development split without proving the published split?

## Repository contents

| Path | Purpose |
|---|---|
| `AGENTS.md` | Working rules, scientific integrity requirements, and approval gates |
| `docs/roadmap.md` | Step deliverables and pass conditions |
| `docs/progress.md` | Human approval record and current review status |
| `docs/p01_ground_truth.md` | P01 evidence, source hashes, conflicts, and conditional feasibility verdict |
| `.gitignore` | Keeps local configuration, secrets, downloads, run artifacts, and caches out of ordinary Git staging |
| `README.md` | Project orientation and current capabilities |
| `pyproject.toml` | Exact Python/tool/dependency pins and pytest/Ruff configuration |
| `uv.lock` | Resolved package versions, sources, and artifact hashes for locked synchronization |
| `Dockerfile` | Pinned Python/uv image, locked in-image environment, and non-root development runtime |
| `.dockerignore` | Minimal build-context allowlist |
| `compose.yaml` | One development service, selective live file mounts, and the checkpoint state volume |
| `inputs/` (ignored, local only) | Unmodified UCI XLS and official README; not included in Git or the image |
| `src/reprolab/__init__.py` | Minimal package marker |
| `src/reprolab/experiment.py` | Verified XLS loading and pure validation, duplicate handling, selection, and split functions |

The Git remote is [kanchanpotdar/reprolabs](https://github.com/kanchanpotdar/reprolabs), configured locally as `origin`. Local preparation does not imply that these files have been published.

## Local files and source attribution

Local paper/data downloads belong in the ignored `inputs/` directory when the relevant step authorizes acquisition. Generated experiment artifacts belong in ignored `runs/` when experiments exist. Neither directory is created by S01. Python environments and caches are also ignored. `.env.example` is exempted from the `.env.*` rule so a safe configuration example can be added in its creating step.

Ignore rules prevent ordinary Git discovery/staging; they do not remove previously tracked files or inspect file contents for secrets. Review status and staged content before any commit.

The [UCI dataset](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) and paper identify CC BY 4.0 licenses. Their attribution, exact source identities, and the separate author-code licensing uncertainty are documented in the S00 evidence. No license has been assigned to this project's code.
