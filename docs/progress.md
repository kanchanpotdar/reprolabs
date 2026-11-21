# ReproLab — human-verified progress

- **Current step:** S01 — repository hygiene
- **Current status:** APPROVED; reported S01 checks rerun successfully
- **Next step:** Read and explain S02 only; implementation requires separate approval
- **Approved steps:** S00 — APPROVED (CONDITIONAL); S01 — APPROVED, 2026-11-21
- **Commit/push:** S00 + S01 authorized together; commit SHA and verified push outcome are reported in the handoff

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
