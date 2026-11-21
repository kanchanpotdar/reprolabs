# P01 ground truth — S00 paper feasibility spike

Reviewed: **2026-11-21 (Asia/Kolkata)**. S00 candidate approval: **APPROVED CONDITIONAL by the user on 2026-11-21**, explicitly retaining the unresolved seed and Linear Regression settings. Individual field-by-field manual checks were not separately reported.

**Feasibility verdict: CONDITIONAL.** Retain Yeh/UCI + Linear Regression as a feasible first candidate, subject to human review of the conditions below. Public paper, data, and author source are obtainable; all five target claims and their metric definitions are identifiable. However, the paper and notebook disagree about Linear Regression selection, and the paper's global seed statement does not establish the holdout seed. The notebook explicitly uses 123 for that split. These gaps prevent a matched-reproduction claim at this stage.

Execution: **NOT_RUN**. Scientific result: **INCONCLUSIVE** because no model experiment was performed. No experiment classification is assigned yet. This annotation is a human-review answer key, not evidence of automated extraction or reproduction. Future extraction code and its model/tool scope must not read `docs/`, including this file.

## 1. Sources and pinned identity

All sources below were accessed on 2026-11-21. Page numbers refer to the printed, one-based pages of the 33-page PDF identified by the hash below. Notebook cell numbers count **all cells**, including Markdown, from 1; cell IDs provide stable secondary pointers.

