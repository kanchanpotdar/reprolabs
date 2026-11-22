# ReproLab — human-verified progress

- **Current step:** S04 — one-service Compose setup
- **Current status:** APPROVED by the user
- **Next step:** S05 implementation authorized separately; stop for review before any S05 commit/push or S06 work
- **Approved steps:** S00 — APPROVED (CONDITIONAL); S01 and S02 — APPROVED, 2026-11-21; S03 and S04 — APPROVED, 2026-11-22
- **Commit/push:** S00 + S01 pushed as `837a92101d5fbaec82a8c6bf73dc854758355860`; S02 pushed as `0835992e92ae3763008a4fb3d849f4169892cff8`; S03 pushed as `db5a995465f2bd2ee6c9a206b46adda1d5a27dc5`; S04 commit/push authorized, with SHA and verified remote outcome reported in the handoff

This file is authoritative for the human review gate. Update it in the **same commit** as each approved step. Do not advance a step merely because automated tests pass; record the human's verification first.

## S00 candidate — approved CONDITIONAL, not an approved reproduction

- Paper: https://www.mdpi.com/2076-3417/15/23/12383
- Target: Yeh / UCI Concrete Compressive Strength; `LinearRegression`.
- Evidence: [P01 ground truth](p01_ground_truth.md), reviewed 2026-11-21. The user explicitly approved S00 as **CONDITIONAL**, accepting the documented unresolved seed and Linear Regression settings.
- Table 6 published Linear Regression claims: RMSE **9.68 MPa**, MAE **7.59 MPa**, MAPE **30.72%**, R² **0.618**, nRMSE **61.81%**. These are paper claims, not local experiment results.
- The paper describes removing 25 duplicates (1030 → 1005) and a 70/30 split. Its global/CV seed statement is **42**; the pinned author notebook's explicit holdout seed is **123**. The seed and split membership that generated Table 6 remain unresolved.
- The paper describes a standard LR baseline; the notebook searches `fit_intercept` and `positive`. Final settings for the published row remain unresolved.
- S00 source checks recorded metric definitions, a pinned author commit, and dataset hashes; UCI and author workbooks were byte-identical. Exact canonical paper version, historical split/settings, declared environment reproducibility, and independent metric reproduction remain unverified. No model was run.
- S00 distinguished the explained raw/cleaned row counts from unresolved Table 1/Table 6 metrics and 3.49/3.71 RMSE values, plus the contradictory correlation threshold (ρ > 0.8 versus 0.74). Details and evidence locations are in the ground-truth document.
- **S00 version-control exception:** Complete and obtain human approval for S00 without a Git commit. S01 creates `.gitignore`, initializes Git if needed, and prepares the first commit including both S00 and S01, subject to separate human approval and instruction.

## Approval log

| Step | Type | Status | Human-observed test/result | Decision and date | Commit / push |
|---|---|---|---|---|---|
| S00 | concept | APPROVED (CONDITIONAL) | User explicitly accepted the feasibility verdict with unresolved seed and LR settings documented; individual manual commands/source checks were not reported | APPROVED by user, 2026-11-21 (Asia/Kolkata) | Included with S01 in the authorized initial commit; see Git history/handoff for SHA and push verification |
| S01 | mechanical | APPROVED | User approved subject to reported checks passing; the agent reran those checks successfully; personal commands were not separately supplied | APPROVED by user, 2026-11-21 (Asia/Kolkata) | Authorized initial commit with S00 to origin/main; see Git history/handoff for SHA and push verification |
| S02 | mechanical | APPROVED | User approved after reviewing reported checks; individual personal commands were not supplied | APPROVED by user, 2026-11-21 (Asia/Kolkata) | Commit/push to origin/main authorized; see Git history/handoff for SHA and remote verification |
| S03 | mechanical | APPROVED | User explicitly approved based on successful Docker verification; individual personal commands were not supplied | APPROVED by user, 2026-11-22 (Asia/Kolkata) | Commit/push to origin/main authorized; see Git history/handoff for SHA and remote verification |
| S04 | mechanical | APPROVED | User explicitly approved S04; reported config/build/runtime/mount/persistence/cleanup results retained; individual personal commands were not supplied | APPROVED by user, 2026-11-22 (Asia/Kolkata) | Commit/push to origin/main authorized; see Git history/handoff for SHA and remote verification |

