# ReproLab

An evidence-driven research reproducibility agent, planned to reconstruct an ML paper's experimental protocol, run a human-approved experiment, and compare observed metrics with published claims. Missing evidence and incompatible protocols must remain visible in the result.

## Current state

This repository contains project instructions, a staged roadmap, a paper feasibility review, a pinned Python environment, a one-service Docker Compose development configuration, and verified local UCI dataset provenance. There is no application, runnable CLI, or model experiment yet.

| Step | State | Evidence |
|---|---|---|
| S00 — Paper feasibility spike | Human-approved **CONDITIONAL**, 2026-11-21 | [Paper evidence and uncertainties](docs/p01_ground_truth.md) |
| S01 — Repository hygiene | Human-approved, 2026-11-21; reported checks rerun successfully | This README, `.gitignore`, local Git initialization, and [approval record](docs/progress.md) |
| S02 — Reproducible Python environment and checks | Human-approved, 2026-11-21, after review of reported checks | `pyproject.toml`, `uv.lock`, and [approval record](docs/progress.md) |
| S03 — Development Docker image | Human-approved, 2026-11-22, based on successful Docker verification | `Dockerfile` and `.dockerignore`; results in [progress](docs/progress.md) |
| S04 — One-service Compose setup | Human-approved, 2026-11-22 | `compose.yaml`; results in [progress](docs/progress.md) |
| S05 — Dataset acquisition and provenance | Human-approved, 2026-11-22, based on successful dataset verification | Ignored raw inputs; [source identity, schema, units, license, and discrepancies](docs/p01_ground_truth.md#8-s05-acquisition-and-provenance--observed-2026-11-22) |

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

The planned first implementation is a fixed, human-approved manifest → data validation → local model run → metrics → comparison report. Paper parsing and orchestration come later. This flow is planned, not implemented.

The ground-truth document is a human reference. Future extraction code and its model/tool access must not read `docs/` or receive these answer keys during evaluation.

## S02 environment and verification

Use **Python 3.12.16** and **uv 0.13.8**. The project enforces both versions in [pyproject.toml](pyproject.toml). Direct dependencies are scikit-learn **1.6.1**, with pytest **9.2.0** and Ruff **0.17.6** in the default development group. [uv.lock](uv.lock) records the resolved transitive dependencies and artifact hashes. The repository is not installed as a package because application source does not exist yet.

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

`uv sync --locked` creates or synchronizes the ignored `.venv` and fails if the manifest and lockfile disagree. Ruff checks Python code without executing it; the project currently has no Python source to lint. Pytest is configured but no application tests exist, so a full pytest run is not a passing test suite at this step. Once Compose is available, use Docker for project execution as required by `AGENTS.md`.

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

Expected versions are Python **3.12.16**, uv **0.13.8**, sklearn **1.6.1**, and pytest **9.2.0**; the runtime UID is **10001**. Ruff should succeed, although application source does not exist yet. Each `--rm` command removes its transient container on exit. The `reprolab-dev` image remains available locally for verification. No ports, host mounts, Docker socket, privileged mode, or additional service are required. This is a development environment; executing untrusted author code requires a separate approved runner design.

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

[.dockerignore](.dockerignore) starts by excluding everything, then permits only the three project files required by this image. Docker still receives its build instructions as metadata. This keeps `.env`, secret files, `.venv`, `.git`, `docs/` answer keys, local datasets, run outputs, and unrelated files out of the build context. Future source inclusion must be added deliberately in its creating step; S03 does not add Compose or application source.

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

Expect only `app` in the service listing, Python **3.12.16**, Ruff success, UID **10001**, and no leftover verification containers. Ruff currently validates the environment/configuration; there is no application code to lint yet. Compose runs commands in disposable containers; the named checkpoint volume persists after those containers exit.

| Configuration | Purpose |
|---|---|
| `build: .`, `image: reprolab-dev` | Builds and uses the pinned development image. |
| Three read-only bind mounts | Expose only current `pyproject.toml`, `uv.lock`, and `README.md` at `/app`. Host edits are read on the next one-off run. Application source/test directories will be mounted when those files exist; S04 creates no empty scaffolding. |
| `create_host_path: false` | Fails for a missing source file instead of silently creating a host directory. |
| `UV_LOCKED=1` | Makes `uv run` reject manifest/lock drift; it must not rewrite the mounted lockfile. |
| `checkpoint_state:/var/lib/reprolab` | Reserves Docker-managed storage for future SQLite checkpoints; no database is created in S04. The image pre-creates this path for UID/GID 10001 so a new volume can be used without root. |

Dependencies remain inside `/opt/venv`, outside the bind mounts. The whole repository is not mounted: `.env`, host `.venv`, `.git`, `docs/` answer keys, inputs, and run artifacts are not exposed by this configuration. Build-context exclusions and runtime mount selection are separate controls. No Docker socket, privileged mode, ports, or additional service is configured.

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

From this repository root with Docker running, the following acquisition command is optional if the two verified files are already present. It downloads only the official UCI archive, validates every member before writing, and refuses to overwrite a different local file. It has a 60-second network socket timeout, a 1 MB response limit, and no automatic retries. It retains only the original XLS and official README; the ZIP is scoped to container `/tmp` and cleaned even on failure. No host Python packages are installed.

```bash
mkdir -p inputs
docker compose run --rm -T --volume "$PWD/inputs:/app/inputs" app python - <<'PY'
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

The Git remote is [kanchanpotdar/reprolabs](https://github.com/kanchanpotdar/reprolabs), configured locally as `origin`. Local preparation does not imply that these files have been published.

## Local files and source attribution

Local paper/data downloads belong in the ignored `inputs/` directory when the relevant step authorizes acquisition. Generated experiment artifacts belong in ignored `runs/` when experiments exist. Neither directory is created by S01. Python environments and caches are also ignored. `.env.example` is exempted from the `.env.*` rule so a safe configuration example can be added in its creating step.

Ignore rules prevent ordinary Git discovery/staging; they do not remove previously tracked files or inspect file contents for secrets. Review status and staged content before any commit.

The [UCI dataset](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) and paper identify CC BY 4.0 licenses. Their attribution, exact source identities, and the separate author-code licensing uncertainty are documented in the S00 evidence. No license has been assigned to this project's code.