| ID | Source | Evidence / version |
|---|---|---|
| P | [Publisher article](https://www.mdpi.com/2076-3417/15/23/12383), [DOI](https://doi.org/10.3390/app152312383) | Olvera-Mayorga et al., *AI-Based Inference System for Concrete Compressive Strength: Multi-Dataset Analysis of Optimized Machine Learning Algorithms*. *Applied Sciences* **2025, 15(23), 12383**; publication date **21 November 2025**, p. 1. CC BY 4.0. |
| PDF | [Publisher-hosted PDF inspected](https://mdpi-res.com/d_attachment/applsci/applsci-15-12383/article_deploy/applsci-15-12383.pdf) | Downloaded successfully: 11,091,081 bytes, 33 pages. SHA-256 `d28d5c35a01f86858642ba61838599555c756e8920628593f49fc6b25abf2f7f`. Relevant claims agree with the publisher HTML checked in this review. |
| V | [Publisher version notes](https://www.mdpi.com/2076-3417/15/23/12383/notes) | Search-indexed publisher notes list an updated PDF version of record at **24 November 2025 09:02 CET**, and HTML update at 09:04. Direct notes access returned HTTP 429; the article's `/pdf` route returned 403. The CDN PDF above was accessible. **Do not assume its hash identifies the latest canonical version of record** without a manual comparison. Its embedded modification date is 21 November 2025, which alone does not establish its publication version. |
| D | [Official UCI dataset 165](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength), [dataset DOI](https://doi.org/10.24432/C5PK67), [official download](https://archive.ics.uci.edu/static/public/165/concrete%2Bcompressive%2Bstrength.zip) | I-Cheng Yeh (1998), *Concrete Compressive Strength*. UCI lists donation date 2007-08-02 and **CC BY 4.0**. No immutable dataset release/version number was established; identify the retrieved bytes by hash. |
| R | [Author repository at inspected commit](https://github.com/1carloso1/ai-inference-system-concrete-strength/tree/ac5aece7961095d802c06199d73a65d541ba10a5) | The paper's Data Availability Statement, p. 29, explicitly links this repository. Default branch `main` resolved to **`ac5aece7961095d802c06199d73a65d541ba10a5`**, committer timestamp **2025-11-25T18:41:25Z**. This postdates publication; it is not proof of the exact source used to generate the tables. |
| N | [Notebook at pinned commit](https://github.com/1carloso1/ai-inference-system-concrete-strength/blob/ac5aece7961095d802c06199d73a65d541ba10a5/notebooks/AI_Based_Inference_System_for_Concrete_Compressive_Strength_Multi_dataset_Analysis_of_Optimized_Machine_Learning_Algorithms.ipynb) | Git blob `6001470ae50e13d230386e3dad726f13edd022b3`, 284,988 bytes. Parsed as JSON and read statically; **not executed**. 264 total cells, 168 code cells, **zero cells with saved outputs**. |
| E | [README](https://github.com/1carloso1/ai-inference-system-concrete-strength/blob/ac5aece7961095d802c06199d73a65d541ba10a5/README.md), [requirements](https://github.com/1carloso1/ai-inference-system-concrete-strength/blob/ac5aece7961095d802c06199d73a65d541ba10a5/requirements.txt) | Environment declarations, not an independently verified execution environment. GitHub metadata returns `license: null`; the inspected repository tree has no license file. Public accessibility does not establish permission to redistribute author code. |

No large paper passages or author code are copied here. The paper and dataset identify CC BY 4.0 licenses; retain their attribution. Repository licensing remains separate.

## 2. Dataset identity and provenance

The target is **Dataset 1 (Yeh)** in P §2.2.1, p. 6 / Table 2, and §3.1 / Table 6, p. 17. It is **not** Dataset 2 (Ke–Qiu, 1,618 cleaned rows) or Dataset 3 (Biswal, 185 cleaned rows).

| Field | Value | Annotation status and evidence |
|---|---|---|
| Task / target | Regression to concrete compressive strength, MPa | `reported`: P §2.2.1 / Table 2; D metadata. |
| Raw observations / predictors | 1,030 rows; eight predictors and one target | `reported`: D; P §2.2.1. Not independently recounted from workbook cells in S00. |
| Ordered predictors in author code | `cement`, `slag`, `flyash`, `water`, `superplasticizer`, `coarseaggregate`, `fineaggregate`, `age` | `reported` in N cell 26 (`G6ZnmosMcWnN`): positional renaming of the nine workbook columns. The first seven represent ingredient mass in kg/m³; age is in days. D supplies the original variable order/units. |
| Target column in author code | `csMPa` | `reported` in N cells 26 and 63 (`yeb0VstlVnhD`); the ninth workbook column. |
| Missing values | None according to UCI | `reported`: D. Not independently scanned in S00. |
| Workbook loaded by author | `Concrete_Data.xls` | `reported`: N cell 10 (`kYoaEi6Bapu1`), loaded by a relative filename. Repository stores it under `data/`; execution would need an explicit path arrangement. |

Both the UCI ZIP and [author workbook at the pinned commit](https://github.com/1carloso1/ai-inference-system-concrete-strength/blob/ac5aece7961095d802c06199d73a65d541ba10a5/data/Concrete_Data.xls) were downloaded into temporary storage. The following are **observed byte checks**, not paper claims:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| UCI ZIP | 34,444 | `dad85d14de8aee4e07479daa774e6b569a313715b71a3b92c95a07cf91c2c9a7` |
| UCI ZIP member `Concrete_Data.xls` | 124,928 | `710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4` |
| Author `data/Concrete_Data.xls` | 124,928 | `710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4` |

The two workbook byte sequences were compared directly and are **identical**. Author workbook Git blob: `707ccac2bbe7a939a42b0aeabee1971ecc6f9115`. This verifies present source-file identity, not the paper's historical split membership. UCI's ZIP also contains `Concrete_Readme.txt`. No workbook rows were modified, no spreadsheet reader was installed, and no model was trained.

## 3. Table 6 target claims

**P §3.1 / Table 6, p. 17**, first model row, Dataset 1 (Yeh, cleaned n = 1,005). Confirmed against HTML and a rendered PDF page. These are **published claims**, not locally observed scores.

| Metric | Published value | Unit / representation | Status |
|---|---:|---|---|
| RMSE | **9.68** | MPa | `reported` |
| MAE | **7.59** | MPa | `reported` |
| MAPE | **30.72** | percent, not fraction 0.3072 | `reported` |
| R² | **0.618** | dimensionless, not percent | `reported` |
| nRMSE | **61.81** | percent, not fraction 0.6181 | `reported` |

P §3.1, p. 17, says the results are evaluated on the **30% held-out test subset**, not averaged cross-validation metrics. The caption's n = 1,005 describes the cleaned dataset, not the test sample count. No numerical acceptance tolerance is proposed or approved in S00; rounded display precision alone is not a scientific reproduction criterion.

### Metric definitions and code agreement

For test observations `y_i`, predictions `yhat_i`, and test-set mean `ybar`:

| Metric | Paper definition and location | Author implementation / remaining limit |
|---|---|---|
| RMSE | `sqrt(sum((y_i - yhat_i)^2) / n)`, Eq. (8), p. 9 | N cell 128 (`YfxyB4jD5_nZ`) takes the square root of `mean_squared_error(y_test, y_pred)`. Agrees. |
| MAE | `sum(abs(y_i - yhat_i)) / n`, Eq. (9), p. 9 | N cell 128 uses `mean_absolute_error`. Agrees. |
| MAPE (%) | `100/n * sum(abs((y_i - yhat_i) / y_i))`, Eq. (10), p. 9; prose on p. 10 excludes zero targets | N cell 127 (`eolGr8c7ZhHp`) masks zero `y_true` and averages over retained terms, then multiplies by 100. The equation does not explicitly redefine n after exclusion; the code does. P §2.2.1 reports a strictly positive Yeh target range, 2.33–82.6 MPa, so zero exclusion should not affect this candidate, subject to later data validation. Near-zero nonzero values are not excluded by the code. |
| R² | `1 - sum((y_i - yhat_i)^2) / sum((y_i - ybar)^2)`, Eq. (11), p. 9 | N cell 128 uses `r2_score(y_test, y_pred)`. Agrees for a nonconstant target. |
| nRMSE (%) | `100 * RMSE / sigma(y_test)`, Eq. (12) and explanatory prose, p. 10 | N cell 126 (`KXOdY_BbImQk`) explicitly uses population standard deviation, `ddof=0`. Cell 143 (`XlAEAtd39JBW`) requests `normalizer='std'`, `nrmse_as_pct=True`. The paper specifies test standard deviation but does **not explicitly specify ddof**. Thus ddof=0 is verified code behavior, not an explicit paper setting. |

Do not substitute target mean, range, IQR, training-target dispersion, or whole-dataset dispersion for the nRMSE denominator. N supports alternative normalizers, but the LR evaluation call selects test standard deviation and percentage output. N returns NaN for a nonpositive denominator; no such degenerate case was tested here.

**Derived consistency check:** with population normalization, `nRMSE(%) = 100 * sqrt(1 - R²)` for the same observations. Using the rounded 0.618 gives **61.8061%**, consistent with 61.81%. The rounded RMSE/nRMSE pair implies test-target standard deviation approximately **15.6609 MPa**. These arithmetic checks support internal compatibility; they do not identify the actual split or establish reproduction.

## 4. Experimental protocol: paper versus code

| Field | Paper evidence | Pinned notebook evidence | Ground-truth treatment |
|---|---|---|---|
| Duplicate removal | §2.2.1 p. 6 and §2.5 pp. 10–11: remove 25 duplicates, 1,030 → 1,005; subsequent analysis uses cleaned data | Cell 31 (`2F6f0MpCVKf1`) calls `dataset1.drop_duplicates(inplace=True)` before X/y creation and split | Count `reported`; exact code policy verified statically: all nine columns including target, first occurrence retained, original order/index retained. These are pandas defaults, not separately specified by the paper. No feature-only deduplication. |
| Outliers / target transformation | §2.5 pp. 10–11: retain extreme but plausible observations; no trimming/winsorization; no log/square-root/Box–Cox target transform | Reviewed Yeh path loads, renames, deduplicates, separates X/y, and splits without such transformations | `reported`, consistent with inspected code path. No physical plausibility audit performed. |
| Train/test allocation | §2.5 p. 11: 70% training / 30% testing | Cell 68 (`nENwrrqKeXtd`): `train_test_split(X1, y1, test_size=0.3, random_state=123)` | Fraction verified in both. **703 train / 302 test is derived**, conditional on 1,005 rows and sklearn split rounding; counts and membership not executed/observed. |
| Global / CV seed | §2.6 pp. 13–14: shuffled K-fold CV with seed 42; p. 14 states a common seed 42 for all algorithms | Cell 131 (`S1KBVhp6Ii4T`) explicitly defines shuffled 5-fold and 3-fold KFold with seed 42; LR search in cell 136 uses 42 | Global statement `reported`; CV/search seed verified in code. There is no estimator RNG parameter to set for ordinary sklearn LinearRegression. |
| Holdout RNG seed | No explicit split call or holdout-specific seed in the reviewed paper statements | **123**, explicitly passed in cell 68; also used for the other datasets' holdouts | Paper/Table 6 holdout seed: **`null`, `not_reported`**. Code value 123 is verified; applying global 42 to the holdout would be an inference contradicted by this code. Do not assert that Table 6 used either seed without further evidence. |
| Split ordering / shuffle / stratification | Raw row ordering and split indices not supplied; shuffle and stratification not explicitly stated for holdout | Workbook load order → all-row deduplication → X/y → split. No intervening row sort in inspected Yeh path. `shuffle` and `stratify` omitted | Code behavior is derived from sklearn 1.6.1 defaults: shuffled, unstratified. Exact historical split membership/order remains unknown. |
| LR scaling | §2.5 pp. 13–14: LR evaluated unscaled | Cells 134–143 select/evaluate the unscaled branch; cell 144 evaluates an auxiliary scaled branch without appending it to the main results dictionary | Main code branch agrees with unscaled evaluation. A train-only scaler in cell 72 is used for the auxiliary comparison; its existence alone is not evidence of test leakage in the main LR branch. |
| LR estimator / selection | §2.6.8 p. 15: standard, unregularized Linear Regression baseline | Cell 135 constructs `LinearRegression()`, but cell 134 (`Vf0WyTeAh8pM`) searches `fit_intercept` and `positive`, each over True/False; cell 136 (`Ceij9ZPiiJiF`) performs CV search; cells 138–139 retain its best estimator | **`conflicting`** protocol description. The selected `fit_intercept` and `positive` for the published row are **`null`**. No saved outputs establish the winning combination. A default constructor does not prove default final settings. |
| LR tuning implementation | Generic §2.6 describes 50 random configurations / 5-fold CV, but §2.6.8 calls LR standard baseline | Cell 136 sets `n_iter=50`, shuffled 5-fold CV, negative MSE scoring, seed 42, `n_jobs=-1`; best estimator is refitted by sklearn's default `refit=True` | Code verified statically. There are only **four distinct LR combinations**; n_iter=50 does not establish 50 distinct LR trials. A finite-grid warning is expected if run under the stated library version; it was not observed in S00. |

Library interpretation sources: [pandas 2.2 drop_duplicates defaults](https://pandas.pydata.org/pandas-docs/version/2.2/reference/api/pandas.DataFrame.drop_duplicates.html), [sklearn 1.6.1 split defaults](https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.train_test_split.html), [RandomizedSearchCV](https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.RandomizedSearchCV.html), and [LinearRegression](https://scikit-learn.org/1.6/modules/generated/sklearn.linear_model.LinearRegression.html). The pandas 2.2 documentation is served as 2.2.3; the author declares 2.2.2. No library was installed or executed to test these interpretations.

The sklearn 1.6.1 constructor defaults are `fit_intercept=True`, `copy_X=True`, `n_jobs=None`, `positive=False`. They describe the initial object and a possible independently approved baseline, **not verified final paper settings**. In particular, `positive=True` changes the fitting constraint. No sample weights are passed in the reviewed LR fit call.

The paper's scale-sensitive-model pipeline statements also have direct code support: N cells 160–161 (SVR), 172–173 (MLP), 184–185 (KNN) place StandardScaler inside the pipeline used by CV. This limited inspection does not constitute an audit of all models or their results.

### Environment evidence

P §2.8 p. 17 / Data Availability p. 29 and E declare Google Colab, Python **3.12.12**, sklearn **1.6.1**, NumPy **2.0.2**, pandas **2.2.2**, Matplotlib **3.10.0**, seaborn **0.13.2**, XGBoost **3.1.1**, LightGBM **4.6.0**, CatBoost **1.2.8**. E additionally pins SciPy **1.16.3**.

This is a declared environment, not a lockfile or installed-environment capture. The version-printing notebook cell has no stored output. `requirements.txt` also contains `python==3.12.12` as if the interpreter were a pip package; interpreter installation must be managed separately. `ipywidgets` and `IPython` are unpinned, and an Excel `.xls` reader such as `xlrd` is not declared. The notebook includes an unpinned `pip install catboost` cell. No dependency installation was attempted, so this review does not claim that the supplied requirements install successfully or fully reconstruct Colab.

## 5. Internal inconsistencies and their significance

| Observation | Evidence | Assessment |
|---|---|---|
| 1,030 raw versus 1,005 cleaned rows | Table 1 p. 4 / §2.2.1 p. 6 versus §2.5 pp. 10–11 / Table 6 p. 17 | **Explainable preprocessing difference**: 25 duplicates removed. Table 1's raw count does not independently demonstrate a different experiment. |
| Table 1 versus Table 6 best Yeh results | Table 1 p. 4, “This work”: RMSE **3.48**, MAE **2.54**, MAPE **8.61%**, R² **0.950**. Table 6 p. 17, CatBoost: RMSE **3.71**, MAE **2.74**, MAPE **9.85%**, R² **0.944**, nRMSE **23.69%** | **Unresolved result inconsistency**. Table 1 lists all models and does not explicitly attach its metric tuple to CatBoost; calling it a verified CatBoost result would overstate the evidence. The tuple differs from Table 6's identified best-RMSE model. Raw/cleaned data or an earlier run could explain it, but no source mapping establishes that explanation. Do not merge the tuples. |
| 3.49 versus 3.71 MPa | §2.5 p. 12 lists best test RMSE **3.49** for Yeh; Tables 5–6 p. 17 and §3.1 p. 18 give **3.71** | **Genuine numerical disagreement in the reported best test result**; too large to explain by the displayed rounding. Historical run/version cause unknown. This does not alter the separately transcribed LR row. P. 12 also gives **3.76** for Biswal versus **3.83** in Table 5 p. 17 / Table 8 p. 18; same unresolved issue, outside the target experiment. |
| Correlation threshold | §3.4 p. 24: Spearman **0.88, 0.93, 0.74**, with ρ > 0.7. Conclusions p. 28: coefficients ρ > **0.8** | **Contradiction in the universal threshold**: 0.74 does not exceed 0.8. It concerns ranking stability, not the LR test metrics. |
| Global 42 versus split 123 | §2.6 p. 14 versus N cell 68 | **Scope ambiguity plus paper/code divergence**. A common algorithm seed need not govern a separate holdout split. Preserve the explicit 42 statement and explicit code 123 separately; the historical paper split is unresolved. |
| Standard LR versus searched constraints | §2.6.8 p. 15 versus N cells 134–139 | **Material paper/code protocol conflict**. The reported scores alone cannot reveal which intercept/positivity setting won. |
| Coefficients under scaling | §2.5 p. 13 says standardization does not change model coefficients or prediction metrics | **Overstated coefficient claim**. For unregularized OLS with an intercept, equivalent predictions can be obtained after feature scaling, but coefficients expressed in scaled coordinates generally change. This does not prove the scores are wrong; it also cannot justify ignoring the notebook's intercept/positivity search. |

The Table 6 LR R²/nRMSE pair passes the arithmetic consistency check in §3. None of the conflicts above justifies editing the paper claims to make a future run agree.

## 6. Conditions for retaining the candidate

The candidate is practical for a small, local CPU experiment: public tabular data, eight inputs, and a supported sklearn estimator. No GPU, paid LLM call, or author-notebook execution is needed to establish a later independent baseline. S00 makes **no runtime, accuracy, or installation-success claim**.

Before treating a later experiment as matched, resolve or explicitly disclose:

1. **Paper source version:** compare the current canonical publisher PDF with the hash and cited pages here. If it differs, reconcile the target claims and protocol evidence first.
2. **Holdout provenance:** obtain evidence tying Table 6 to a seed, workbook order, deduplication rule, and split membership. Notebook seed 123 is usable only as a disclosed code-derived choice until that tie is verified. Seed 42 is not automatically the holdout seed.
3. **LR settings:** establish whether Table 6 used default OLS or the searched best estimator, including final `fit_intercept` and `positive`. Do not silently select one interpretation or search seeds/settings against test metrics.
4. **Approved implementation and environment:** decide the experiment's scope and disclose defaults/deviations, including ddof=0 if adopted from code. A simple default OLS run under unresolved protocol differences must remain an explicitly scoped independent baseline with an inconclusive paper-reproduction verdict.

The best next evidence would be a publication-linked run record or author clarification identifying the Table 6 split and LR best parameters. No author contact was made. If exact historical reproducibility is mandatory and these facts cannot be established, the human should explicitly choose whether to switch benchmark candidates. **No alternate paper is selected and no next step is authorized by this document.**

Failure example: a future run happens to obtain RMSE 9.68 after assuming split seed 42. Without compatible split/settings and metric populations, that numerical match cannot support `REPRODUCED`.

## 7. Verification performed and manual approval checklist

### Checks actually performed

- Read `AGENTS.md`, `docs/progress.md`, and only roadmap S00; no later roadmap step was read or implemented.
- Opened official paper HTML, UCI metadata/license, and the paper-linked GitHub repository. Pinned the author commit and inspected the notebook JSON, requirements, and README without executing author code.
- Retrieved the publisher CDN PDF and the small UCI/author data files into an owned `/tmp/reprolab-s00-*` directory using bounded downloads. Calculated SHA-256 hashes, enumerated ZIP members, and directly compared workbook bytes.
- Used the existing bundled PDF reader and renderer. Extracted relevant page text; visually inspected rendered pages **4, 17, 24, and 28**, including all five LR metrics and the two conflicting ranking statements. Formula and preprocessing locations were checked in text. A first PDF extraction attempt could not import PyMuPDF; the existing pypdf/Poppler tools supplied the needed evidence without installation.
- Calculated the two rounded-metric arithmetic checks in §3. No train/test split, workbook row-count validation, fit, CV search, unit test, Docker check, or application test was run. This is a feasibility/source review.
- Only this documentation file is intentionally added. Temporary downloads and page renders are removed after review; no paper/data copies, `inputs/`, `runs/`, project dependencies, or application files are retained by S00.

### Human source checks — individual completion not reported

The user approved the CONDITIONAL candidate decision. Unchecked source-verification items below remain available for review; their individual completion is not inferred from that approval.

- [ ] Open the publisher paper and visually confirm **Table 6 p. 17**: 9.68 MPa, 7.59 MPa, 30.72%, 0.618, 61.81%. Confirm Dataset 1/Yeh and the test-subset statement immediately above it.
- [ ] Compare **Eqs. (8)–(12), pp. 9–10**, particularly MAPE's zero policy and nRMSE's **test** standard deviation. Confirm that ddof=0 is code evidence, not explicit paper text.
- [ ] Read duplicate removal on **pp. 6 and 10–11**, holdout allocation on **p. 11**, seed wording on **pp. 13–14**, and LR baseline wording on **p. 15**. In the pinned notebook find cell IDs `nENwrrqKeXtd` (split 123), `S1KBVhp6Ii4T` (CV 42), and `Vf0WyTeAh8pM` (LR search).
- [ ] Compare Table 1 **p. 4**, best-error prose **p. 12**, Tables 5–6 **p. 17**, and ranking prose **pp. 24/28**. Confirm the distinction between an explained row-count change and unresolved result conflicts.
- [ ] Open official UCI metadata, check **CC BY 4.0** and attribution, and confirm that its download provides `Concrete_Data.xls`. For an independent byte check, download into your own temporary folder and run `shasum -a 256` on the ZIP and extracted workbook; expect the hashes in §2. Avoid resaving the workbook before hashing it.
- [ ] Check the current canonical PDF and publisher version notes; establish whether the inspected CDN PDF is the version you approve. The source URLs and retrieval hashes here are not a claim that all publisher versions are identical.
- [x] Candidate decision: the user explicitly approved **S00 as CONDITIONAL** on 2026-11-21, with the unresolved seed and Linear Regression settings documented. This accepts a feasible candidate and its unresolved evidence, not an exact reproduction. The user separately requested S01.

Understanding prompts for review:

1. Why can a CV seed of 42 and a holdout seed of 123 coexist, and what still prevents claiming that 123 produced Table 6?
2. Why is `LinearRegression()` at construction insufficient evidence that the final estimator kept default settings?
3. Why would matching RMSE alone fail to demonstrate reproduction?

Approval record: **S00 APPROVED CONDITIONAL by the user, 2026-11-21 (Asia/Kolkata)**. The user explicitly accepted the unresolved seed and Linear Regression settings; no individual manual commands or source checks were reported. `docs/progress.md` records the decision. The user subsequently approved S01 subject to its checks passing and separately authorized including this S00 evidence in the combined initial S00 + S01 commit and push. The commit SHA and push verification are reported in the handoff. S02 implementation still requires separate approval.