### S00 approval record

- User decision: “I approve S00 as CONDITIONAL, with the unresolved seed and Linear Regression settings explicitly documented.”
- Approval scope: accept the paper as a conditional candidate; no claim of matched reproduction or successful model execution.
- Commands the human personally ran: not supplied. No individual checklist completion is inferred from the approval.
- Open uncertainties and source-check limitations remain in `p01_ground_truth.md`; the approval does not convert unknown fields into verified settings.
- S00 temporary downloads/renders were removed by the agent; human cleanup verification was not separately reported.
- Version control: the user subsequently approved S01 and explicitly authorized committing and pushing the combined S00 + S01 initial change set to `origin/main`.

### S01 approval record

- New files: `README.md` for current project orientation; `.gitignore` for local configuration/secrets, downloaded inputs, generated runs, environments, and caches.
- Repository setup: local Git initialized on `main`; the user-supplied `https://github.com/kanchanpotdar/reprolabs.git` is configured as `origin`. The GitHub API reported the remote repository empty before the authorized initial push.
- Documentation synchronization: record this S00 approval here and in the ground-truth document without changing its scientific claims or unresolved fields.
- User decision: “I approve S01, subject to the reported checks passing.” The same message separately authorizes staging only the six intended files, reviewing for secrets/temporary files, committing, and pushing S00 + S01 to `origin/main`.
- Agent checks rerun successfully on 2026-11-21: exact six-file inventory; 32 representative ignored paths and 11 trackable paths checked without creating probe files; README checker found no issues across seven local links after approval synchronization; supplied `AGENTS.md` and roadmap hashes unchanged. Staged-content and whitespace checks passed; the six intended text files contained no credential-pattern findings, datasets, or temporary artifacts.
- Commands the human personally ran: not supplied. The user's conditional approval is recorded without inventing personal test observations.
- S00's unresolved seed, LR settings, and other scientific limitations remain accepted conditions. No package environment, application code, or S02 implementation is included.
- Initial commit message authorized by user: `chore: initialize ReproLab with S00 evidence and repository hygiene`. The handoff reports the resulting SHA and remote verification; no follow-up commit is created just to record its own hash here.

### S02 approval record

