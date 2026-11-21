# ReproLab

An evidence-driven research reproducibility agent, planned to reconstruct an ML paper's experimental protocol, run a human-approved experiment, and compare observed metrics with published claims. Missing evidence and incompatible protocols must remain visible in the result.

## Current state

This repository contains project instructions, a staged roadmap, a paper feasibility review, and a pinned Python environment configuration. There is no application, runnable CLI, or model experiment yet.

| Step | State | Evidence |
|---|---|---|
| S00 — Paper feasibility spike | Human-approved **CONDITIONAL**, 2026-11-21 | [Paper evidence and uncertainties](docs/p01_ground_truth.md) |
| S01 — Repository hygiene | Human-approved, 2026-11-21; reported checks rerun successfully | This README, `.gitignore`, local Git initialization, and [approval record](docs/progress.md) |
| S02 — Reproducible Python environment and checks | Human-approved, 2026-11-21, after review of reported checks | `pyproject.toml`, `uv.lock`, and [approval record](docs/progress.md) |

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

S02 permits a one-time host uv bootstrap before Docker exists. From this repository root, run:

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

The Git remote is [kanchanpotdar/reprolabs](https://github.com/kanchanpotdar/reprolabs), configured locally as `origin`. Local preparation does not imply that these files have been published.

## Local files and source attribution

Local paper/data downloads belong in the ignored `inputs/` directory when the relevant step authorizes acquisition. Generated experiment artifacts belong in ignored `runs/` when experiments exist. Neither directory is created by S01. Python environments and caches are also ignored. `.env.example` is exempted from the `.env.*` rule so a safe configuration example can be added in its creating step.

Ignore rules prevent ordinary Git discovery/staging; they do not remove previously tracked files or inspect file contents for secrets. Review status and staged content before any commit.

The [UCI dataset](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) and paper identify CC BY 4.0 licenses. Their attribution, exact source identities, and the separate author-code licensing uncertainty are documented in the S00 evidence. No license has been assigned to this project's code.
