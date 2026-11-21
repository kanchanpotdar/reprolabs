# ReproLab — human-verified progress

- **Current step:** S02 — reproducible Python environment and checks
- **Current status:** APPROVED by the user after reviewing reported checks
- **Next step:** Read and explain S03 only; implementation requires separate approval
- **Approved steps:** S00 — APPROVED (CONDITIONAL); S01 and S02 — APPROVED, 2026-11-21
- **Commit/push:** S00 + S01 pushed as `837a92101d5fbaec82a8c6bf73dc854758355860`; S02 commit/push authorized, with its SHA and verified remote outcome reported in the handoff

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
- S03 scope explanation is requested; implementation remains unauthorized until a separate explicit approval.

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