- User authorization: implement S02 with minimal dependencies, exact version pins, `pyproject.toml`, `uv.lock`, pytest/Ruff configuration, and the permitted host bootstrap. Do not commit, push, or proceed to S03 before explicit approval.
- Two new project files: `pyproject.toml` and generated `uv.lock`. README/progress changes document this step and preserve the approval gate. No source, tests, Docker files, or extra requirements manifests are created.
- Existing host tools reused: Python 3.12.16 and uv 0.13.8. Both are pinned in the project; no global installation or interpreter download is needed. Dependencies are installed only into ignored `.venv`; download caches are scoped to temporary storage.
- Direct dependency: scikit-learn 1.6.1. Development group: pytest 9.2.0 and Ruff 0.17.6. Other packages are resolved transitively and frozen in `uv.lock`; unused planned libraries and agent frameworks remain deferred.
- Environment limitation: the author declares Python 3.12.12, NumPy 2.0.2, and SciPy 1.16.3. This development baseline pins Python 3.12.16; its generated lockfile resolves NumPy 2.5.5 and SciPy 1.18.1. It is not evidence of a matched paper environment or model reproduction.
- Bootstrap observation: the first dependency sync reached its 300-second download timeout before installation completed; its temporary cache was cleaned. The checkout was renamed from `reprolab_codex_plan_v3` to `reprolab` during this session. One retry in the current path succeeded within a 600-second download/install cap. No cause is inferred beyond the observed timeout and folder change. No global tools or system packages were installed.
- Required checks passed on 2026-11-21: `uv sync --locked` installed 12 packages into the ignored project `.venv`; `uv run ruff check .` printed `All checks passed!`; `uv run python -c 'import sklearn; print(sklearn.__version__)'` printed `1.6.1`. There is no application source to lint yet; Ruff's success verifies the tool/configuration rather than application quality.
- Observed versions: CPython 3.12.16, uv 0.13.8, scikit-learn 1.6.1, pytest 9.2.0, Ruff 0.17.6, NumPy 2.5.5, SciPy 1.18.1. The lock also includes the Windows-only conditional dependency colorama; the local virtual project itself is not installed as a distribution.
- Pytest check: `uv run --locked pytest --collect-only -p no:cacheprovider` identified `pyproject.toml` as its configuration and collected zero tests, exiting with expected code 5. No application tests exist yet; this is not a passing model/application test suite.
- Lockfile verification: required checks left `uv.lock` unchanged. In a disposable copy, changing the local project version caused `uv lock --check` to reject the stale lock explicitly without rewriting it; the same check worked offline after registry metadata was cached. Initial offline probes with empty metadata caches were inconclusive, not evidence of the lock guard. All probe copies and temporary download caches were cleaned.
- Source review: the lock contains only public PyPI registry artifacts with SHA-256 hashes; no private registry credentials or machine-specific paths. Lock SHA-256: `13f0bfbe84fc6fc2b9e6ec440aaa588ee75fd971953d780ad0085997bb29d67d`.
- User decision: “I approve S02 after reviewing the reported checks.” The user separately authorized staging the intended files, reviewing for secrets/unnecessary artifacts, committing with `build: pin Python environment and configure checks`, and pushing to `origin/main`.
- Human-observed review: approval of the reported checks is explicit; individual commands the human personally ran were not supplied and are not inferred. The documented environment differences and absence of application/model tests remain unchanged.
- Commit scope: `pyproject.toml`, `uv.lock`, `README.md`, and this progress record. The handoff reports the resulting commit SHA and verified remote outcome. No follow-up commit is created merely to record its own hash here.
- At the S02 handoff, only an S03 scope explanation was requested. The user subsequently authorized S03 implementation separately, as recorded below.

### S03 approval record

