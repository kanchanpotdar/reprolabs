"""Strict evidence and development-manifest contracts; no file I/O or execution.

Only SourceObservations (and reusable SourceFact types) belong in future extraction
prompts. The fixture and locked execution profile contain human reference values.
Content locking identifies a configuration; it grants no permission to execute it.
"""

import hashlib
import json
from typing import Annotated, Generic, Literal, TypeVar
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    StringConstraints,
    model_validator,
)

from reprolab.experiment import CONCRETE_COLUMNS, CONCRETE_SHA256

Text = Annotated[StrictStr, StringConstraints(min_length=1, pattern=r"\S")]
SHA256 = Annotated[
    StrictStr, StringConstraints(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
]
Revision = Annotated[
    StrictStr, StringConstraints(min_length=40, max_length=40, pattern=r"^[0-9a-f]{40}$")
]
Seed = Annotated[StrictInt, Field(ge=0, lt=2**32)]
Origin = Literal[
    "paper_reported", "author_code_derived", "human_selected", "dataset_source", "runtime_observed"
]
Status = Literal["reported", "derived", "inferred", "not_reported", "conflicting"]
T = TypeVar("T")


class FrozenModel(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        validate_default=True,
        allow_inf_nan=False,
        revalidate_instances="always",
    )


def _https(reference: str) -> None:
    parsed = urlsplit(reference)
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Source URL has an invalid port") from exc
    if parsed.scheme != "https" or not parsed.hostname or any(c.isspace() for c in reference):
        raise ValueError("Source references must be nonblank HTTPS URLs")


class Evidence(FrozenModel):
    kind: Literal["paper", "author_code", "dataset", "human", "runtime"]
    reference: Text
    location: Text
    revision: Revision | None

    @model_validator(mode="after")
    def check_reference(self):
        if self.kind in {"human", "runtime"}:
            if (
                not self.reference.startswith(self.kind + ":")
                or not self.reference[len(self.kind) + 1 :].strip()
            ):
                raise ValueError(
                    "Human/runtime evidence must use an explicit decision/check reference"
                )
        else:
            _https(self.reference)
        if self.kind == "author_code" and self.revision is None:
            raise ValueError("Author-code evidence requires a pinned commit revision")
        if self.kind != "author_code" and self.revision is not None:
            raise ValueError("Commit revisions belong only to author-code evidence")
        return self


class SourceEvidence(Evidence):
    """An extractor cannot mint human decisions or runtime verification records."""

    kind: Literal["paper", "author_code"]


class Fact(FrozenModel, Generic[T]):
    value: T | None
    origin: Origin | None
    status: Status
    evidence: Annotated[tuple[Evidence, ...], Field(min_length=1)]
    explanation: Text | None

    @model_validator(mode="after")
    def check_provenance(self):
        if self.status in {"not_reported", "conflicting"}:
            if self.value is not None or self.origin is not None or self.explanation is None:
                raise ValueError("Unresolved facts need null value/origin and an explanation")
            if self.status == "conflicting" and len(set(self.evidence)) < 2:
                raise ValueError("Conflicting facts require distinct evidence pointers")
        elif self.status == "inferred":
            if self.value is None or self.origin is not None or self.explanation is None:
                raise ValueError(
                    "An inference needs a candidate value/reason, not a claimed source origin"
                )
        else:
            if self.value is None or self.origin is None:
                raise ValueError("Known facts require a value and origin")
            required_kind = {
                "paper_reported": "paper",
                "author_code_derived": "author_code",
                "human_selected": "human",
                "dataset_source": "dataset",
                "runtime_observed": "runtime",
            }[self.origin]
            if not any(e.kind == required_kind for e in self.evidence):
                raise ValueError("Fact origin contradicts its evidence kinds")
            derived = self.origin in {"author_code_derived", "runtime_observed"}
            if self.status != ("derived" if derived else "reported"):
                raise ValueError("Fact status contradicts its provenance")
            if self.origin == "human_selected" and not self.explanation:
                raise ValueError("Human selections require an explanation")
        return self


class SourceFact(Fact[T], Generic[T]):
    origin: Literal["paper_reported", "author_code_derived"] | None
    evidence: Annotated[tuple[SourceEvidence, ...], Field(min_length=1)]


class SourceObservations(FrozenModel):
    """Generic source-only observations: no P01 values, defaults, or approval flags.

    Future extraction can reuse SourceFact for additional observed fields. Export
    this schema, never LockedManifest's schema or the development fixture.
    """

    common_or_cv_seed: SourceFact[Seed]
    holdout_seed: SourceFact[Seed]
    final_fit_intercept: SourceFact[StrictBool]
    final_positive: SourceFact[StrictBool]
    final_copy_X: SourceFact[StrictBool]
    final_n_jobs: SourceFact[StrictInt]
    nrmse_ddof: SourceFact[Annotated[StrictInt, Field(ge=0)]]


def _resolved(*facts: Fact) -> None:
    if any(f.value is None or f.status not in {"reported", "derived"} for f in facts):
        raise ValueError("Execution settings must be explicit and resolved; no inferred defaults")


class Paper(FrozenModel):
    title: Text
    doi: Annotated[StrictStr, StringConstraints(pattern=r"^10\.\d{4,9}/\S+$")]
    article_url: Text
    pdf_url: Text
    exact_pdf_sha256: Fact[SHA256]
    evidence: Annotated[tuple[SourceEvidence, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def check_paper(self):
        _https(self.article_url)
        _https(self.pdf_url)
        if not any(e.kind == "paper" for e in self.evidence):
            raise ValueError("Paper identity requires paper evidence")
        if self.exact_pdf_sha256.value is not None:
            if self.exact_pdf_sha256.origin != "runtime_observed":
                raise ValueError("An exact PDF hash must come from verified artifact bytes")
            _resolved(self.exact_pdf_sha256)
        return self


class Column(FrozenModel):
    name: Text
    role: Literal["feature", "target"]
    unit: Literal["kg/m^3", "day", "MPa"]


class Dataset(FrozenModel):
    uci_id: StrictInt
    source_url: Text
    download_url: Text
    archive_member: Literal["Concrete_Data.xls"]
    format: Literal["xls"]
    sheet: Literal["Sheet1"]
    sha256: Fact[SHA256]
    raw_rows: StrictInt
    columns: tuple[Column, ...]
    schema_origin: Literal["dataset_source"]
    evidence: Annotated[tuple[Evidence, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def check_profile(self):
        _https(self.source_url)
        _https(self.download_url)
        _resolved(self.sha256)
        if self.uci_id != 165 or self.raw_rows != 1030 or self.sha256.value != CONCRETE_SHA256:
            raise ValueError(
                "Dataset identity/checksum/count is incompatible with the approved loader"
            )
        if not any(e.kind == "dataset" for e in self.evidence):
            raise ValueError("Dataset schema needs official dataset evidence")
        expected = tuple(
            (
                name,
                "feature" if i < 8 else "target",
                "kg/m^3" if i < 7 else "day" if i == 7 else "MPa",
            )
            for i, name in enumerate(CONCRETE_COLUMNS)
        )
        if tuple((c.name, c.role, c.unit) for c in self.columns) != expected:
            raise ValueError("Ordered columns, roles, and units must match the approved XLS schema")
        return self


class Preprocessing(FrozenModel):
    deduplicate: Fact[StrictBool]
    duplicate_key: Fact[Literal["all_columns"]]
    keep: Fact[Literal["first"]]
    order: Fact[Literal["preserve"]]
    scaling: Fact[Literal["none"]]
    target_transform: Fact[Literal["none"]]
    expected_rows: StrictInt

    @model_validator(mode="after")
    def check_profile(self):
        _resolved(
            self.deduplicate,
            self.duplicate_key,
            self.keep,
            self.order,
            self.scaling,
            self.target_transform,
        )
        if self.deduplicate.value is not True or self.expected_rows != 1005:
            raise ValueError("The current pipeline requires full-row deduplication to 1005 rows")
        return self


class Split(FrozenModel):
    test_fraction: Fact[StrictFloat]
    seed: Fact[Seed]
    shuffle: Fact[StrictBool]
    stratify: Fact[Literal["none"]]

    @model_validator(mode="after")
    def check_profile(self):
        _resolved(self.test_fraction, self.seed, self.shuffle, self.stratify)
        if self.test_fraction.value != 0.30 or self.shuffle.value is not True:
            raise ValueError("The current split supports only shuffled 70/30 allocation")
        return self


class LinearRegressionSpec(FrozenModel):
    name: Literal["sklearn.linear_model.LinearRegression"]
    fit_intercept: Fact[StrictBool]
    positive: Fact[StrictBool]
    copy_X: Fact[StrictBool]
    n_jobs: Fact[StrictInt]

    @model_validator(mode="after")
    def check_settings(self):
        _resolved(self.fit_intercept, self.positive, self.copy_X, self.n_jobs)
        if self.n_jobs.value < 1:
            raise ValueError("Development n_jobs must explicitly bound positive CPU concurrency")
        return self


METRIC_PROTOCOL = {
    "RMSE": ("MPa", "sqrt(mean((y_true-y_pred)**2))"),
    "MAE": ("MPa", "mean(abs(y_true-y_pred))"),
    "MAPE": ("percent", "100*mean(abs((y_true-y_pred)/y_true)) over nonzero y_true"),
    "R2": ("dimensionless", "1-sum((y_true-y_pred)**2)/sum((y_true-mean(y_true))**2)"),
    "nRMSE": ("percent", "100*RMSE/std(y_test)"),
}


class Metric(FrozenModel):
    name: Literal["RMSE", "MAE", "MAPE", "R2", "nRMSE"]
    unit: Literal["MPa", "percent", "dimensionless"]
    population: Literal["test"]
    definition: Fact[StrictStr]
    published_claim: Fact[StrictFloat]
    ddof: Fact[StrictInt] | None
    zero_target_policy: Fact[Literal["exclude_zero_targets"]] | None

    @model_validator(mode="after")
    def check_metric(self):
        _resolved(self.definition, self.published_claim)
        if (self.unit, self.definition.value) != METRIC_PROTOCOL[self.name]:
            raise ValueError("Unsupported metric unit or definition")
        claim = self.published_claim
        if claim.origin != "paper_reported" or claim.status != "reported":
            raise ValueError(
                "Published claims must remain paper-reported, separate from run results"
            )
        if (self.name != "R2" and claim.value < 0) or (self.name == "R2" and claim.value > 1):
            raise ValueError("Published metric value is outside its mathematical range")
        if self.name == "nRMSE":
            if self.ddof is None:
                raise ValueError("nRMSE needs an explicit test-standard-deviation ddof")
            _resolved(self.ddof)
            if self.ddof.value != 0:
                raise ValueError("This development metric protocol uses explicit ddof=0")
        elif self.ddof is not None:
            raise ValueError("ddof applies only to nRMSE")
        if self.name == "MAPE":
            if self.zero_target_policy is None:
                raise ValueError("MAPE requires an explicit zero-target policy")
            _resolved(self.zero_target_policy)
        elif self.zero_target_policy is not None:
            raise ValueError("Zero-target policy applies only to MAPE")
        return self


class Environment(FrozenModel):
    python: Literal["3.12.16"]
    uv: Literal["0.13.8"]
    sklearn: Literal["1.6.1"]
    pydantic: Literal["2.14.4"]
    uv_lock_sha256: SHA256


class LockedManifest(FrozenModel):
    schema_version: Annotated[StrictInt, Field(ge=1, le=1)]
    purpose: Literal["development_baseline"]
    paper: Paper
    dataset: Dataset
    research: SourceObservations
    preprocessing: Preprocessing
    split: Split
    model: LinearRegressionSpec
    metrics: tuple[Metric, ...]
    environment: Environment

    @model_validator(mode="after")
    def check_metrics(self):
        names = tuple(m.name for m in self.metrics)
        if len(names) != len(set(names)) or set(names) != set(METRIC_PROTOCOL):
            raise ValueError("Specify each supported evaluation metric exactly once")
        return self


def canonical_json(manifest: LockedManifest) -> str:
    """Validate even copied/constructed instances, then serialize without a self-hash."""
    checked = LockedManifest.model_validate(manifest)
    return json.dumps(
        checked.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def fingerprint(manifest: LockedManifest) -> str:
    return hashlib.sha256(canonical_json(manifest).encode("utf-8")).hexdigest()


def development_manifest(uv_lock_sha256: str) -> LockedManifest:
    """Human-reviewed P01 fixture, never an extraction prompt or approval token.

    The caller supplies the actual lockfile digest. No PDF bytes are read or
    claimed verified here. These model choices do not resolve published settings.
    """
    article = "https://www.mdpi.com/2076-3417/15/23/12383"
    pdf = "https://mdpi-res.com/d_attachment/applsci/applsci-15-12383/article_deploy/applsci-15-12383.pdf"
    revision = "ac5aece7961095d802c06199d73a65d541ba10a5"
    notebook = (
        "https://github.com/1carloso1/ai-inference-system-concrete-strength/blob/"
        + revision
        + "/notebooks/AI_Based_Inference_System_for_Concrete_Compressive_Strength_"
        "Multi_dataset_Analysis_of_Optimized_Machine_Learning_Algorithms.ipynb"
    )

    def paper(location):
        return SourceEvidence(kind="paper", reference=article, location=location, revision=None)

    def code(location):
        return SourceEvidence(
            kind="author_code", reference=notebook, location=location, revision=revision
        )

    human = Evidence(
        kind="human",
        reference="human:S08-2026-11-22",
        location="User explicitly selected the development LR configuration; no training authorized",
        revision=None,
    )
    data_source = Evidence(
        kind="dataset",
        reference="https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength",
        location="Variables table, units, 1030 instances; DOI 10.24432/C5PK67",
        revision=None,
    )
    data_check = Evidence(
        kind="runtime",
        reference="runtime:S05-2026-11-22",
        location="Official raw XLS SHA-256 independently checked in S00/S05 and S06/S07 verification",
        revision=None,
    )

    def fact(value, origin, *evidence, explanation=None):
        return dict(
            value=value,
            origin=origin,
            status="derived"
            if origin in {"author_code_derived", "runtime_observed"}
            else "reported",
            evidence=tuple(evidence),
            explanation=explanation,
        )

    def unknown(*evidence, explanation, status="not_reported"):
        return dict(
            value=None,
            origin=None,
            status=status,
            evidence=tuple(evidence),
            explanation=explanation,
        )

    source_split = code(
        "Cell 68, nENwrrqKeXtd: test_size=0.3, random_state=123; sklearn 1.6.1 defaults"
    )
    lr_paper = paper("Section 2.6.8, p. 15: standard LR baseline")
    lr_code = code(
        "Cells 134-139, Vf0WyTeAh8pM: intercept/positive search; no saved winning parameters"
    )

    def selected(value):
        return fact(
            value,
            "human_selected",
            human,
            explanation="Explicit S08 development choice; not verified final paper settings",
        )

    metrics = []
    for name, claim, equation in (
        ("RMSE", 9.68, 8),
        ("MAE", 7.59, 9),
        ("MAPE", 30.72, 10),
        ("R2", 0.618, 11),
        ("nRMSE", 61.81, 12),
    ):
        definition_evidence = paper(f"Equation ({equation}), pp. 9-10")
        # MAPE's retained denominator is explicit code behavior, not added to the paper claim.
        definition_origin = "author_code_derived" if name == "MAPE" else "paper_reported"
        if name == "MAPE":
            definition_evidence = code(
                "Cell 127, eolGr8c7ZhHp: exclude zero targets and average retained terms"
            )
        metrics.append(
            dict(
                name=name,
                unit=METRIC_PROTOCOL[name][0],
                population="test",
                definition=fact(METRIC_PROTOCOL[name][1], definition_origin, definition_evidence),
                published_claim=fact(
                    claim, "paper_reported", paper("Table 6, p. 17, Dataset 1, LR test row")
                ),
                ddof=fact(
                    0, "author_code_derived", code("Cell 126, KXOdY_BbImQk: test std, ddof=0")
                )
                if name == "nRMSE"
                else None,
                zero_target_policy=fact(
                    "exclude_zero_targets", "author_code_derived", definition_evidence
                )
                if name == "MAPE"
                else None,
            )
        )
    return LockedManifest(
        schema_version=1,
        purpose="development_baseline",
        paper=Paper(
            title="AI-Based Inference System for Concrete Compressive Strength: Multi-Dataset Analysis of Optimized Machine Learning Algorithms",
            doi="10.3390/app152312383",
            article_url=article,
            pdf_url=pdf,
            exact_pdf_sha256=unknown(
                human,
                explanation="Exact PDF bytes/version have not been verified for this manifest. S00's historical CDN hash is not promoted to a current verified identity.",
            ),
            evidence=(
                paper(
                    "Article identity and prior S00 review; current canonical PDF version remains unresolved"
                ),
            ),
        ),
        dataset=Dataset(
            uci_id=165,
            source_url=data_source.reference,
            download_url="https://archive.ics.uci.edu/static/public/165/concrete%2Bcompressive%2Bstrength.zip",
            archive_member="Concrete_Data.xls",
            format="xls",
            sheet="Sheet1",
            sha256=fact(CONCRETE_SHA256, "runtime_observed", data_check),
            raw_rows=1030,
            columns=tuple(
                Column(
                    name=name,
                    role="feature" if i < 8 else "target",
                    unit="kg/m^3" if i < 7 else "day" if i == 7 else "MPa",
                )
                for i, name in enumerate(CONCRETE_COLUMNS)
            ),
            schema_origin="dataset_source",
            evidence=(data_source, data_check),
        ),
        research=SourceObservations(
            common_or_cv_seed=fact(
                42,
                "paper_reported",
                paper("Section 2.6, pp. 13-14: global/CV seed, not verified holdout seed"),
            ),
            holdout_seed=unknown(
                paper("Sections 2.5/2.6, pp. 11, 13-14"),
                explanation="No verified Table 6 holdout seed. Global/CV 42 does not identify the holdout; code uses 123.",
            ),
            final_fit_intercept=unknown(
                lr_paper,
                lr_code,
                status="conflicting",
                explanation="Paper baseline description versus code search; final Table 6 value unresolved.",
            ),
            final_positive=unknown(
                lr_paper,
                lr_code,
                status="conflicting",
                explanation="Paper baseline description versus code search; final Table 6 value unresolved.",
            ),
            final_copy_X=unknown(
                lr_paper,
                lr_code,
                explanation="No verified published final copy_X value; constructor defaults are not a final run record.",
            ),
            final_n_jobs=unknown(
                lr_paper,
                lr_code,
                explanation="No verified published estimator n_jobs value; search-worker concurrency is a separate setting.",
            ),
            nrmse_ddof=unknown(
                paper("Equation (12), p. 10"),
                explanation="Test standard deviation is specified, but its ddof is not reported.",
            ),
        ),
        preprocessing=Preprocessing(
            deduplicate=fact(
                True,
                "paper_reported",
                paper("Sections 2.2.1/2.5, pp. 6, 10-11: remove 25 duplicates"),
            ),
            duplicate_key=fact(
                "all_columns",
                "author_code_derived",
                code("Cell 31, 2F6f0MpCVKf1: drop_duplicates, all nine columns"),
            ),
            keep=fact(
                "first",
                "author_code_derived",
                code("Cell 31, 2F6f0MpCVKf1: pandas default keep=first"),
            ),
            order=fact(
                "preserve",
                "author_code_derived",
                code("Cells 26-68: workbook order, first-occurrence deduplication, then split"),
            ),
            scaling=fact(
                "none", "paper_reported", paper("Section 2.5, pp. 13-14: LR evaluated unscaled")
            ),
            target_transform=fact(
                "none",
                "paper_reported",
                paper("Section 2.5, pp. 10-11: raw target, retain plausible extremes"),
            ),
            expected_rows=1005,
        ),
        split=Split(
            test_fraction=fact(0.30, "paper_reported", paper("Section 2.5, p. 11: 70/30 holdout")),
            seed=fact(
                123,
                "author_code_derived",
                source_split,
                human,
                explanation="Human-approved S06/S08 development choice; published holdout remains unknown.",
            ),
            shuffle=fact(True, "author_code_derived", source_split),
            stratify=fact("none", "author_code_derived", source_split),
        ),
        model=LinearRegressionSpec(
            name="sklearn.linear_model.LinearRegression",
            fit_intercept=selected(True),
            positive=selected(False),
            copy_X=selected(True),
            n_jobs=selected(1),
        ),
        metrics=tuple(metrics),
        environment=Environment(
            python="3.12.16",
            uv="0.13.8",
            sklearn="1.6.1",
            pydantic="2.14.4",
            uv_lock_sha256=uv_lock_sha256,
        ),
    )
