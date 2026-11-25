# ReproLab

An evidence-driven research reproducibility agent, planned to reconstruct an ML paper's experimental protocol, run a human-approved experiment, and compare observed metrics with published claims. Missing evidence and incompatible protocols must remain visible in the result.

## Current state

This repository contains paper evidence, verified UCI dataset provenance, a pinned Docker environment, strict manifests, a deterministic Linear Regression CLI, and honest Markdown comparison reports. Execution success, numerical display agreement, and scientific reproduction remain separate.

| Step | State | Evidence |
|---|---|---|
| S00 — Paper feasibility spike | Human-approved **CONDITIONAL**, 2026-11-21 | [Paper evidence and uncertainties](docs/p01_ground_truth.md) |
| S01 — Repository hygiene | Human-approved, 2026-11-21; reported checks rerun successfully | This README, `.gitignore`, local Git initialization, and [approval record](docs/progress.md) |
| S02 — Reproducible Python environment and checks | Human-approved, 2026-11-21, after review of reported checks | `pyproject.toml`, `uv.lock`, and [approval record](docs/progress.md) |
| S03 — Development Docker image | Human-approved, 2026-11-22, based on successful Docker verification | `Dockerfile` and `.dockerignore`; results in [progress](docs/progress.md) |
| S04 — One-service Compose setup | Human-approved, 2026-11-22 | `compose.yaml`; results in [progress](docs/progress.md) |
| S05 — Dataset acquisition and provenance | Human-approved, 2026-11-22, based on successful dataset verification | Ignored raw inputs; [source identity, schema, units, license, and discrepancies](docs/p01_ground_truth.md#8-s05-acquisition-and-provenance--observed-2026-11-22) |
| S06 — Data loader, duplicate handling, and split | Human-approved, 2026-11-22, based on successful verification | [Data functions](src/reprolab/experiment.py); verification commands below |
| S07 — Data and split regression tests | Human-approved, 2026-11-22, based on successful verification | [Pytest module](tests/test_experiment.py); S07 verification below |
| S08 — Explicit locked manifest | Human-approved, 2026-11-23, based on successful verification | [Manifest schema and reviewed fixture](src/reprolab/manifest.py); S08 verification below |
| S09 — Deterministic CLI execution | Human-approved, 2026-11-25, based on successful verification and repeatable results | [CLI](src/reprolab/cli.py); measured development runs and verification below |
| S10 — Comparison and honest Markdown report | Human-approved, 2026-11-25, following manual verification of 162 passing tests and the INCONCLUSIVE report | [Report module](src/reprolab/report.py); S10 comparison and verification below |
| S11 — Validator and report regression tests | Human-approved, 2026-11-25, based on successful verification | [Manifest/metric tests](tests/test_manifest.py); 11 new cases, 173 total passing |

[Human-verified progress](docs/progress.md) is authoritative for approvals. Each step requires explicit review; committing and pushing require a separate instruction.

## First candidate

The candidate is the [2025 concrete-strength paper by Olvera-Mayorga et al.](https://doi.org/10.3390/app152312383), using **Yeh / UCI Concrete Compressive Strength** and scikit-learn **LinearRegression**. Its Table 6 metrics and source references are recorded in [the S00 ground-truth document](docs/p01_ground_truth.md). These remain published claims; S09 measurements below are separate development results with an inconclusive reproduction status.

Two material protocol uncertainties remain:

- The paper states a common seed of 42, while the inspected author notebook explicitly uses 123 for the holdout split. The seed that generated Table 6 remains unknown.
- The paper describes a standard Linear Regression baseline, while the notebook searches intercept and positivity settings. The final settings associated with the published row remain unknown.

The candidate's conditional approval retains these uncertainties. A similar score alone cannot establish a matched reproduction.

## Start here

1. Read [AGENTS.md](AGENTS.md) for working rules and approval boundaries.
2. Read [docs/progress.md](docs/progress.md) for the active step and human decisions.
3. Read only the active step in [docs/roadmap.md](docs/roadmap.md).
4. Review that step's files and observable checks before approving it.

The implemented flow is an explicit reviewed manifest → data validation/preparation → bounded local model run → metrics → immutable JSON evidence → deterministic comparison report. Paper parsing and orchestration remain future work. Historical sections below retain each step's observed verification counts; the current full suite has 173 tests.

The ground-truth document is a human reference. Future extraction code and its model/tool access must not read `docs/` or receive these answer keys during evaluation.

## S02 environment and verification

Use **Python 3.12.16** and **uv 0.13.8**. The project enforces both versions in [pyproject.toml](pyproject.toml). Direct dependencies are scikit-learn **1.6.1**, xlrd **2.0.2**, and Pydantic **2.14.4**, with pytest **9.2.0** and Ruff **0.17.6** in the default development group. [uv.lock](uv.lock) records resolved transitive dependencies and artifact hashes. Compose imports source through `PYTHONPATH=/app/src`; no packaging backend is needed yet.

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

`uv sync --locked` creates or synchronizes the selected environment and fails if the manifest and lockfile disagree. Ruff checks Python code without executing it; S02 had no source, while S06 adds the first module. S07 adds pytest regression tests alongside the earlier S06 smoke assertions. Use Docker for project execution as required by `AGENTS.md`.

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

[.dockerignore](.dockerignore) starts by excluding everything, then permits only the three project files required by this image. Docker still receives its build instructions as metadata. This keeps `.env`, secret files, `.venv`, `.git`, `docs/` answer keys, local datasets, run outputs, and unrelated files out of the build context. Compose exposes source, tests, and the approved XLS through selective runtime mounts; they remain excluded from the image.

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
| Six read-only bind mounts | Expose `pyproject.toml`, `uv.lock`, README, `src/`, `tests/`, and only the approved `inputs/Concrete_Data.xls`. Host edits are visible without copying the whole checkout. |
| `create_host_path: false` | Fails for a missing source file instead of silently creating a host directory. |
| `UV_LOCKED=1` | Makes `uv run` reject manifest/lock drift; it must not rewrite the mounted lockfile. |
| `PYTHONPATH=/app/src` | Imports the mounted S06 package without adding a build backend or installing source on the host. |
| `PYTEST_ADDOPTS=-p no:cacheprovider` | Disables pytest's persistent cache; test scratch files use scoped container `/tmp`. |
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

## S07 regression tests and verification

[tests/test_experiment.py](tests/test_experiment.py) has **47 collected cases**. Most fixtures use 2–10 deterministic synthetic rows with literal expected outputs. The raw schema/cell checks generate a 1,030-row tuple in memory because that public validator requires exactly 1,030 rows; no dataset file is generated. Expected headers are independently specified, and reviewed literal split IDs come from the pinned RNG reference rather than being calculated by the function under test.

| Category | What a failure would reveal |
|---|---|
| Raw validation | Changed exact headers, row/column counts, or acceptance of missing, text, boolean, or nonfinite cells |
| File boundary | Missing input or parsing bytes before checking the approved checksum; the temporary parser sentinel is restored by pytest |
| Duplicate handling | Sorting retained rows, keeping later occurrences, dropping IDs, wrong duplicate mappings/counts, or merging identical features with different targets |
| Feature/target selection | Wrong columns, rounding/scaling, reordered values, or loss of original IDs |
| Splitting | Wrong reviewed seed memberships, nonrepeatable output, overlapping/missing rows, misaligned features/targets/IDs, input mutation, or acceptance of invalid/omitted seeds and undeduplicated data |
| Optional XLS integration | Drift from the approved SHA-256, 1,030 × 9 raw shape, 1,005 retained rows, or 703/302 partition counts; unexpected changes to original bytes |

All tests use the already pinned pytest; no dependencies, production code, interpreter/image pins, or lockfile are changed by S07. Compose adds only a read-only tests mount and disables [pytest's cache provider](https://docs.pytest.org/en/stable/how-to/cache.html). The image already disables Python bytecode writes. Temporary test files use `TemporaryDirectory` under container `/tmp`, scoped for cleanup on success and failure.

From the repository root with the existing S06 image available, run:

```bash
docker compose run --rm app uv run pytest --collect-only -q
docker compose run --rm app uv run pytest -q
docker compose run --rm -T app uv run --offline ruff check --no-cache .
docker compose run --rm -T app ruff format --check src tests
docker compose run --rm -T app uv lock --check --offline
```

Expected with the local approved XLS: **47 collected, 47 passed, 0 failed, 0 skipped**; Ruff lint/format and lock checks pass. The integration test skips only when the XLS path is absent; a present but wrong/corrupt file must fail. The Compose service requires its approved XLS bind source to exist before startup, so use this dataset-free route when no local dataset is available:

```bash
docker run --rm \
  --mount "type=bind,source=$PWD/src,target=/app/src,readonly" \
  --mount "type=bind,source=$PWD/tests,target=/app/tests,readonly" \
  --env PYTHONPATH=/app/src \
  --env 'PYTEST_ADDOPTS=-p no:cacheprovider' \
  reprolab-dev pytest -q
```

This mounts no inputs and should report **47 collected, 46 passed, 0 failed, 1 skipped**, with the explicit integration skip reason. It uses the same non-root image and pinned environment, with no extra service, dataset download, or Excel-writing dependency.

To demonstrate that a test detects a real fixture change, run the following. It changes only a temporary copy's feature-selection fixture target from `99.125` to `99.25`, keeps the independently specified expectation unchanged, and requires an assertion failure. It then restores the copy and requires the selected test to pass. The original mounted test file and XLS are not edited:

```bash
docker compose run --rm -T app python - <<'PY'
import subprocess
import tempfile
from pathlib import Path

source = Path('/app/tests/test_experiment.py')
original = source.read_text()
needle = '7.5, 8.0, 99.125'
assert original.count(needle) == 1
with tempfile.TemporaryDirectory(prefix='reprolab-s07-probe-', dir='/tmp') as scratch:
    copy = Path(scratch) / 'test_experiment.py'
    copy.write_text(original.replace(needle, '7.5, 8.0, 99.25', 1))
    selected = str(copy) + '::test_feature_target_values_are_preserved'
    command = ['python', '-m', 'pytest', '-q', '-c', '/app/pyproject.toml', selected]
    changed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    print(changed.stdout)
    assert changed.returncode == 1, changed.stderr
    assert 'AssertionError' in changed.stdout and '1 failed' in changed.stdout
    copy.write_text(original)
    restored = subprocess.run(command, capture_output=True, text=True, timeout=60)
    print(restored.stdout)
    assert restored.returncode == 0 and '1 passed' in restored.stdout, restored.stderr
assert not Path(scratch).exists()
assert source.read_text() == original
print('Expected fixture failure and restored pass verified; temporary copy removed.')
PY
docker compose run --rm app uv run pytest -q
git diff --check
git diff --cached --name-only
git ls-files -- inputs/
docker compose ps -a
```

Expected deliberate probe: **1 collected, 0 passed, 1 failed, 0 skipped**. Restored probe: **1 collected, 1 passed, 0 failed, 0 skipped**. The final full run returns to **47 passed**, showing repeatable results in a fresh process/container. No staged files, tracked datasets, whitespace issues, or leftover project containers should appear. Do not remove the checkpoint volume.

These are data-contract regressions, not evidence of model accuracy or paper reproduction. Seed 123 remains a disclosed development choice. Review questions: Why retain rows with identical predictors but different strength targets? Why should a changed fixture fail against an unchanged expected value?

## S08 manifest, evidence, and verification

[manifest.py](src/reprolab/manifest.py) separates generic source observations from an explicit **development baseline**. All models use strict field types, forbidden extras, frozen nested models, immutable tuple collections, and finite numbers. A shared `Fact` record carries a value, origin, evidence status, nonempty evidence pointers, and an explanation where needed. Unknown/conflicting facts require null value/origin and reasons; conflicts need distinct pointers. Inferences may carry a candidate value but no claimed reporting origin, and cannot serve as resolved execution settings.

The intended flow is source observations → separate human review/explicit execution choices → `LockedManifest` → canonical JSON and fingerprint → a later approved experiment. S08 supplies the schema and fixed development fixture only. File I/O stays with the caller (for example, hashing the actual lockfile); the manifest module neither reads documents nor runs the data/model pipeline. It assumes reviewed source pointers and the current approved dataset profile. For example, omitting `split.seed` raises `ValidationError` before a fingerprint or later execution can be accepted.

The locked profile checks the approved dataset hash, exact column order/roles/units, full-row first-occurrence deduplication, preserved order, no scaling/transformation, and shuffled unstratified 70/30 splitting. Unsupported models/parameters are rejected; the typed LR configuration is **human-selected** `fit_intercept=True`, `positive=False`, `copy_X=True`, `n_jobs=1`. Seed **123** remains code-derived and approved only as a development choice. Published final intercept/positivity remain null/conflicting; published `copy_X`/estimator `n_jobs`, the holdout seed, and nRMSE ddof remain null/not reported. Global/CV seed 42 is not relabeled as the holdout seed.

Metrics store **definitions and published claims**, never computed results. nRMSE explicitly adopts author-code test-standard-deviation `ddof=0`; MAPE explicitly adopts zero-target exclusion/retained-term averaging from author code. Canonical JSON sorts object keys, preserves tuple order and literal strings, uses UTF-8 and finite numbers, and contains no fingerprint field. `fingerprint()` hashes those bytes. The fingerprint identifies content; it is not a signature, approval, or permission to train.

**Exact PDF hash is null.** S00 recorded a hash for an inspected CDN PDF, but its relationship to the canonical version remains unresolved and its exact bytes are not verified for this manifest. That historical record stays in the human reference; the fixture does not promote it into a new verified PDF identity. Dataset and environment lock hashes identify their respective bytes separately.

`SourceObservations.model_json_schema()` is the current source-only protocol subset, with reusable `SourceFact`/`SourceEvidence` types for later extraction fields. It contains no P01 values, scientific defaults, claims, or human execution choices. It rejects human/runtime evidence kinds. A future extractor receives only the generic source schema and approved paper content; it must not receive the fixture, locked profile schema, `docs/`, or evaluation answers. A separate trusted review stage must resolve execution choices. Neither schema nor citations authenticate their own truth; artifact verification and human review remain necessary. S08 implements no extraction agent or automatic conversion/approval.

One direct dependency is added: [Pydantic 2.14.4](https://pypi.org/project/pydantic/2.14.4/). Its four required transitives are locked; every previous package/version/artifact is retained. Lock resolution/installations run only inside Docker. Existing source mounts support the new module; no Compose/Dockerfile change is needed. S08 used the smoke assertions below; S11 adds permanent missing-field regressions without duplicating the existing metric/CLI/report tests.

Rebuild once for the new dependency lock, then run the existing suite and quality checks. The build timeout is configurable; the host Python only orchestrates Docker:

```bash
python3 - <<'PY'
import os
import subprocess
subprocess.run(['docker', 'compose', 'build'], check=True,
               timeout=int(os.environ.get('REPROLAB_S08_BUILD_TIMEOUT_SECONDS', '900')))
PY
docker compose run --rm app uv run pytest -q
docker compose run --rm -T app uv run --offline ruff check --no-cache .
docker compose run --rm -T app ruff format --check src tests
docker compose run --rm -T app uv sync --locked --offline --no-cache --no-build
docker compose run --rm -T app uv lock --check --offline
docker compose run --rm -T app python - <<'PY'
import os
import tempfile
from pathlib import Path
assert os.getuid() == os.getgid() == 10001
assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
for file in ('src/reprolab/manifest.py', 'tests/test_experiment.py', 'uv.lock', 'inputs/Concrete_Data.xls'):
    assert not os.access(Path('/app') / file, os.W_OK)
assert not Path('/app/docs').exists() and not Path('/app/.git').exists()
assert os.access('/var/lib/reprolab', os.W_OK)
try:
    with tempfile.TemporaryDirectory(prefix='reprolab-s08-', dir='/tmp') as scratch:
        Path(scratch, 'cleanup-check').write_text('temporary verification only')
        raise RuntimeError('Deliberate cleanup-path check')
except RuntimeError:
    pass
assert not Path(scratch).exists()
assert not list(Path('/tmp').glob('reprolab-s08-*'))
assert not list(Path('/app/src').rglob('__pycache__'))
assert not list(Path('/app/tests').rglob('__pycache__'))
assert not Path('/app/.pytest_cache').exists()
print('Non-root, read-only mounts, writable checkpoint directory, and failure-path cleanup: PASS')
PY
```

Run this manifest contract check. All invalid/sensitivity variants are temporary in-memory validation inputs, not changes to the reviewed fixture or claims:

```bash
docker compose run --rm -T app python - <<'PY'
import copy
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
from pydantic import ValidationError
from reprolab.experiment import load_concrete, remove_duplicates, select_features_target, split_data
from reprolab.manifest import (
    LockedManifest, SourceObservations, canonical_json, development_manifest, fingerprint,
)

lock = hashlib.sha256(Path('/app/uv.lock').read_bytes()).hexdigest()
m = development_manifest(lock)
encoded = canonical_json(m)
payload = json.loads(encoded)
assert fingerprint(m) == fingerprint(LockedManifest.model_validate_json(encoded))
assert canonical_json(LockedManifest.model_validate_json(encoded)) == encoded
assert 'fingerprint' not in payload
assert m.environment.uv_lock_sha256 == lock
assert m.environment.python == platform.python_version()
assert m.environment.pydantic == importlib.metadata.version('pydantic') == '2.14.4'
assert m.environment.sklearn == importlib.metadata.version('scikit-learn') == '1.6.1'
assert m.paper.exact_pdf_sha256.value is None
assert m.research.holdout_seed.value is None and m.research.holdout_seed.status == 'not_reported'
assert m.research.common_or_cv_seed.value == 42
assert m.research.nrmse_ddof.value is None
assert m.research.final_fit_intercept.value is None and m.research.final_fit_intercept.status == 'conflicting'
assert m.research.final_positive.value is None and m.research.final_positive.status == 'conflicting'
assert m.research.final_copy_X.value is None and m.research.final_n_jobs.value is None
assert m.split.seed.value == 123 and m.split.seed.origin == 'author_code_derived'
for name, expected in (('fit_intercept', True), ('positive', False), ('copy_X', True), ('n_jobs', 1)):
    fact = getattr(m.model, name)
    assert fact.value == expected and fact.origin == 'human_selected'

def edit(data, path, value=None, drop=False):
    keys = [int(k) if k.isdigit() else k for k in path.split('.')]
    parent = data
    for key in keys[:-1]:
        parent = parent[key]
    if drop:
        del parent[keys[-1]]
    else:
        parent[keys[-1]] = value

rejections = 0
def reject(path, value=None, drop=False):
    global rejections
    data = copy.deepcopy(payload)
    edit(data, path, value, drop)
    try:
        LockedManifest.model_validate_json(json.dumps(data))
    except ValidationError:
        rejections += 1
    else:
        raise AssertionError('Unexpected acceptance: ' + path)

for path in ('split', 'split.seed', 'split.seed.value', 'split.seed.evidence', 'model',
             'model.fit_intercept', 'model.copy_X', 'model.n_jobs', 'dataset.sha256',
             'paper.evidence', 'paper.exact_pdf_sha256', 'environment', 'environment.uv_lock_sha256', 'metrics'):
    reject(path, drop=True)
for path, values in (
    ('schema_version', (2, True)), ('approved', (True,)),
    ('model.name', ('RandomForestRegressor',)), ('model.alpha', (1.0,)),
    ('split.seed.value', ('123', True, -1, 2**32, None)),
    ('split.test_fraction.value', (0.5, 30.0, '0.3', float('nan'), float('inf'))),
    ('split.shuffle.value', (False, 1)), ('split.stratify.value', ('age',)),
    ('model.positive.value', ('False', 0)), ('model.n_jobs.value', (0, -1, True, '1')),
    ('preprocessing.deduplicate.value', (False,)),
    ('preprocessing.duplicate_key.value', ('features_only',)),
    ('preprocessing.keep.value', ('last',)), ('preprocessing.order.value', ('sort',)),
    ('preprocessing.scaling.value', ('standard',)), ('preprocessing.target_transform.value', ('log',)),
    ('preprocessing.expected_rows', (1004,)), ('dataset.raw_rows', (1031,)),
    ('dataset.uci_id', (166, True)), ('dataset.format', ('csv',)),
    ('dataset.sha256.value', ('bad', 'X'*64, '0'*64, m.dataset.sha256.value+'\n')),
    ('environment.uv_lock_sha256', ('', 'g'*64, lock+'\n')),
    ('dataset.columns.0.role', ('target',)), ('dataset.columns.0.unit', ('MPa',)),
    ('dataset.columns.1.name', (m.dataset.columns[0].name,)),
    ('metrics.0.name', ('accuracy',)), ('metrics.0.unit', ('percent',)),
    ('metrics.0.population', ('train',)), ('metrics.0.definition.value', ('unknown formula',)),
    ('metrics.0.published_claim.value', (-1.0, '9.68', float('nan'), float('inf'))),
    ('metrics.4.ddof', (None,)), ('metrics.4.ddof.value', (1, True)),
    ('metrics.2.zero_target_policy', (None,)),
    ('split.seed.origin', ('paper_reported',)), ('split.seed.status', ('reported', 'not_reported')),
    ('split.seed.evidence', ([],)), ('split.seed.evidence.0.revision', (None,)),
    ('split.seed.evidence.0.revision', ('a'*40+'\n',)),
    ('model.fit_intercept.explanation', (None,)),
    ('research.holdout_seed.value', (42,)), ('research.holdout_seed.origin', ('paper_reported',)),
    ('paper.exact_pdf_sha256.value', ('0'*64,)),
    ('paper.evidence.0.reference', ('http://example.org/paper', 'https://:', 'https://x:bad')),
):
    for value in values:
        reject(path, value)
for value in (-1, 2**32, True, '42'):
    reject('research.common_or_cv_seed.value', value)
reject('dataset.columns', payload['dataset']['columns'][:-1])
reject('metrics', payload['metrics'][:-1])
reject('metrics', payload['metrics'] + [payload['metrics'][0]])
first = payload['research']['final_positive']['evidence'][0]
reject('research.final_positive.evidence', [first, first])
inferred = copy.deepcopy(payload['split']['seed'])
inferred.update(origin=None, status='inferred', explanation='Unverified hypothesis; not execution-ready')
reject('split.seed', inferred)
human_claim = copy.deepcopy(payload['model']['fit_intercept'])
human_claim['value'] = 9.68
reject('metrics.0.published_claim', human_claim)

# Frozen objects and tuples; even bypass-created invalid copies are revalidated before hashing.
for obj, field, value in ((m.split.seed, 'value', 7), (m.model.positive, 'value', True),
                          (m.paper.evidence[0], 'location', 'changed')):
    try:
        setattr(obj, field, value)
    except ValidationError as exc:
        assert exc.errors()[0]['type'] == 'frozen_instance'
    else:
        raise AssertionError('Mutable configuration')
assert isinstance(m.metrics, tuple) and isinstance(m.dataset.columns, tuple)
try:
    canonical_json(m.model_copy(update={'schema_version': 99}))
except ValidationError:
    pass
else:
    raise AssertionError('Unvalidated copied instance was hashed')

# Hypothetical configuration variants are validation inputs, never authorization to run.
for path, value in (('split.seed.value', 7), ('model.positive.value', True),
                    ('split.seed.evidence.0.location', 'Verification-only citation annotation')):
    data = copy.deepcopy(payload)
    edit(data, path, value)
    if path.endswith('.value'):
        fact = data['split']['seed'] if path.startswith('split') else data['model']['positive']
        fact.update(origin='human_selected', status='reported',
                    evidence=[{'kind': 'human', 'reference': 'human:S08-verification-only',
                               'location': 'Requested sensitivity check, not a run approval', 'revision': None}],
                    explanation='Synthetic validation variant only; no experiment execution authorized')
    assert fingerprint(LockedManifest.model_validate_json(json.dumps(data))) != fingerprint(m)

# Only generic source facts may reach a future extractor, without fixture values/defaults.
schema = SourceObservations.model_json_schema()
schema_text = json.dumps(schema)
for secret in ('human_selected', 'runtime_observed', m.paper.title, m.dataset.sha256.value, '9.68'):
    assert secret not in schema_text
def no_defaults(node):
    if isinstance(node, dict):
        assert 'default' not in node
        for value in node.values():
            no_defaults(value)
    elif isinstance(node, list):
        for value in node:
            no_defaults(value)
no_defaults(schema)
observed = json.loads(m.research.model_dump_json())
SourceObservations.model_validate_json(json.dumps(observed))
injection = copy.deepcopy(observed)
injection['holdout_seed'] = copy.deepcopy(payload['model']['n_jobs'])
try:
    SourceObservations.model_validate_json(json.dumps(injection))
except ValidationError:
    pass
else:
    raise AssertionError('Extractor minted human-selected provenance')

path = Path('/app/inputs/Concrete_Data.xls')
before = path.read_bytes()
raw = load_concrete(path)
cleaned, duplicates = remove_duplicates(raw, expected_rows=m.preprocessing.expected_rows)
train, test = split_data(cleaned, seed=m.split.seed.value)
assert (len(raw.rows), len(cleaned.rows), len(train.rows), len(test.rows)) == (1030, 1005, 703, 302)
assert set(train.row_ids).isdisjoint(test.row_ids)
assert set(train.row_ids) | set(test.row_ids) | set(duplicates) == set(raw.row_ids)
for partition in (train, test):
    X, y = select_features_target(partition)
    assert tuple(x+(target,) for x, target in zip(X, y, strict=True)) == partition.rows
assert path.read_bytes() == before and fingerprint(m) == fingerprint(development_manifest(lock))
print('S08 PASS; rejected invalid manifest variants:', rejections)
print('Canonical JSON bytes:', len(encoded.encode('utf-8')), 'fingerprint:', fingerprint(m))
print('Research unknowns preserved; immutable choices; source schema data-free; pipeline compatible; XLS unchanged.')
PY
git diff --check
git diff --cached --name-only
docker compose ps -a
```

To inspect a readable view without creating an artifact:

```bash
docker compose run --rm -T app python - <<'PY'
import hashlib
import json
from pathlib import Path
from reprolab.manifest import development_manifest, fingerprint
m = development_manifest(hashlib.sha256(Path('/app/uv.lock').read_bytes()).hexdigest())
print(json.dumps({
    'purpose': m.purpose,
    'exact_pdf_sha256': m.paper.exact_pdf_sha256.value,
    'published_holdout_seed': m.research.holdout_seed.value,
    'published_fit_intercept': m.research.final_fit_intercept.value,
    'published_positive': m.research.final_positive.value,
    'published_copy_X': m.research.final_copy_X.value,
    'published_n_jobs': m.research.final_n_jobs.value,
    'development_seed': m.split.seed.model_dump(mode='json'),
    'human_selected_model': {name: getattr(m.model, name).value for name in
                            ('fit_intercept', 'positive', 'copy_X', 'n_jobs')},
    'published_claims': {metric.name: metric.published_claim.value for metric in m.metrics},
    'fingerprint': fingerprint(m),
}, indent=2))
# Full validated payload, if desired: print(m.model_dump_json(indent=2))
PY
```

Expected: S08 assertions pass, its 47 existing data tests remain included in the current 162-case suite, Ruff/format/lock checks pass, and no stopped verification containers or new project scratch artifacts remain. The printed view is an excerpt; the fingerprint is displayed beside the payload, never included in its hash. These S08 assertions perform no model fit. Review questions: Why can the executable seed be known while the published seed is null? Why must an extraction schema omit reviewed fixture defaults? Why does a fingerprint not count as human approval?

## S09 deterministic CLI and measured development runs

[cli.py](src/reprolab/cli.py) uses argparse and the existing immutable Pydantic profile. Required arguments select a reviewed manifest (the explicit name `development` or an absolute saved-JSON path), its expected canonical SHA-256, the absolute XLS path, and an unused run ID. The caller must review any new fingerprint; passing a fingerprint is a drift check, not automatic approval. The approved development fingerprint remains:

```text
7ebf5b0ec902bc5c9c112f96e0956568c47cfc22d719732dd85659079b8e4716
```

The CLI verifies manifest structure/provenance, fingerprint, actual lockfile bytes, Python/uv versions, every installed distribution against the locked Linux package set, and an offline `uv lock --check`. JSON manifests reject duplicate keys and are limited to 1 MiB. Existing data functions remain unchanged: checksum-before-parse, exact schema, full-row first-occurrence deduplication, original IDs, no scaling/rounding, and a shuffled unstratified 70/30 split with explicit seed **123**. Eight features and the strength target remain aligned. LinearRegression receives all four settings explicitly: `fit_intercept=True`, `positive=False`, `copy_X=True`, `n_jobs=1`; their human-selected provenance stays in the saved manifest. No tuning, seed search, author-notebook execution, network acquisition, or paid call occurs.

The parent reserves a new run directory exclusively, supervises a spawned worker, and publishes files only after successful computation and finite JSON validation. A parent deadline also covers publication; a timed-out worker/process group is killed and reaped. `--max-seconds` (or `REPROLAB_MAX_SECONDS`) defaults to **300**, accepts a lower positive finite limit, and rejects values above 300. Timeout exits **124**; invalid inputs/configuration/access exit **2**; unexpected execution errors exit **1**; completion exits **0**. There are **zero automatic retries**. Caught failures remove only this invocation's incomplete files/reservation. Existing run IDs and files are never overwritten. Paths must be absolute, contain no `..`, and have no symlink components; inputs must be regular files. Run IDs use 1–64 ASCII letters/digits/underscores/hyphens and begin with a letter/digit.

`compose.yaml` adds only one writable bind, `./runs` → `/app/runs`, with missing-path protection. Create that directory before Compose use. Source, tests, manifests/lock/README, and the approved XLS remain read-only; docs/Git remain unmounted; the existing SQLite checkpoint volume is preserved. OMP/OpenBLAS/MKL concurrency is set to one in Compose and enforced for the worker. No dependency, lockfile, Dockerfile, image pin, or packaging change is required. This was verified on Linux/arm64 with the existing non-root image.

Metric functions consume actual targets/predictions, without any paper-claim argument or fallback:

| Metric | Definition and explicit denominator behavior |
|---|---|
| RMSE (MPa) | `sqrt(mean(error²))`; stable L2 norm / square root of test count |
| MAE (MPa) | Mean absolute test error |
| R² | `1 − SSE/SST`; computed using equivalent L2-norm ratios; null/`NOT_COMPARABLE` for fewer than two or constant targets; negative values are retained |
| MAPE (%) | `100*mean(abs(error/y))` over nonzero test targets; record retained and excluded counts; no epsilon or near-zero exclusion; null if all targets are zero |
| nRMSE (%) | `100*RMSE/std(y_test, ddof=0)`; record the actual test standard deviation/count/ddof; null if the denominator is zero |

S00 supports these definitions; MAPE's retained-term denominator and nRMSE's `ddof=0` are explicitly **author-code-derived**, not newly claimed paper settings. Unknown/unsupported execution formulas are rejected. Nonfinite inputs, predictions, or metric arithmetic fail explicitly rather than producing NaN/Infinity. Undefined metrics carry null values and reasons while other supported measurements remain available.

Successful outputs are the ignored local files `runs/<run_id>/manifest.json` and `results.json`. The manifest is exact canonical JSON, whose file SHA equals the manifest fingerprint. Results contain actual measurements, denominator details and definition provenance, execution status, split counts/row-ID hash, dataset/manifest/lock hashes, explicit model parameters, package versions, platform/thread settings, actual source-file hashes, optional caller-supplied **base** Git revision, UTC timestamp, wall/CPU time and Linux worker peak RSS in KiB. The base revision alone does not identify uncommitted S09 code; the recorded source hashes do. Published claims remain in the manifest and never populate measured results. No data rows, model pickle, prediction dump, or report is created.

For the retained `s09-a`/`s09-b` runs, `source.base_git_commit` is the S08 revision `a885656a3559bea614fe54051ebdfda3d6accbb4`; it is labelled caller-supplied and does not identify the then-uncommitted S09 implementation. At S09 closeout, the four recorded runtime file hashes were verified against committed snapshot `9c66566554183d1f310b4a96cd9f7ecd6d675bca`, with aggregate SHA-256 `a0606bbb74e873883535dbd7d4ab4f378d7526062e753c5c4cc6648bed4713ca`. Current reporting code can differ from that historical snapshot. This is not a whole-worktree snapshot or signed execution attestation; data and environment identities are separate. Historical results retain their original provenance unchanged.

Two agent-executed runs on **2026-11-23**, `s09-a` and `s09-b`, used the same input/configuration. The second loaded the first's saved manifest. Both loaded 1,030 rows, removed 25 duplicates, and used **703 training / 302 testing** observations. Every metric had **zero absolute difference**, passing `rtol=1e-12`, `atol=1e-12`:

| Actual metric | Both development runs |
|---|---:|
| RMSE (MPa) | 9.678767807275001 |
| MAE (MPa) | 7.589085799684043 |
| R² | 0.6182298804778745 |
| MAPE (%) | 30.686085389150236 |
| nRMSE (%) | 61.78754886885589 |

The results are `COMPLETED` executions, classified `INDEPENDENT_REIMPLEMENTATION`, with reproduction status **`INCONCLUSIVE`**. The published holdout seed, final LR settings, and exact approved PDF identity remain unresolved. Numerical repeatability is not a reproduction verdict or a tolerance against the paper's rounded claims. Package locks/thread limits do not promise bitwise equality across different hardware or numerical libraries. This is a local trusted-code development runner, not a hostile-code sandbox or a crash-recoverable artifact store; abrupt machine/container loss during publication can require inspection of incomplete files. Caught failures and the enforced deadline clean their owned incomplete outputs.

### Verify S09 now

Start Docker Desktop first. The commands below are implemented and were verified; use the repository root. Bash blocks omit comment lines so they paste into default interactive zsh. Use unused run IDs each time; preserve previous runs for review.

```bash
docker info --format '{{.ServerVersion}}'
mkdir -p runs
docker compose run --rm app uv run pytest -q
docker compose run --rm -T app uv run --offline ruff check --no-cache .
docker compose run --rm -T app ruff format --check src tests
docker compose run --rm -T app uv sync --locked --offline --no-cache --no-build
docker compose run --rm -T app uv lock --check --offline
docker compose run --rm -T app uv run --offline python -m reprolab.cli --help
```

At S09 completion: **95 passed, 0 failed/skipped**, with five Python files formatted. The current S10 suite has **162 tests and six Python files**. All 47 original tests remain; the 48 S09 additions cover known synthetic linear predictions/settings, independent hand-calculated metrics, zero/near-zero/constant/invalid numeric cases, manifest/version drift, claims independence, unsafe paths, existing IDs, missing/corrupt inputs, actual worker timeout, parent publication timeout, and partial-write/unexpected-error cleanup. Synthetic CLI I/O fixtures live in scoped `/tmp` and are removed. The full raw-XLS test still skips cleanly when unavailable; default Compose itself requires its approved XLS bind source.

Run twice with a **300-second cap, zero paid calls, zero retries**. No rebuilding is needed for these source-only changes. The second invocation reads the first saved canonical manifest:

```bash
S09_SHA=7ebf5b0ec902bc5c9c112f96e0956568c47cfc22d719732dd85659079b8e4716
docker compose run --rm -T -e REPROLAB_GIT_COMMIT="$(git rev-parse HEAD)" app uv run --offline python -m reprolab.cli --manifest development --expected-manifest-sha256 "$S09_SHA" --input /app/inputs/Concrete_Data.xls --run-id s09-manual-a --max-seconds 300
docker compose run --rm -T -e REPROLAB_GIT_COMMIT="$(git rev-parse HEAD)" app uv run --offline python -m reprolab.cli --manifest /app/runs/s09-manual-a/manifest.json --expected-manifest-sha256 "$S09_SHA" --input /app/inputs/Concrete_Data.xls --run-id s09-manual-b --max-seconds 300
```

Compare identities, canonical manifest round-trips, measured values, and provenance without creating another artifact:

```bash
docker compose run --rm -T app python - <<'PY'
import hashlib
import json
import math
from pathlib import Path
from reprolab.manifest import LockedManifest, canonical_json, fingerprint
roots = [Path('/app/runs') / name for name in ('s09-manual-a', 's09-manual-b')]
a, b = [json.loads((root/'results.json').read_text()) for root in roots]
for key in ('manifest_sha256', 'dataset_sha256', 'split', 'model', 'environment', 'source'):
    assert a[key] == b[key], key
for root in roots:
    raw = (root/'manifest.json').read_bytes()
    manifest = LockedManifest.model_validate_json(raw)
    assert canonical_json(manifest).encode() == raw
    assert fingerprint(manifest) == hashlib.sha256(raw).hexdigest() == a['manifest_sha256']
    assert manifest.research.holdout_seed.value is None
    assert manifest.research.final_fit_intercept.value is None
    assert manifest.research.final_positive.value is None
for name, left in a['metrics'].items():
    right = b['metrics'][name]
    assert left['status'] == right['status'] == 'COMPUTED'
    assert math.isclose(left['value'], right['value'], rel_tol=1e-12, abs_tol=1e-12), name
    print(name, left['value'], 'absolute repeat difference:', abs(left['value']-right['value']))
assert a['execution_status'] == b['execution_status'] == 'COMPLETED'
assert a['reproduction_status'] == b['reproduction_status'] == 'INCONCLUSIVE'
assert a['split']['train_rows'] == 703 and a['split']['test_rows'] == 302
assert a['metrics']['MAPE']['denominator'] == {'retained_count': 302, 'excluded_zero_count': 0}
print('Repeatability and manifest round-trip: PASS; paper-reproduction status remains inconclusive.')
PY
```

Expected failure check: this uses an absent **input argument**, keeping the original XLS in place. The CLI must exit 2, remove its reservation, and leave no `results.json`. An existing failure-check run ID is also refused; use an unused ID to test the input error specifically.

```bash
docker compose run --rm -T app uv run --offline python -m reprolab.cli --manifest development --expected-manifest-sha256 "$S09_SHA" --input /app/inputs/missing.xls --run-id s09-manual-missing --max-seconds 300
test "$?" -eq 2
test ! -e runs/s09-manual-missing/results.json
git diff --check
git diff --cached --name-only
docker compose ps -a
```

Verify non-root access, immutable mounts, preserved input bytes, and absence of cache/scratch files:

```bash
docker compose run --rm -T app python - <<'PY'
import hashlib
import os
from pathlib import Path
assert os.getuid() == os.getgid() == 10001
for name in ('src/reprolab/cli.py', 'tests/test_experiment.py', 'uv.lock', 'inputs/Concrete_Data.xls'):
    assert not os.access(Path('/app')/name, os.W_OK)
assert os.access('/app/runs', os.W_OK) and os.access('/var/lib/reprolab', os.W_OK)
assert not Path('/app/docs').exists() and not Path('/app/.git').exists()
assert hashlib.sha256(Path('/app/inputs/Concrete_Data.xls').read_bytes()).hexdigest() == '710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4'
assert not list(Path('/tmp').glob('reprolab-s09-test-*'))
assert not Path('/app/.pytest_cache').exists()
assert not list(Path('/app/src').rglob('__pycache__'))
assert not list(Path('/app/tests').rglob('__pycache__'))
print('Non-root permissions, raw XLS identity, and scratch/cache audit: PASS')
PY
docker compose ps -a
```

Completed `s09-a`/`s09-b` artifacts are intentionally retained locally; generated outputs are ignored. The user approved S09 and separately authorized its six-file commit/push on 2026-11-25. The next comparison/report step remains planning-only until explicitly approved. Review questions: why can a completed repeatable run remain inconclusive? What does a null metric mean when its denominator is undefined? Which recorded identity captures uncommitted source changes?

## S10 comparison and honest Markdown report

[report.py](src/reprolab/report.py) has three public responsibilities: `validate_results` checks the saved S09-v1 result contract and its consistency with an approved manifest, lock, and independently audited split; `compare_run` separates artifact/protocol findings from arithmetic diagnostics; `render_markdown` creates deterministic text from saved evidence. These functions perform no file I/O, model fit, or source extraction. Small strict Pydantic records reject extra/missing fields, coercive strings/booleans, nonfinite measurements, inconsistent statuses, unsupported formulas/units, normalization mismatches, wrong dataset/split/model metadata, software drift, and invalid source provenance. Source digests describe historical runtime files; the newer reporting code is allowed to differ.

`cli.py --report-only` reads an existing run's manifest/results, verifies the manifest fingerprint and **a separately supplied trusted results-file SHA-256**, validates lock and recorded package versions, and re-creates only data preparation/split identity and held-out target statistics from the verified read-only XLS. It performs no training, prediction, or experiment rerun. Dataset bytes, preprocessing counts, split IDs, test population/normalization, model parameters, definition evidence, saved UTC timestamp, source-map checksum, and execution limits are checked before writing. Duplicate JSON keys, unsafe/symlink paths, missing/inconsistent artifacts, existing report files, and incomplete writes fail cleanly. The only new artifact is `runs/<run_id>/report.md`; the original two JSON files are never rewritten. Existing report files are refused with exit 2. Report mode retains the at-most-300-second parent deadline and uses no paid calls, retries, dependencies, or new mounts.

The extra `--expected-results-sha256` is deliberate: S09 did not retain predictions, so a reader cannot independently recompute every measured value without retraining. A checksum copied from trusted prior review detects otherwise plausible numeric edits; calculating a new checksum of a changed file does not approve that change. Hashes are integrity anchors, not signatures or proof of execution. This reporting layer validates the current fixed Concrete development profile; it cannot manufacture a complete historical paper protocol from missing fields.

### Observed numerical comparison

The generated local `runs/s09-a/report.md` uses the existing saved execution timestamp, **2026-11-23T14:30:23.666456+00:00**, and was verified on 2026-11-25. All original JSON evidence remains byte-identical. Comparisons use full decimal values with fixed rounding rules before deterministic formatting, `rtol=0`, and the following **human-selected display-precision** bounds. They are not paper-reported scientific acceptance thresholds:

| Metric | Published | Observed | Absolute arithmetic difference | Relative difference (%) | Abs tolerance | Display check | Definition compatibility | Eligible agreement |
|---|---:|---:|---:|---:|---:|---|---|---|
| RMSE (MPa) | 9.68 | 9.678767807275001 | 0.001232192724999 | 0.0127292636880 | 0.005 MPa | WITHIN | MATCH | WITHIN |
| MAE (MPa) | 7.59 | 7.589085799684043 | 0.000914200315957 | 0.0120447999467 | 0.005 MPa | WITHIN | MATCH | WITHIN |
| R² | 0.618 | 0.6182298804778745 | 0.0002298804778745 | N/A | 0.0005 | WITHIN | MATCH | WITHIN |
| MAPE (%) | 30.72 | 30.686085389150236 | 0.033914610849764 pp | 0.110399123860 | 0.005 pp | OUTSIDE | MATCH | OUTSIDE |
| nRMSE (%) | 61.81 | 61.78754886885589 | 0.02245113114411 pp | 0.0363228136938 | 0.005 pp | OUTSIDE | UNKNOWN | NOT_COMPARABLE |

`pp` means percentage points; relative difference is `100*absolute_difference/abs(published)` for positive error references. Zero references and R² use N/A for relative differences. Undefined measurements retain null values/reasons and receive `NOT_COMPARABLE`, never invented numbers. Tolerance boundaries are inclusive and based on the full values, not rounded table text.

RMSE, MAE, and R² fall inside the display bounds; MAPE and nRMSE fall outside arithmetically. MAPE uses the reviewed mean formula, and all **302** test targets are nonzero, so the code-derived zero mask leaves its denominator unchanged. With excluded zeros, the paper's retained denominator would be uncertain and its eligible comparison would be `NOT_COMPARABLE`. nRMSE uses the actual test std **15.66459259909823 MPa** and code-derived `ddof=0`; the published ddof remains unknown. Its arithmetic OUTSIDE label therefore does not become an eligible disagreement verdict.

### Scientific conclusion and provenance

The report distinguishes `MATCH`, `MISMATCH`, and `UNKNOWN` findings. Recorded dataset/preprocessing/split/model/environment information matches the approved development configuration. Published holdout seed/membership, final LR settings, exact PDF identity, and historical environment equivalence remain unresolved. Global/CV seed 42 never substitutes for the missing holdout seed, and the execution seed 123/four human-selected LR parameters never fill research nulls. Even identical scores cannot establish historical protocol equivalence. The S09 runs retain **COMPLETED execution / INDEPENDENT_REIMPLEMENTATION / INCONCLUSIVE reproduction**, and the report's scientific verdict is **INCONCLUSIVE**.

Report provenance includes dataset, canonical manifest, pinned result file, lock, ordered split-ID and source-map hashes, recorded package/platform/thread versions, evidence locations, and saved timestamps. It correctly labels the recorded S08 Git SHA as a caller-supplied base revision and preserves the four historical runtime-file hashes. Source-map self-consistency does not authenticate execution; no whole-worktree snapshot, signed attestation, or verified PDF hash is invented. Current schema/evidence does not establish a fully matched reproduction. No `docs/` answer key is read by runtime reporting.

The initial `s09-a/report.md` is **10,976 bytes**, SHA-256 `8b0c308e30ddded3c1f27806e5f7fdc908899a9e6fbaca6844e6a0f010f23c86`. It is intentionally ignored/local. The only saved S09 evidence checksums remain:

| Artifact | SHA-256 |
|---|---|
| Both saved manifests | `7ebf5b0ec902bc5c9c112f96e0956568c47cfc22d719732dd85659079b8e4716` |
| `s09-a/results.json` | `6756cb82b19c8791ba1584ca418e31e5cec23b4fd5af4bc751470809e1503b08` |
| `s09-b/results.json` | `5732c6cf51e0830b72ea2ed0796683c20db3dd87784479470ec020e67635921a` |

### Verify S10 now

Start Docker Desktop and work from this repository root. The report command is implemented. Tests and validation run inside Docker; no rebuild or host package installation is required:

```bash
docker info --format '{{.ServerVersion}}'
docker compose run --rm app uv run pytest -q
docker compose run --rm -T app uv run --offline pytest -q -k report
docker compose run --rm -T app uv run --offline ruff check --no-cache .
docker compose run --rm -T app ruff format --check src tests
docker compose run --rm -T app uv sync --locked --offline --no-cache --no-build
docker compose run --rm -T app uv lock --check --offline
cat runs/s09-a/report.md
```

Expected: **162 passed, zero failed/skipped**, including all 95 existing cases and 67 report cases; six files already formatted; lint/lock checks pass. Focused tests cover exact-score UNKNOWN/MISMATCH controls, wrong dataset/split/model rejection, missing/tampered/duplicate/nonfinite artifacts, all five tolerance boundaries, pp versus relative percentages, zero/undefined denominators, fixed decimal context, deterministic safe Markdown, no-fit report mode, JSON preservation, and overwrite/partial-write/deadline failure handling. Fixtures use scoped container `/tmp` with synthetic evidence and a reader stub; no new real-data experiment is run by report tests.

The report for `s09-a` already exists. This preservation check deliberately attempts an overwrite and expects exit 2; it must leave both JSON files and the report unchanged:

```bash
S10_MANIFEST_SHA=7ebf5b0ec902bc5c9c112f96e0956568c47cfc22d719732dd85659079b8e4716
S10_A_RESULTS_SHA=6756cb82b19c8791ba1584ca418e31e5cec23b4fd5af4bc751470809e1503b08
S10_BEFORE="$(shasum -a 256 runs/s09-a/manifest.json runs/s09-a/results.json runs/s09-a/report.md)"
docker compose run --rm -T app uv run --offline python -m reprolab.cli --report-only --run-id s09-a --expected-manifest-sha256 "$S10_MANIFEST_SHA" --expected-results-sha256 "$S10_A_RESULTS_SHA"
test "$?" -eq 2
test "$S10_BEFORE" = "$(shasum -a 256 runs/s09-a/manifest.json runs/s09-a/results.json runs/s09-a/report.md)"
```

Optional manual creation for the unused `s09-b/report.md` path uses its own trusted result checksum. This invocation audits data/saved artifacts and creates only that report; it never fits a model. It was not executed by the agent, which generated only the requested `s09-a` report. Once a report exists, the same command is refused:

```bash
docker compose run --rm -T app uv run --offline python -m reprolab.cli --report-only --run-id s09-b --expected-manifest-sha256 7ebf5b0ec902bc5c9c112f96e0956568c47cfc22d719732dd85659079b8e4716 --expected-results-sha256 5732c6cf51e0830b72ea2ed0796683c20db3dd87784479470ec020e67635921a --max-seconds 300
```

Independently render twice in memory and verify exact equality with the saved report, while checking original bytes against approved hashes:

```bash
docker compose run --rm -T app python - <<'PY'
import hashlib
import json
from pathlib import Path
from reprolab.experiment import load_concrete, remove_duplicates, split_data
from reprolab.manifest import LockedManifest
from reprolab.report import render_markdown
root = Path('/app/runs/s09-a')
manifest_bytes = (root/'manifest.json').read_bytes()
results_bytes = (root/'results.json').read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest() == '7ebf5b0ec902bc5c9c112f96e0956568c47cfc22d719732dd85659079b8e4716'
result_sha = hashlib.sha256(results_bytes).hexdigest()
assert result_sha == '6756cb82b19c8791ba1584ca418e31e5cec23b4fd5af4bc751470809e1503b08'
m = LockedManifest.model_validate_json(manifest_bytes)
r = json.loads(results_bytes)
clean, _ = remove_duplicates(load_concrete('/app/inputs/Concrete_Data.xls'))
train, test = split_data(clean, seed=m.split.seed.value)
split_sha = hashlib.sha256(json.dumps({'train':train.row_ids,'test':test.row_ids}, sort_keys=True, separators=(',',':')).encode()).hexdigest()
context = dict(lock_bytes=Path('/app/uv.lock').read_bytes(), split_identity=split_sha, results_sha256=result_sha)
first = render_markdown(m, r, **context)
assert first == render_markdown(m, r, **context) == (root/'report.md').read_text()
assert (root/'manifest.json').read_bytes() == manifest_bytes
assert (root/'results.json').read_bytes() == results_bytes
print('Deterministic report SHA-256:', hashlib.sha256(first.encode()).hexdigest())
print('Scientific verdict remains INCONCLUSIVE; original evidence unchanged.')
PY
git diff --check
git diff --cached --name-only
docker compose ps -a
```

The reporter detects structural/configuration inconsistencies and pinned-file changes. It cannot independently authenticate a caller-provided checksum, reconstruct discarded predictions, or recover from arbitrary machine loss during a write; a caught write error removes only its newly created incomplete report. The scientific limitations remain visible. The user approved S10 following manual verification and separately authorized its five-file commit/push on 2026-11-25; S11 implementation was subsequently authorized separately. Review questions: why does nRMSE have an OUTSIDE arithmetic check but NOT_COMPARABLE eligible status? Why do three WITHIN values leave the scientific verdict inconclusive?

## S11 validator and metric consistency regressions

[test_manifest.py](tests/test_manifest.py) adds **11 cases** to the existing 162, after checking their coverage. Eight cases delete exactly one required field from an otherwise valid in-memory development manifest: split seed; each of `fit_intercept`, `positive`, `copy_X`, and `n_jobs`; paper evidence; nRMSE `ddof`; or MAPE zero-target policy. Each expects Pydantic `ValidationError` with type `missing` at that exact field. Passing a negative test means the incomplete configuration was rejected, rather than completed with a default. The synthetic lock digest is a schema input, not a claim that a lockfile was verified by those unit tests.

Three cases check perfect predictions, imperfect predictions, and negative R² using the same synthetic targets `(2, 4, 6)`. Their mean is 4, total squared target deviation is 8, and population variance is 8/3. Independently specified predictions produce squared-error sums of 0, 4, and 48:

| Case | Predictions | Expected R² | Expected nRMSE (%) |
|---|---|---:|---:|
| Perfect | `(2, 4, 6)` | 1 | 0 |
| Imperfect | `(2, 4, 8)` | 0.5 | `100 / sqrt(2)` |
| Negative R² | `(6, 8, 10)` | −5 | `100 * sqrt(6)` |

Each test first checks the independent expected values, units, counts, and population standard deviation, then asserts **`nRMSE / 100 ≈ sqrt(1 − R²)`**, using **rtol=atol=1e-12** (`pytest.approx(rel=..., abs=...)`). The identity requires the same aligned, unweighted evaluation population, at least two nonconstant targets, and nRMSE normalized by that population's standard deviation with **ddof=0**. It does not establish the paper's unresolved normalization convention and must not be applied to another denominator.

The existing tests retain known-answer RMSE/MAE/R²/MAPE/nRMSE, MAPE zero handling, unsupported formulas, failed executions, incompatible protocols, and report classifications. S11 adds no duplicate report suite, production changes, dependencies, Compose changes, training runs, sweeps, or new artifacts. The full suite still includes its existing tiny synthetic model fits; the new S11 tests only validate in-memory manifests and evaluate fixed predictions.

From the repository root, with Docker running and the existing approved input/run mounts available:

```bash
docker compose run --rm -T app uv run --offline pytest -q
docker compose run --rm -T app uv run --offline pytest -v tests/test_manifest.py
docker compose run --rm -T app uv run --offline ruff check --no-cache .
docker compose run --rm -T app ruff format --check src tests
docker compose run --rm -T app uv lock --check --offline
docker compose run --rm -T app uv sync --locked --offline --no-cache --no-build
docker compose run --rm -T app id
git diff --check
git diff --cached --name-only
docker compose ps -a
```

Observed: **173 collected/passed, 0 failed/skipped** overall; **11 collected/passed, 0 failed/skipped** independently. Ruff lint/format (seven files), offline lock/frozen sync, and Git whitespace checks passed. Runtime UID/GID **10001**, read-only tests/source/data/lock, disabled pytest cache, absent bytecode/scratch, and container cleanup were verified. An initial format check requested two line-wrap changes in the new file; those were applied and the check passed. Original S09 JSON and the S10 report remain byte-identical and ignored. Published claims, source settings, manifests, and production code are unchanged; these unit tests cannot establish scientific reproduction. The user approved S11 based on successful verification on 2026-11-25 and separately authorized its three-file commit/push. S12 is planning-only until explicitly approved.

Review questions: why divide nRMSE by 100? Why does a passing missing-field test indicate a rejection? Why does this identity leave the paper's normalization unresolved?

Future controlled experiment sweeps are recorded as a [deferred roadmap proposal](docs/progress.md#future-roadmap-proposal--controlled-experiment-sweeps-deferred), not an S12 requirement: documented seed candidates including 42 and 123, scientifically justified model variants, independent manifests/results for every experiment, and consolidated reporting with separate numerical-agreement and protocol-verification statuses. All planned outcomes must be disclosed; exploratory matches must not be cherry-picked or relabelled as verified historical configurations. No sweep support or execution is implemented here.

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
| `compose.yaml` | One development service, read-only source/input mounts, writable run outputs, and checkpoint storage |
| `inputs/` (ignored, local only) | Unmodified UCI XLS and official README; not included in Git or the image |
| `src/reprolab/__init__.py` | Minimal package marker |
| `src/reprolab/experiment.py` | Verified XLS loading, data preparation, explicit LR fit/predict, and test metric definitions |
| `src/reprolab/manifest.py` | Strict immutable manifest, source evidence/uncertainties, reviewed development fixture, and content fingerprint |
| `src/reprolab/cli.py` | Bounded offline argparse runner, strict validation, and guarded artifact publication |
| `src/reprolab/report.py` | Strict result validation, compatibility gates, display-precision comparisons, and deterministic Markdown |
| `tests/test_experiment.py` | Data/model/metric/CLI regressions and optional read-only XLS integration |
| `tests/test_manifest.py` | Eight required-field regressions and three population-normalized nRMSE/R² consistency cases |
| `runs/` (ignored, local only) | Canonical manifests, actual measured results, and generated reports; not included in Git or image |

The Git remote is [kanchanpotdar/reprolabs](https://github.com/kanchanpotdar/reprolabs), configured locally as `origin`. Local preparation does not imply that these files have been published.

## Local files and source attribution

Local paper/data downloads belong in the ignored `inputs/` directory when the relevant step authorizes acquisition. Generated experiment artifacts belong in ignored `runs/` when experiments exist. Neither directory is created by S01. Python environments and caches are also ignored. `.env.example` is exempted from the `.env.*` rule so a safe configuration example can be added in its creating step.

Ignore rules prevent ordinary Git discovery/staging; they do not remove previously tracked files or inspect file contents for secrets. Review status and staged content before any commit.

The [UCI dataset](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) and paper identify CC BY 4.0 licenses. Their attribution, exact source identities, and the separate author-code licensing uncertainty are documented in the S00 evidence. No license has been assigned to this project's code.