- User authorization on 2026-11-22: implement the pinned Docker environment, build it, run S03 verification, explain each Dockerfile instruction, and stop before any commit, push, or S04 work. This authorizes implementation; final review of the resulting files/checks remains pending.
- Two new files: `Dockerfile` and `.dockerignore`. README/progress edits document the environment and verification procedure. No Compose or application files are created; no project packages are installed on the host.
- Registry-verified image-index pins: `python:3.12.16-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df` and `ghcr.io/astral-sh/uv:0.13.8@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85`. Digests were resolved through `docker buildx imagetools inspect` on 2026-11-22. The built/tested platform is **linux/arm64**; other platforms are not execution-verified by S03.
- Image layout: Debian Bookworm slim with Python 3.12.16; pinned uv executable; dependencies in `/opt/venv`; work directory `/app`; user/group `reprolab` UID/GID 10001. Only `pyproject.toml`, `uv.lock`, and README are copied. Installation uses `uv sync --locked --no-cache --no-build` as the non-root user, including development tools. No privileged mode, host mounts, ports, Docker socket, extra services, or source compilation are required.
- Resource budget: zero paid calls; configurable `REPROLAB_S03_BUILD_TIMEOUT_SECONDS` defaults to 900 seconds per build attempt, with at most one retry for a diagnosed download failure. No model training or paper experiment is part of S03.
- Docker context check passed using a disposable scratch build/export: only the three allowed project files reached the export; dummy `.env`, `.venv`, `inputs`, `runs`, `.git`, `docs`, and unrelated-file probes were excluded. Real secrets/data were not used. The temporary context/export was cleaned. Docker's missing-Git-metadata warning for the temporary non-repository context was informational and did not affect the exclusion check.
- Required build passed on the first attempt: `docker build -t reprolab-dev .` exited 0 within the 900-second cap. The build installed 12 locked packages inside the image as the unprivileged user, printed Python 3.12.16 and uv 0.13.8, and left the host lockfile unchanged. No retry or host dependency installation was needed.
- All runtime commands exited 0: default `docker run --rm reprolab-dev`; explicit `python --version` → **3.12.16**; `uv --version` → **0.13.8**; sklearn import/version → **1.6.1**; `id -u` → **10001**; `ruff check .` → **All checks passed!**; `pytest --version` → **9.2.0**. No application source/tests exist; these are environment checks rather than model or application correctness results.
- Additional runtime assertions passed: UID/GID both 10001; environment `/opt/venv`; exactly `README.md`, `pyproject.toml`, and `uv.lock` in `/app`; no copied host `.venv` or retained uv download cache; container lock SHA-256 equals the unchanged host lock; a `TemporaryDirectory` under `/tmp` is writable and removed after its context exits. NumPy **2.5.5** and SciPy **1.18.1** match the lock.
- Built local image ID/digest: `sha256:3831ec67a3dfd7717f1b77101c57ad7f1b6e427929395d177c9342bb100b0c20`, tag `reprolab-dev:latest`, configured user `reprolab:reprolab`, default command `["python", "--version"]`. This is a local build artifact; no image publication occurred.
- Cleanup: all verification containers used `--rm`; temporary context/export files and in-container scratch data were removed. The development image and ordinary Docker build cache remain for human verification. No project virtual environment or dependency was added/changed on the host by S03.
- User decision: “I approve S03 based on the successful Docker verification.” The same message separately authorizes final diff review, staging only intended files, committing with `build: add pinned non-root Docker development image`, and pushing to `origin/main`.
- Human-observed review: approval based on the reported Docker verification is explicit; individual commands personally run by the human were not supplied and are not inferred. The recorded platform limitation and absence of model/application tests remain unchanged.
- Commit scope: `Dockerfile`, `.dockerignore`, `README.md`, and this progress record. The handoff reports the resulting SHA and verified remote outcome; no follow-up commit is created merely to record its own hash.
- At the S03 handoff only an S04 explanation was requested. The user subsequently authorized S04 implementation separately, as recorded below.

### S04 approval record

