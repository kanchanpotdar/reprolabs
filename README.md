# ReproLab

An evidence-driven research reproducibility agent, planned to reconstruct an ML paper's experimental protocol, run a human-approved experiment, and compare observed metrics with published claims. Missing evidence and incompatible protocols must remain visible in the result.

## Current state

This repository contains project instructions, a staged roadmap, a paper feasibility review, a pinned Python environment, and a Docker development image configuration. There is no application, runnable CLI, or model experiment yet.

| Step | State | Evidence |
|---|---|---|
| S00 — Paper feasibility spike | Human-approved **CONDITIONAL**, 2026-11-21 | [Paper evidence and uncertainties](docs/p01_ground_truth.md) |
| S01 — Repository hygiene | Human-approved, 2026-11-21; reported checks rerun successfully | This README, `.gitignore`, local Git initialization, and [approval record](docs/progress.md) |
| S02 — Reproducible Python environment and checks | Human-approved, 2026-11-21, after review of reported checks | `pyproject.toml`, `uv.lock`, and [approval record](docs/progress.md) |
| S03 — Development Docker image | Human-approved, 2026-11-22, based on successful Docker verification | `Dockerfile` and `.dockerignore`; results in [progress](docs/progress.md) |

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
| First `RUN` | Creates user/group `reprolab` with UID/GID 10001, its home, and writable `/app` and `/opt/venv` directories. |
| `WORKDIR /app` | Sets the working directory for later build instructions and runtime commands. |
| Project `COPY --chown=...` | Copies only `pyproject.toml`, `uv.lock`, and this README, owned by the unprivileged user. |
| `USER reprolab:reprolab` | Runs subsequent build instructions and containers without root privileges. |
| Final `RUN` | Uses `uv sync --locked --no-cache --no-build` to install existing locked dependencies, including development tools, then prints Python/uv versions. Downloads use uv's temporary cache; source distributions are not compiled. |
| `CMD ["python", "--version"]` | Prints the effective Python version when no command is supplied; there is no application entry point yet. |

The Python and uv references include registry-verified multi-platform digests in [Dockerfile](Dockerfile). These pin the selected image content; platform and system-library differences still matter for experiments. Dependencies are installed inside the image and do not reuse the host `.venv`.

[.dockerignore](.dockerignore) starts by excluding everything, then permits only the three project files required by this image. Docker still receives its build instructions as metadata. This keeps `.env`, secret files, `.venv`, `.git`, `docs/` answer keys, local datasets, run outputs, and unrelated files out of the build context. Future source inclusion must be added deliberately in its creating step; S03 does not add Compose or application source.

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

The Git remote is [kanchanpotdar/reprolabs](https://github.com/kanchanpotdar/reprolabs), configured locally as `origin`. Local preparation does not imply that these files have been published.

## Local files and source attribution

Local paper/data downloads belong in the ignored `inputs/` directory when the relevant step authorizes acquisition. Generated experiment artifacts belong in ignored `runs/` when experiments exist. Neither directory is created by S01. Python environments and caches are also ignored. `.env.example` is exempted from the `.env.*` rule so a safe configuration example can be added in its creating step.

Ignore rules prevent ordinary Git discovery/staging; they do not remove previously tracked files or inspect file contents for secrets. Review status and staged content before any commit.

The [UCI dataset](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) and paper identify CC BY 4.0 licenses. Their attribution, exact source identities, and the separate author-code licensing uncertainty are documented in the S00 evidence. No license has been assigned to this project's code.