- User authorization on 2026-11-22: implement one Compose `app` service, selective source mounts, and a named volume for future SQLite; adjust Dockerfile only for permissions; verify runtime, non-root access, persistence, and container cleanup. Stop before commit, push, or S05.
- One new file, `compose.yaml`; Dockerfile change only extends existing directory creation/ownership to `/var/lib/reprolab`. README/progress changes document this step. Dependencies, base-image digests, lockfile, and scientific ground truth remain unchanged.
- Mount scope: only existing `pyproject.toml`, `uv.lock`, and README are bound read-only into `/app`, with `create_host_path: false`. There is no application source yet; no empty source/test/input/run directories are created. Host secrets, `.venv`, Git history, and `docs/` answer keys are not mounted. Dependencies remain at `/opt/venv`.
- Stable Compose project name `reprolab`; exactly one `app` service, image `reprolab-dev`, and named volume `checkpoint_state` at `/var/lib/reprolab` (default Docker name `reprolab_checkpoint_state`). `UV_LOCKED=1` enforces locked `uv run` behavior. No privileged mode, Docker socket, published ports, or extra service is configured.
- Resource budget: zero paid calls; build timeout configurable via `REPROLAB_S04_BUILD_TIMEOUT_SECONDS`, default 900 seconds per attempt, at most one retry for a diagnosed download failure. No host project package installation or model experiment is part of S04.
- Compose v5.7.0 is available. `docker compose config --services` reports only `app`; parsed configuration checks passed for the three read-only file mounts, missing-path protection, named volume, and absence of privileged/port/device configuration.
- Build passed on the first attempt within the 900-second cap: `docker compose build` installed 12 locked packages inside the image and printed Python 3.12.16 / uv 0.13.8. Dependency downloads took about 10 minutes 41 seconds; no retry, source compilation, lockfile change, or host dependency installation was needed. Built/tested platform: **linux/arm64**. Local image ID/digest: `sha256:80732adc1d14c2369d5983fa83db503e2e0c3babea6a9b0778b2bb772e53e9c5`.
- Required runtime checks passed: `docker compose run --rm app python --version` → **Python 3.12.16**; `docker compose run --rm app uv run ruff check .` → **All checks passed!**. Additional checks returned UID **10001**, uv **0.13.8**, and sklearn **1.6.1**. Verification containers used unique task-scoped names alongside `--rm` so their removal could be checked explicitly.
- Permission/mount assertions passed: UID/GID both 10001; `/opt/venv` remains the dependency environment; `UV_LOCKED=1` is present; all three mounted file hashes match current host files; Linux mount metadata confirms each bind mount is read-only; `/app` exposes only those three files. The named state directory is owned by UID/GID 10001 and is readable/writable/traversable without root. A scoped scratch file under `/tmp` was removed after its context exited.
- Persistence passed across two different containers: the first created an exclusive UUID-named marker in `/var/lib/reprolab`, then was removed; the second read the exact marker contents and deleted only that marker. No SQLite database, checkpointer, or application source was created.
- Cleanup passed: each of the eight successful verification containers was absent after its `--rm` run; project container IDs matched the empty pre-check baseline; `docker compose ps -a` showed only headers. There were no pre-existing project containers or checkpoint volume before these checks. The newly created `reprolab_checkpoint_state` volume remains intentionally reserved for future state; it was not deleted. The image, build cache, and normal project network also remain available.
- macOS/Windows caveat: SQLite state belongs in Docker's named volume, not in bind-mounted source or `runs/`, to avoid the project's documented locking/performance caveat. S04 reserves storage only; it creates no SQLite database or checkpointer implementation.
- User decision: “I approve S04 — Docker Compose Setup” and separately authorized finalizing, committing, and pushing S04 with `build: add one-service Compose development setup`. Individual personal commands were not supplied and are not inferred.
- Commit scope: `compose.yaml`, the Dockerfile permissions change, README, and this progress record. The resulting SHA and verified remote outcome are reported in the handoff; no follow-up commit is created merely to record its own hash.
- The user separately authorized S05 acquisition/provenance after this push, with no model training, S05 commit/push, or S06 work. S05 results still require human review and explicit approval.

### Entry template for approved steps

```text
Step: Sxx [concept|mechanical]
Changed: paths intentionally updated
Commands I personally ran: ...
Observed results: ...
Checks passed/failed: ...
Understanding check or explanation: ...
Open uncertainties/deviations: ...
Temporary cleanup checked: ...
Decision: APPROVED / BLOCKED / SKIPPED BY EXPLICIT EXCEPTION
Approved by human on: YYYY-MM-DD
Commit hash and pushed remote: (when available; can be recorded next step)
```

## Exception log

No exceptions approved. If the human authorizes combining mechanical steps, skipping a hosted LangSmith step, or replacing a blocked paper, record the reason, impacted tests, alternative verification, and explicit human approval here.

## Evaluation targets (not achieved results)

- 5 human-labelled papers/excerpts before trusting extraction generalization; reuse P01 labels from `docs/p01_ground_truth.md` without passing any `docs/` files to the extractor.
- Track correct/incorrect extracted fields, grounded evidence, missing-field honesty, and run-to-run variability (3 repeated model calls on a fixed excerpt).
- **Zero false `REPRODUCED` claims** on the named incompatible-protocol and prompt-injection test suite.
- Measure real observed LLM spend, retries, experiment runtime, and blocked/inconclusive outcomes.
