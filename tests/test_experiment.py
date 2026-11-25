"""Data/experiment contracts with independent synthetic expectations and scoped I/O."""

import copy
import hashlib
import json
import math
import multiprocessing
import tempfile
import tomllib
from decimal import Decimal, localcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from reprolab import cli, experiment
from reprolab.experiment import (
    ConcreteData,
    evaluate_predictions,
    fit_predict,
    load_concrete,
    remove_duplicates,
    select_features_target,
    split_data,
    validate_concrete,
)

# Synthetic values, not sampled or copied from the UCI dataset.
ROW_A = (300.25, 0.0, 15.5, 180.125, 4.75, 990.5, 780.25, 28.0, 42.125)
ROW_B = (100.75, 1.5, 20.25, 190.5, 3.125, 950.25, 800.5, 7.0, 15.875)
ROW_C = (300.25, 0.0, 15.5, 180.125, 4.75, 990.5, 780.25, 28.0, 99.625)


@pytest.fixture
def headers():
    """Literal source contract, deliberately not imported from production constants."""
    return (
        "Cement (component 1)(kg in a m^3 mixture)",
        "Blast Furnace Slag (component 2)(kg in a m^3 mixture)",
        "Fly Ash (component 3)(kg in a m^3 mixture)",
        "Water  (component 4)(kg in a m^3 mixture)",
        "Superplasticizer (component 5)(kg in a m^3 mixture)",
        "Coarse Aggregate  (component 6)(kg in a m^3 mixture)",
        "Fine Aggregate (component 7)(kg in a m^3 mixture)",
        "Age (day)",
        "Concrete compressive strength(MPa, megapascals) ",
    )


@pytest.fixture
def raw_rows():
    """Only the raw-validator contract needs 1030 rows; no file is generated."""
    return (ROW_A,) * 1030


@pytest.fixture
def duplicate_data():
    """Unsorted values, adjacent/nonadjacent repeats, and nonconsecutive IDs."""
    return ConcreteData((ROW_A, ROW_A, ROW_B, ROW_A, ROW_C, ROW_B), (2, 3, 7, 8, 12, 20))


@pytest.fixture
def feature_data():
    return ConcreteData(
        (
            (13.125, 2.25, 3.5, 4.75, 5.125, 6.25, 7.5, 8.0, 99.125),
            (2.875, 3.25, 4.5, 5.75, 6.125, 7.25, 8.5, 9.0, 27.875),
        ),
        (4, 17),
    )


@pytest.fixture
def split_fixture():
    rows = tuple(
        (i + 0.125, 2.25, 3.5, 4.75, 5.125, 6.25, 7.5, 28.0, i + 100.875) for i in range(10)
    )
    return ConcreteData(rows, (2, 4, 7, 11, 16, 22, 29, 37, 46, 56))


def test_raw_validation_preserves_values_and_assigns_excel_ids(headers, raw_rows):
    data = validate_concrete(headers, raw_rows)
    assert data.rows == raw_rows
    assert len(data.rows) == 1030
    assert data.row_ids == tuple(range(2, 1032))


@pytest.mark.parametrize("change", ["reordered", "missing", "extra", "trailing_space"])
def test_validation_rejects_invalid_headers(headers, raw_rows, change):
    malformed = {
        "reordered": (headers[1], headers[0]) + headers[2:],
        "missing": headers[:-1],
        "extra": headers + ("unexpected",),
        "trailing_space": headers[:-1] + (headers[-1].rstrip(),),
    }[change]
    with pytest.raises(ValueError, match="schema mismatch"):
        validate_concrete(malformed, raw_rows)


@pytest.mark.parametrize("count", [0, 1, 1029, 1031])
def test_validation_rejects_invalid_row_counts(headers, count):
    with pytest.raises(ValueError, match="Expected 1030 raw data rows"):
        validate_concrete(headers, (ROW_A,) * count)


@pytest.mark.parametrize("first_row", [ROW_A[:-1], ROW_A + (0.0,)])
def test_validation_rejects_invalid_column_counts(headers, raw_rows, first_row):
    with pytest.raises(ValueError, match="expected 9 columns"):
        validate_concrete(headers, (first_row,) + raw_rows[1:])


@pytest.mark.parametrize(
    "value", [None, "", "1.0", True, float("nan"), float("inf"), -float("inf")]
)
def test_validation_rejects_incomplete_or_nonnumeric_values(headers, raw_rows, value):
    first_row = (ROW_A[0], value) + ROW_A[2:]
    with pytest.raises(ValueError, match="Excel row 2, column 2: expected a finite number"):
        validate_concrete(headers, (first_row,) + raw_rows[1:])


@pytest.mark.parametrize(
    ("row_ids", "message"),
    [
        ((4, 4), "unique"),
        ((4,), "equal lengths"),
        ((0, 17), "original Excel row numbers"),
        ((1, 17), "original Excel row numbers"),
        ((4, 1032), "original Excel row numbers"),
        ((True, 17), "original Excel row numbers"),
        (("4", 17), "original Excel row numbers"),
        ((4.0, 17), "original Excel row numbers"),
    ],
)
def test_processing_rejects_invalid_identifiers(feature_data, row_ids, message):
    with pytest.raises(ValueError, match=message):
        select_features_target(ConcreteData(feature_data.rows, row_ids))


def test_checksum_failure_precedes_parsing(monkeypatch):
    def unexpected_parser(*args, **kwargs):
        pytest.fail("The parser must not receive bytes with an unapproved checksum")

    monkeypatch.setattr(experiment.xlrd, "open_workbook", unexpected_parser)
    with tempfile.TemporaryDirectory(prefix="reprolab-s07-checksum-", dir="/tmp") as scratch:
        path = Path(scratch) / "synthetic.xls"
        payload = b"unapproved synthetic XLS bytes\n"
        path.write_bytes(payload)
        with pytest.raises(ValueError, match="SHA-256 mismatch"):
            load_concrete(path)
        assert path.read_bytes() == payload
    assert not Path(scratch).exists()


def test_missing_input_fails_explicitly():
    with tempfile.TemporaryDirectory(prefix="reprolab-s07-missing-", dir="/tmp") as scratch:
        with pytest.raises(FileNotFoundError):
            load_concrete(Path(scratch) / "missing.xls")
    assert not Path(scratch).exists()


def test_duplicates_keep_first_occurrences_and_account_for_every_id(duplicate_data):
    before = ConcreteData(duplicate_data.rows, duplicate_data.row_ids)
    cleaned, duplicate_of = remove_duplicates(duplicate_data, expected_rows=3)
    assert cleaned == ConcreteData((ROW_A, ROW_B, ROW_C), (2, 7, 12))
    assert duplicate_of == {3: 2, 8: 2, 20: 7}
    assert set(cleaned.row_ids).isdisjoint(duplicate_of)
    assert set(cleaned.row_ids) | set(duplicate_of) == {2, 3, 7, 8, 12, 20}
    select_features_target(cleaned)
    split_data(cleaned, seed=123)
    assert duplicate_data == before


def test_identical_features_with_different_targets_are_not_duplicates():
    data = ConcreteData((ROW_A, ROW_C), (2, 12))
    assert ROW_A[:8] == ROW_C[:8] and ROW_A[8] != ROW_C[8]
    cleaned, duplicate_of = remove_duplicates(data, expected_rows=2)
    assert cleaned == data
    assert duplicate_of == {}


def test_unexpected_duplicate_count_fails(duplicate_data):
    with pytest.raises(ValueError, match="Expected 4 distinct full rows, got 3"):
        remove_duplicates(duplicate_data, expected_rows=4)


def test_feature_target_values_are_preserved(feature_data):
    features, target = select_features_target(feature_data)
    assert features == (
        (13.125, 2.25, 3.5, 4.75, 5.125, 6.25, 7.5, 8.0),
        (2.875, 3.25, 4.5, 5.75, 6.125, 7.25, 8.5, 9.0),
    )
    assert target == (99.125, 27.875)
    assert feature_data.row_ids == (4, 17)


# Literal memberships reviewed against pinned NumPy's reference permutations.
# Expected IDs are not calculated using the function under test at runtime.
@pytest.mark.parametrize(
    ("seed", "train_ids", "test_ids"),
    [
        (123, (22, 46, 11, 4, 29, 56, 7), (16, 2, 37)),
        (7, (7, 4, 56, 37, 11, 29, 16), (46, 22, 2)),
    ],
)
def test_seeded_split_matches_reviewed_ids_and_repeats(split_fixture, seed, train_ids, test_ids):
    train, test = split_data(split_fixture, seed=seed)
    assert train.row_ids == train_ids
    assert test.row_ids == test_ids
    assert (train, test) == split_data(split_fixture, seed=seed)


def test_split_is_disjoint_complete_and_does_not_change_input(split_fixture):
    before = ConcreteData(split_fixture.rows, split_fixture.row_ids)
    train, test = split_data(split_fixture, seed=123)
    assert (len(train.rows), len(test.rows)) == (7, 3)
    assert set(train.row_ids).isdisjoint(test.row_ids)
    assert set(train.rows).isdisjoint(test.rows)
    assert set(train.row_ids) | set(test.row_ids) == {2, 4, 7, 11, 16, 22, 29, 37, 46, 56}
    assert split_fixture == before


def test_split_preserves_feature_target_and_id_alignment(split_fixture):
    original = dict(zip(split_fixture.row_ids, split_fixture.rows, strict=True))
    for partition in split_data(split_fixture, seed=123):
        features, targets = select_features_target(partition)
        for row_id, row, x, target in zip(
            partition.row_ids, partition.rows, features, targets, strict=True
        ):
            assert row == original[row_id] == x + (target,)


@pytest.mark.parametrize("seed", [None, True, -1, 2**32, 1.5, "123"])
def test_split_rejects_invalid_seeds(split_fixture, seed):
    with pytest.raises(ValueError, match="seed must be an explicitly supplied integer"):
        split_data(split_fixture, seed=seed)


def test_split_requires_a_seed(split_fixture):
    with pytest.raises(TypeError, match="seed"):
        split_data(split_fixture)


def test_split_rejects_duplicates(duplicate_data):
    with pytest.raises(ValueError, match="Remove duplicate full rows before splitting"):
        split_data(duplicate_data, seed=123)


@pytest.mark.parametrize("count", [0, 1])
def test_split_rejects_too_few_rows(count):
    data = ConcreteData((ROW_A,) * count, (2,) * count)
    with pytest.raises(ValueError, match="at least two rows"):
        split_data(data, seed=123)


def test_approved_xls_integration():
    path = Path("/app/inputs/Concrete_Data.xls")
    if not path.exists():
        pytest.skip("Approved XLS is unavailable; synthetic tests do not require it")
    before = path.read_bytes()
    assert hashlib.sha256(before).hexdigest() == (
        "710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4"
    )
    raw = load_concrete(path)
    cleaned, duplicate_of = remove_duplicates(raw)
    train, test = split_data(cleaned, seed=123)
    assert len(raw.rows) == 1030 and all(len(row) == 9 for row in raw.rows)
    assert (len(cleaned.rows), len(duplicate_of)) == (1005, 25)
    assert (len(train.rows), len(test.rows)) == (703, 302)
    assert set(train.row_ids).isdisjoint(test.row_ids)
    assert set(train.row_ids) | set(test.row_ids) | set(duplicate_of) == set(range(2, 1032))
    assert path.read_bytes() == before


@pytest.fixture
def linear_data():
    # Hand-defined y=2*x+1; seven zero predictors, no held-out observation in fit.
    train = ConcreteData(
        tuple((float(x),) + (0.0,) * 7 + (float(2 * x + 1),) for x in (0, 1, 2, 3)), (2, 3, 4, 5)
    )
    test = ConcreteData(((4.0,) + (0.0,) * 7 + (9.0,), (5.0,) + (0.0,) * 7 + (11.0,)), (6, 7))
    return train, test


def test_explicit_lr_has_known_predictions_and_preserves_inputs(linear_data):
    train, test = linear_data
    before = (train, test)
    actual = fit_predict(train, test, fit_intercept=True, positive=False, copy_X=True, n_jobs=1)
    assert actual == pytest.approx((9.0, 11.0), rel=1e-12, abs=1e-12)
    assert (train, test) == before


def test_lr_forwards_all_settings_and_fits_training_only(monkeypatch, linear_data):
    train, test = linear_data
    seen = {}

    class Model:
        def __init__(self, **kwargs):
            seen.update(kwargs)

        def fit(self, X, y):
            assert X == tuple(row[:8] for row in train.rows)
            assert y == (1.0, 3.0, 5.0, 7.0)

        def predict(self, X):
            assert X == tuple(row[:8] for row in test.rows)
            return (9.0, 11.0)

    monkeypatch.setattr(experiment, "LinearRegression", Model)
    fit_predict(train, test, fit_intercept=False, positive=True, copy_X=False, n_jobs=2)
    assert seen == {"fit_intercept": False, "positive": True, "copy_X": False, "n_jobs": 2}


@pytest.mark.parametrize(
    "change",
    [{"positive": 0}, {"fit_intercept": "True"}, {"copy_X": 1}, {"n_jobs": 0}, {"n_jobs": True}],
)
def test_lr_rejects_invalid_settings(linear_data, change):
    settings = dict(fit_intercept=True, positive=False, copy_X=True, n_jobs=1)
    settings.update(change)
    with pytest.raises(ValueError):
        fit_predict(*linear_data, **settings)


def test_lr_rejects_overlap_empty_data_and_nonfinite_predictions(monkeypatch, linear_data):
    train, test = linear_data
    settings = dict(fit_intercept=True, positive=False, copy_X=True, n_jobs=1)
    for invalid in (ConcreteData((), ()), train):
        with pytest.raises(ValueError):
            fit_predict(train, invalid, **settings)

    class BadModel:
        def __init__(self, **kwargs):
            pass

        def fit(self, X, y):
            pass

        def predict(self, X):
            return (float("nan"), 1.0)

    monkeypatch.setattr(experiment, "LinearRegression", BadModel)
    with pytest.raises(ValueError, match="Predictions"):
        fit_predict(train, test, **settings)


def measured(y, predictions, **changes):
    settings = dict(mape_zero_policy="exclude_zero_targets", nrmse_ddof=0)
    settings.update(changes)
    return evaluate_predictions(y, predictions, **settings)


def test_metrics_equal_hand_calculated_values():
    result = measured((1.0, 2.0, 3.0), (1.0, 2.0, 4.0))
    expected = {
        "RMSE": math.sqrt(1 / 3),
        "MAE": 1 / 3,
        "R2": 0.5,
        "MAPE": 100 / 9,
        "nRMSE": 100 / math.sqrt(2),
    }
    for name, value in expected.items():
        assert result[name]["value"] == pytest.approx(value, rel=1e-12, abs=1e-12)
        assert result[name]["status"] == "COMPUTED"
    assert result["MAPE"]["denominator"] == {"retained_count": 3, "excluded_zero_count": 0}
    assert result["nRMSE"]["denominator"]["test_std"] == pytest.approx(math.sqrt(2 / 3))
    assert result["nRMSE"]["denominator"]["ddof"] == 0


def test_mape_uses_retained_count_without_epsilon_or_near_zero_exclusion():
    result = measured((0.0, 2.0), (9.0, 1.0))
    assert result["MAPE"]["value"] == 50.0
    assert result["MAPE"]["denominator"] == {"retained_count": 1, "excluded_zero_count": 1}
    near_zero = measured((1e-300, 2e-300), (0.0, 0.0))
    assert near_zero["MAPE"]["value"] == 100.0
    assert near_zero["RMSE"]["value"] > 0
    assert near_zero["R2"]["status"] == "COMPUTED"


@pytest.mark.parametrize(
    "y,predictions,undefined",
    [
        ((0.0, 0.0), (1.0, 2.0), ("MAPE", "nRMSE", "R2")),
        ((2.0, 2.0), (2.0, 2.0), ("nRMSE", "R2")),
        ((2.0,), (1.0,), ("nRMSE", "R2")),
    ],
)
def test_undefined_metrics_are_null_with_reasons(y, predictions, undefined):
    result = measured(y, predictions)
    for name in undefined:
        assert result[name]["value"] is None and result[name]["reason"]
        assert result[name]["status"] == "NOT_COMPARABLE"
    json.dumps(result, allow_nan=False)


def test_r2_retains_negative_values():
    assert measured((1.0, 2.0, 3.0), (10.0, 10.0, 10.0))["R2"]["value"] < 0


@pytest.mark.parametrize(
    "y,predictions",
    [
        ((), ()),
        ((1.0,), ()),
        ((True,), (1.0,)),
        ((1.0,), ("1",)),
        ((float("nan"),), (1.0,)),
        ((1.0,), (float("inf"),)),
        ((1e308, -1e308), (-1e308, 1e308)),
    ],
)
def test_metrics_reject_invalid_or_overflowing_numbers(y, predictions):
    with pytest.raises(ValueError):
        measured(y, predictions)


@pytest.mark.parametrize(
    "change", [{"nrmse_ddof": 1}, {"nrmse_ddof": True}, {"mape_zero_policy": "epsilon"}]
)
def test_metrics_reject_unsupported_definitions(change):
    with pytest.raises(ValueError):
        measured((1.0, 2.0), (1.0, 2.0), **change)


@pytest.fixture
def cli_case():
    from reprolab.manifest import development_manifest, fingerprint

    with tempfile.TemporaryDirectory(prefix="reprolab-s09-test-", dir="/tmp") as scratch:
        root = Path(scratch)
        outputs = root / "runs"
        outputs.mkdir()
        m = development_manifest(hashlib.sha256(Path("/app/uv.lock").read_bytes()).hexdigest())
        argv = [
            "--manifest",
            "development",
            "--expected-manifest-sha256",
            fingerprint(m),
            "--input",
            "/app/inputs/missing.xls",
            "--run-id",
            "synthetic",
            "--output-root",
            str(outputs),
        ]
        yield root, outputs, argv, m
    assert not Path(scratch).exists()


def test_cli_loads_json_roundtrip_and_rejects_unapproved_or_invalid_manifest(cli_case):
    from reprolab.manifest import canonical_json, fingerprint

    root, _, _, m = cli_case
    lock = Path("/app/uv.lock").read_bytes()
    path = root / "manifest.json"
    path.write_text(canonical_json(m))
    assert fingerprint(cli._load_manifest(str(path), fingerprint(m), lock)) == fingerprint(m)
    with pytest.raises(ValueError, match="fingerprint"):
        cli._load_manifest(str(path), "0" * 64, lock)
    with pytest.raises(ValueError, match="lockfile"):
        cli._load_manifest(str(path), fingerprint(m), lock + b"\n")
    data = json.loads(path.read_text())
    del data["split"]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        cli._load_manifest(str(path), fingerprint(m), lock)
    data["split"] = json.loads(canonical_json(m))["split"]
    data["model"]["name"] = "RandomForestRegressor"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        cli._load_manifest(str(path), fingerprint(m), lock)
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="Duplicate"):
        cli._load_manifest(str(path), fingerprint(m), lock)


def test_environment_rejects_actual_version_drift(monkeypatch, cli_case):
    _, _, _, m = cli_case
    monkeypatch.setattr(cli.platform, "python_version", lambda: "3.12.0")
    with pytest.raises(ValueError, match="software"):
        cli._environment(m, Path("/app/uv.lock").read_bytes())


def test_claim_values_do_not_enter_measured_outputs(monkeypatch, cli_case, linear_data):
    from reprolab.manifest import LockedManifest

    root, _, argv, m = cli_case
    train, test = linear_data
    path = root / "synthetic.xls"
    path.write_bytes(b"synthetic loader stub; not an XLS")
    args = SimpleNamespace(
        manifest="development",
        expected_manifest_sha256="ignored by isolated stub",
        input=str(path),
        run_id="synthetic",
        max_seconds=300,
    )
    monkeypatch.setattr(cli, "_environment", lambda *_: {})
    monkeypatch.setattr(
        cli,
        "load_concrete",
        lambda _: ConcreteData(train.rows + test.rows, train.row_ids + test.row_ids),
    )
    monkeypatch.setattr(cli, "remove_duplicates", lambda raw, **kw: (raw, {}))
    monkeypatch.setattr(cli, "split_data", lambda raw, **kw: (train, test))
    values = []
    for fake_claim in (0.0, 999.0):
        data = json.loads(m.model_dump_json())
        for metric in data["metrics"]:
            metric["published_claim"]["value"] = 0.123 if metric["name"] == "R2" else fake_claim
        variant = LockedManifest.model_validate_json(json.dumps(data))
        monkeypatch.setattr(cli, "_load_manifest", lambda *a: variant)
        result = cli._execute(args)["results"]
        values.append(result["metrics"])
        assert (
            result["execution_status"] == "COMPLETED"
            and result["reproduction_status"] == "INCONCLUSIVE"
        )
        assert "published_claim" not in json.dumps(result)
    assert values[0] == values[1]
    assert values[0]["RMSE"]["value"] == pytest.approx(0, abs=1e-12)


def test_cli_missing_input_and_checksum_failure_leave_no_results(cli_case, capsys):
    root, outputs, argv, _ = cli_case
    assert cli.main(argv) == 2
    assert json.loads(capsys.readouterr().err)["execution_status"] == "BLOCKED"
    assert not list(outputs.iterdir())
    bad = root / "altered.xls"
    bad.write_bytes(b"wrong checksum")
    argv[argv.index("--input") + 1] = str(bad)
    assert cli.main(argv) == 2
    assert not list(outputs.iterdir())


@pytest.mark.parametrize("run_id", ["../escape", ".", "..", "/tmp/escape", "a/b", "a b", "a" * 65])
def test_cli_rejects_unsafe_run_ids(cli_case, run_id):
    _, outputs, argv, _ = cli_case
    argv[argv.index("--run-id") + 1] = run_id
    assert cli.main(argv) == 2
    assert not list(outputs.iterdir())


def test_cli_refuses_existing_runs_and_symlink_paths(monkeypatch, cli_case):
    root, outputs, argv, _ = cli_case

    def unexpected(*args):
        raise AssertionError("Existing run must fail before computation")

    monkeypatch.setattr(cli, "_supervise", unexpected)
    existing = outputs / "synthetic"
    existing.mkdir()
    sentinel = existing / "results.json"
    sentinel.write_text("previous result stays byte-identical")
    assert cli.main(argv) == 2
    assert sentinel.read_text() == "previous result stays byte-identical"
    link = root / "linked"
    link.symlink_to(outputs, target_is_directory=True)
    argv[argv.index("--output-root") + 1] = str(link)
    assert cli.main(argv) == 2
    for name in ("linked", "linked/synthetic/results.json"):
        with pytest.raises(ValueError, match="Symlink"):
            cli._safe_path(str(root / name))
    with pytest.raises(ValueError, match="traversal"):
        cli._safe_path(str(root / ".." / "anything"))


@pytest.mark.parametrize("seconds", ["0", "-1", "nan", "inf", "301"])
def test_cli_rejects_invalid_execution_limits(cli_case, seconds):
    _, outputs, argv, _ = cli_case
    with pytest.raises(SystemExit) as exc:
        cli.main(argv + ["--max-seconds", seconds])
    assert exc.value.code == 2
    assert not list(outputs.iterdir())


def test_actual_supervisor_timeout_kills_worker_and_cleans_reservation(cli_case, capsys):
    _, outputs, argv, _ = cli_case
    before = {p.pid for p in multiprocessing.active_children()}
    assert cli.main(argv + ["--max-seconds", "0.001"]) == 124
    assert json.loads(capsys.readouterr().err)["error_type"] == "TimeoutError"
    assert not list(outputs.iterdir())
    assert {p.pid for p in multiprocessing.active_children()} == before


def test_unexpected_failure_and_partial_write_cleanup(monkeypatch, cli_case, capsys):
    from reprolab.manifest import canonical_json

    _, outputs, argv, m = cli_case

    def fail(*args):
        raise RuntimeError("sensitive diagnostic must not be logged")

    monkeypatch.setattr(cli, "_supervise", fail)
    assert cli.main(argv) == 1
    assert "sensitive diagnostic" not in capsys.readouterr().err
    assert not list(outputs.iterdir())
    payload = {
        "manifest": canonical_json(m),
        "results": {"execution_status": "COMPLETED", "resources": {}},
    }
    monkeypatch.setattr(cli, "_supervise", lambda *a: {"ok": True, "payload": payload})
    count = 0

    def failed_sync(fd):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("injected failure after writing results")

    monkeypatch.setattr(cli.os, "fsync", failed_sync)
    assert cli.main(argv) == 2
    assert not list(outputs.iterdir())


def test_publisher_writes_only_manifest_and_results(monkeypatch, cli_case):
    from reprolab.manifest import canonical_json

    _, outputs, argv, m = cli_case
    payload = {
        "manifest": canonical_json(m),
        "results": {"execution_status": "COMPLETED", "resources": {}},
    }
    monkeypatch.setattr(cli, "_supervise", lambda *a: {"ok": True, "payload": payload})
    assert cli.main(argv) == 0
    run = outputs / "synthetic"
    assert {p.name for p in run.iterdir()} == {"manifest.json", "results.json"}
    assert (run / "manifest.json").read_text() == canonical_json(m)
    assert json.loads((run / "results.json").read_text())["execution_status"] == "COMPLETED"


@pytest.mark.parametrize("bad_manifest", [False, True])
def test_cli_invalid_manifest_or_fingerprint_never_publishes(cli_case, bad_manifest):
    root, outputs, argv, _ = cli_case
    if bad_manifest:
        path = root / "invalid.json"
        path.write_text('{"unsupported": true}')
        argv[argv.index("--manifest") + 1] = str(path)
    else:
        argv[argv.index("--expected-manifest-sha256") + 1] = "0" * 64
    assert cli.main(argv) == 2
    assert not list(outputs.iterdir())


def test_parent_publication_is_also_time_bounded(monkeypatch, cli_case):
    import time

    from reprolab.manifest import canonical_json

    _, outputs, argv, m = cli_case
    payload = {
        "manifest": canonical_json(m),
        "results": {"execution_status": "COMPLETED", "resources": {}},
    }
    monkeypatch.setattr(cli, "_supervise", lambda *a: {"ok": True, "payload": payload})
    monkeypatch.setattr(cli.os, "fsync", lambda fd: time.sleep(2))
    assert cli.main(argv + ["--max-seconds", "0.05"]) == 124
    assert not list(outputs.iterdir())


def test_environment_rejects_distribution_drift(monkeypatch, cli_case):
    _, _, _, m = cli_case
    monkeypatch.setattr(cli.importlib.metadata, "distributions", lambda: [])
    with pytest.raises(ValueError, match="software"):
        cli._environment(m, Path("/app/uv.lock").read_bytes())


@pytest.fixture
def report_case():
    """Independent synthetic measurements; no persisted experiment or dataset needed."""
    from reprolab.manifest import development_manifest, fingerprint

    lock = Path("/app/uv.lock").read_bytes()
    m = development_manifest(hashlib.sha256(lock).hexdigest())
    protocols = {p.name: p for p in m.metrics}
    values = {"RMSE": 1.0, "MAE": 0.5, "R2": 0.75, "MAPE": 20.0, "nRMSE": 50.0}
    denominators = {
        "RMSE": {"count": 302},
        "MAE": {"count": 302},
        "R2": {"count": 302, "target_deviation_l2": 2 * math.sqrt(302)},
        "MAPE": {"retained_count": 302, "excluded_zero_count": 0},
        "nRMSE": {"count": 302, "test_std": 2.0, "ddof": 0},
    }
    measurements = {
        name: {
            "value": value,
            "unit": "dimensionless"
            if name == "R2"
            else "percent"
            if name in ("MAPE", "nRMSE")
            else "MPa",
            "status": "COMPUTED",
            "reason": None,
            "denominator": denominators[name],
            "definition": protocols[name].definition.model_dump(mode="json"),
        }
        for name, value in values.items()
    }
    measurements["MAPE"]["zero_policy_provenance"] = protocols[
        "MAPE"
    ].zero_target_policy.model_dump(mode="json")
    measurements["nRMSE"]["ddof_provenance"] = protocols["nRMSE"].ddof.model_dump(mode="json")
    source = {name: "0" * 64 for name in ("__init__.py", "cli.py", "experiment.py", "manifest.py")}
    source_sha = hashlib.sha256(
        json.dumps(source, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    r = {
        "results_schema_version": 1,
        "run_id": "synthetic",
        "execution_status": "COMPLETED",
        "experiment_classification": "INDEPENDENT_REIMPLEMENTATION",
        "reproduction_status": "INCONCLUSIVE",
        "protocol_limitations": ["Synthetic unit-test evidence; no real execution claim"],
        "manifest_sha256": fingerprint(m),
        "dataset_sha256": m.dataset.sha256.value,
        "split": {
            "seed": 123,
            "raw_rows": 1030,
            "cleaned_rows": 1005,
            "duplicates_removed": 25,
            "train_rows": 703,
            "test_rows": 302,
            "row_ids_sha256": "a" * 64,
        },
        "model": {
            "name": "sklearn.linear_model.LinearRegression",
            "parameters": {"fit_intercept": True, "positive": False, "copy_X": True, "n_jobs": 1},
        },
        "metrics": measurements,
        "environment": {
            "python": "3.12.16",
            "uv": "0.13.8",
            "packages": {
                p["name"]: p["version"]
                for p in tomllib.loads(lock.decode())["package"]
                if p["name"] not in ("reprolab", "colorama")
            },
            "system": "Linux",
            "machine": "test-architecture",
            "threads": {
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
            },
            "uv_lock_sha256": m.environment.uv_lock_sha256,
        },
        "source": {
            "base_git_commit": None,
            "git_revision_origin": "unavailable",
            "files_sha256": source,
            "sha256": source_sha,
        },
        "resources": {
            "execution_limit_seconds": 300.0,
            "automatic_retries": 0,
            "paid_calls": 0,
            "worker_cpu_seconds": 1.0,
            "worker_peak_rss_kib": 1000,
            "wall_seconds": 1.1,
        },
        "created_at_utc": "2026-01-01T00:00:00+00:00",
    }
    return m, r, dict(lock_bytes=lock, split_identity="a" * 64)


def _report_rebind(manifest, results, data):
    from reprolab.manifest import LockedManifest, fingerprint

    changed = LockedManifest.model_validate_json(json.dumps(data))
    results["manifest_sha256"] = fingerprint(changed)
    return changed


def test_report_identical_numbers_leave_unknown_protocol_inconclusive(report_case):
    from reprolab.report import compare_run

    m, r, context = report_case
    data = json.loads(m.model_dump_json())
    for p in data["metrics"]:
        p["published_claim"]["value"] = r["metrics"][p["name"]]["value"]
    m = _report_rebind(m, r, data)
    comparison = compare_run(m, r, **context)
    assert comparison["scientific_verdict"] == "INCONCLUSIVE"
    assert all(row["display_check"] == "WITHIN" for row in comparison["metrics"])
    findings = {f["item"]: f for f in comparison["findings"]}
    assert findings["Published holdout seed"]["status"] == "UNKNOWN"
    assert findings["Published LR positive"]["status"] == "UNKNOWN"
    assert comparison["metrics"][-1]["agreement"] == "NOT_COMPARABLE"


@pytest.mark.parametrize("field,actual", [("holdout_seed", 7), ("final_positive", True)])
def test_report_known_conflicting_paper_settings_are_mismatch(report_case, field, actual):
    from reprolab.report import compare_run

    m, r, context = report_case
    data = json.loads(m.model_dump_json())
    for metric in data["metrics"]:
        metric["published_claim"]["value"] = r["metrics"][metric["name"]]["value"]
    evidence = data["paper"]["evidence"]
    data["research"][field] = {
        "value": actual,
        "origin": "paper_reported",
        "status": "reported",
        "evidence": evidence,
        "explanation": None,
    }
    m = _report_rebind(m, r, data)
    comparison = compare_run(m, r, **context)
    assert comparison["scientific_verdict"] == "INCONCLUSIVE"
    assert any(f["status"] == "MISMATCH" for f in comparison["findings"])
    assert all(row["display_check"] == "WITHIN" for row in comparison["metrics"])


@pytest.mark.parametrize(
    "path,value",
    [
        ("dataset_sha256", "0" * 64),
        ("manifest_sha256", "0" * 64),
        ("split.seed", 7),
        ("split.row_ids_sha256", "b" * 64),
        ("split.cleaned_rows", 1030),
        ("model.parameters.positive", True),
        ("model.name", "RandomForestRegressor"),
        ("metrics.RMSE.value", float("nan")),
        ("metrics.MAE.value", float("inf")),
        ("metrics.MAPE.value", "20"),
        ("metrics.RMSE.value", None),
        ("metrics.MAE.value", 2.0),
        ("metrics.R2.value", 0.5),
        ("metrics.nRMSE.value", 40.0),
        ("metrics.RMSE.unit", "percent"),
        ("metrics.RMSE.definition.value", "unreviewed formula"),
        ("metrics.RMSE.population", "train"),
        ("metrics.MAPE.denominator.retained_count", 301),
        ("metrics.nRMSE.denominator.ddof", 1),
        ("metrics.R2.denominator.count", True),
        ("metrics.nRMSE.denominator.test_std", 1.0),
        ("metrics.nRMSE.ddof_provenance", None),
        ("environment.python", "3.12.0"),
        ("environment.packages.numpy", "0.0"),
        ("environment.uv_lock_sha256", "0" * 64),
        ("environment.threads.OMP_NUM_THREADS", "2"),
        ("source.sha256", "0" * 64),
        ("source.files_sha256.cli.py", "f" * 64),
        ("source.git_revision_origin", "caller_supplied"),
        ("execution_status", "FAILED"),
        ("reproduction_status", "REPRODUCED"),
        ("created_at_utc", "2026-01-01T00:00:00"),
        ("resources.paid_calls", 1),
        ("results_schema_version", True),
        ("unexpected", "field"),
    ],
)
def test_report_rejects_invalid_or_tampered_artifacts(report_case, path, value):
    from reprolab.report import validate_results

    m, r, context = report_case
    if path == "source.files_sha256.cli.py":
        r["source"]["files_sha256"]["cli.py"] = value
    else:
        parent = r
        keys = path.split(".")
        for key in keys[:-1]:
            parent = parent[key]
        parent[keys[-1]] = value
    with pytest.raises((ValueError, TypeError)):
        validate_results(m, r, **context)


@pytest.mark.parametrize(
    "missing", ["metrics", "split", "source", "environment", "resources", "created_at_utc"]
)
def test_report_rejects_incomplete_artifacts(report_case, missing):
    from reprolab.report import validate_results

    m, r, context = report_case
    del r[missing]
    with pytest.raises(ValueError):
        validate_results(m, r, **context)


def test_report_tolerance_boundaries_and_percentage_points(report_case):
    from reprolab.report import compare_run

    m, r, context = report_case
    for published, expected in [(20.005, "WITHIN"), (20.005000001, "OUTSIDE")]:
        data = json.loads(m.model_dump_json())
        next(p for p in data["metrics"] if p["name"] == "MAPE")["published_claim"]["value"] = (
            published
        )
        current = _report_rebind(m, r, data)
        row = next(p for p in compare_run(current, r, **context)["metrics"] if p["name"] == "MAPE")
        assert row["display_check"] == expected
        if expected == "WITHIN":
            assert row["absolute_difference"] == Decimal("0.005")
            assert row["relative_difference_percent"] != Decimal("0.005")
    data = json.loads(m.model_dump_json())
    next(p for p in data["metrics"] if p["name"] == "MAPE")["published_claim"]["value"] = 0.0
    current = _report_rebind(m, r, data)
    row = next(p for p in compare_run(current, r, **context)["metrics"] if p["name"] == "MAPE")
    assert row["relative_difference_percent"] is None


def test_report_incompatible_denominator_cannot_receive_agreement(report_case):
    from reprolab.report import compare_run

    m, r, context = report_case
    r["metrics"]["MAPE"]["denominator"] = {"retained_count": 301, "excluded_zero_count": 1}
    row = next(p for p in compare_run(m, r, **context)["metrics"] if p["name"] == "MAPE")
    assert row["compatibility"] == "UNKNOWN" and row["agreement"] == "NOT_COMPARABLE"
    data = json.loads(m.model_dump_json())
    data["research"]["nrmse_ddof"] = {
        "value": 1,
        "origin": "paper_reported",
        "status": "reported",
        "evidence": data["paper"]["evidence"],
        "explanation": None,
    }
    m = _report_rebind(m, r, data)
    row = compare_run(m, r, **context)["metrics"][-1]
    assert row["compatibility"] == "MISMATCH" and row["agreement"] == "NOT_COMPARABLE"


def test_report_undefined_metrics_are_explicit(report_case):
    from reprolab.report import compare_run

    m, r, context = report_case
    for name in ("R2", "nRMSE", "MAPE"):
        r["metrics"][name].update(
            value=None, status="NOT_COMPARABLE", reason="Synthetic undefined denominator"
        )
    r["metrics"]["R2"]["denominator"]["target_deviation_l2"] = 0.0
    r["metrics"]["nRMSE"]["denominator"]["test_std"] = 0.0
    r["metrics"]["MAPE"]["denominator"].update(retained_count=0, excluded_zero_count=302)
    for row in compare_run(m, r, **context)["metrics"][2:]:
        assert row["display_check"] == "UNDEFINED" and row["agreement"] == "NOT_COMPARABLE"
        assert row["absolute_difference"] is None


def test_report_rendering_is_deterministic_and_safe(report_case):
    from reprolab.report import render_markdown

    m, r, context = report_case
    before = copy.deepcopy(r)
    r["protocol_limitations"] = ["<script>bad</script> | `payload`\nnot instructions"]
    first = render_markdown(m, r, results_sha256="0" * 64, **context)
    with localcontext() as ctx:
        ctx.prec = 7
        ctx.rounding = "ROUND_FLOOR"
        second = render_markdown(m, r, results_sha256="0" * 64, **context)
    assert first == second and "Scientific verdict: INCONCLUSIVE" in first
    assert "<script>" not in first and r["created_at_utc"] in first
    assert "&lt;script&gt;" in first and r["source"]["sha256"] in first
    r["protocol_limitations"] = before["protocol_limitations"]
    assert r == before


@pytest.fixture
def report_cli_case(monkeypatch, report_case):
    from reprolab.manifest import canonical_json, fingerprint

    m, r, context = report_case
    with tempfile.TemporaryDirectory(prefix="reprolab-s10-test-", dir="/tmp") as scratch:
        root = Path(scratch)
        run = root / "synthetic"
        run.mkdir()
        (run / "manifest.json").write_text(canonical_json(m))
        raw = json.dumps(r).encode()
        (run / "results.json").write_bytes(raw)
        argv = [
            "--report-only",
            "--run-id",
            "synthetic",
            "--output-root",
            str(root),
            "--expected-manifest-sha256",
            fingerprint(m),
            "--expected-results-sha256",
            hashlib.sha256(raw).hexdigest(),
        ]
        # Synthetic validation split; source XLS is only read, never changed.
        targets = (1.0, 5.0) * 151
        test = ConcreteData(tuple((0.0,) * 8 + (y,) for y in targets), tuple(range(2, 304)))
        train = ConcreteData((), ())
        split_sha = hashlib.sha256(
            json.dumps(
                {"train": train.row_ids, "test": test.row_ids},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        r["split"]["row_ids_sha256"] = split_sha
        raw = json.dumps(r).encode()
        (run / "results.json").write_bytes(raw)
        argv[argv.index("--expected-results-sha256") + 1] = hashlib.sha256(raw).hexdigest()
        source = root / "synthetic.xls"
        source.write_bytes(b"Synthetic reader stub, not a dataset")
        argv += ["--input", str(source)]
        monkeypatch.setattr(cli, "load_concrete", lambda path: test)
        monkeypatch.setattr(cli, "remove_duplicates", lambda data, **kw: (data, {}))
        monkeypatch.setattr(cli, "split_data", lambda *a, **kw: (train, test))

        def forbidden(*a, **kw):
            raise AssertionError("Reporting must never fit or supervise a model")

        monkeypatch.setattr(cli, "fit_predict", forbidden)
        monkeypatch.setattr(cli, "_supervise", forbidden)
        yield run, argv
    assert not Path(scratch).exists()


def test_report_cli_preserves_json_and_refuses_overwrite(report_cli_case):
    run, argv = report_cli_case
    before = {name: (run / name).read_bytes() for name in ("manifest.json", "results.json")}
    assert cli.main(argv) == 0
    report = (run / "report.md").read_bytes()
    assert b"INCONCLUSIVE" in report
    assert cli.main(argv) == 2
    assert (run / "report.md").read_bytes() == report
    assert all((run / name).read_bytes() == raw for name, raw in before.items())


@pytest.mark.parametrize(
    "failure", ["missing", "tamper", "duplicate", "unsafe", "symlink", "write"]
)
def test_report_cli_failure_never_publishes_or_changes_evidence(
    monkeypatch, report_cli_case, failure
):
    run, argv = report_cli_case
    if failure == "missing":
        (run / "results.json").unlink()
    if failure == "tamper":
        data = json.loads((run / "results.json").read_text())
        data["metrics"]["MAPE"]["value"] = 20.0001
        (run / "results.json").write_text(json.dumps(data))
    if failure == "duplicate":
        raw = b'{"run_id":"synthetic",' + (run / "results.json").read_bytes()[1:]
        (run / "results.json").write_bytes(raw)
        argv[argv.index("--expected-results-sha256") + 1] = hashlib.sha256(raw).hexdigest()
    if failure == "unsafe":
        argv[argv.index("--run-id") + 1] = "../escape"
    if failure == "symlink":
        (run / "report.md").symlink_to("/tmp/nonexistent-s10-report")
    if failure == "write":

        def bad_sync(fd):
            raise OSError("Injected report flush failure")

        monkeypatch.setattr(cli.os, "fsync", bad_sync)
    before = {p.name: p.read_bytes() for p in run.glob("*.json")}
    assert cli.main(argv) == 2
    assert not (run / "report.md").exists()
    assert before == {p.name: p.read_bytes() for p in run.glob("*.json")}


@pytest.mark.parametrize(
    "name,value,tolerance",
    [
        ("RMSE", "1", "0.005"),
        ("MAE", "0.5", "0.005"),
        ("R2", "0.75", "0.0005"),
        ("MAPE", "20", "0.005"),
        ("nRMSE", "50", "0.005"),
    ],
)
def test_report_each_inclusive_tolerance_boundary(report_case, name, value, tolerance):
    from reprolab.report import compare_run

    m, r, context = report_case
    for increment, expected in [("0", "WITHIN"), ("0.000000000001", "OUTSIDE")]:
        data = json.loads(m.model_dump_json())
        published = Decimal(value) + Decimal(tolerance) + Decimal(increment)
        next(p for p in data["metrics"] if p["name"] == name)["published_claim"]["value"] = float(
            published
        )
        changed = _report_rebind(m, r, data)
        row = next(p for p in compare_run(changed, r, **context)["metrics"] if p["name"] == name)
        assert row["display_check"] == expected


def test_report_percentage_point_and_relative_differences_are_distinct(report_case):
    from reprolab.report import compare_run

    m, r, context = report_case
    data = json.loads(m.model_dump_json())
    for name, published in [("MAPE", 25.0), ("nRMSE", 80.0)]:
        next(p for p in data["metrics"] if p["name"] == name)["published_claim"]["value"] = (
            published
        )
    changed = _report_rebind(m, r, data)
    rows = {p["name"]: p for p in compare_run(changed, r, **context)["metrics"]}
    assert rows["MAPE"]["absolute_difference"] == Decimal("5")
    assert rows["MAPE"]["relative_difference_percent"] == Decimal("20")
    assert rows["nRMSE"]["absolute_difference"] == Decimal("30")
    assert rows["nRMSE"]["relative_difference_percent"] == Decimal("37.5")
    assert rows["nRMSE"]["agreement"] == "NOT_COMPARABLE"


def test_report_rejects_zero_normalizer_masked_by_float_tolerance(report_case):
    from reprolab.report import validate_results

    m, r, context = report_case
    r["metrics"]["R2"]["denominator"]["target_deviation_l2"] = 1e-300
    r["metrics"]["nRMSE"]["denominator"]["test_std"] = 0.0
    r["metrics"]["nRMSE"].update(value=None, status="NOT_COMPARABLE", reason="zero denominator")
    with pytest.raises(ValueError, match="Zero/nonzero"):
        validate_results(m, r, **context)


def test_report_requires_independent_results_digest(report_cli_case):
    _, argv = report_cli_case
    idx = argv.index("--expected-results-sha256")
    del argv[idx : idx + 2]
    with pytest.raises(SystemExit) as exc:
        cli.main(argv)
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "path,value", [("dataset_sha256", "0" * 64), ("seed", 7), ("positive", True)]
)
def test_report_wrong_execution_metadata_rejected_even_for_exact_scores(report_case, path, value):
    from reprolab.report import compare_run

    m, r, context = report_case
    data = json.loads(m.model_dump_json())
    for metric in data["metrics"]:
        metric["published_claim"]["value"] = r["metrics"][metric["name"]]["value"]
    m = _report_rebind(m, r, data)
    assert all(row["display_check"] == "WITHIN" for row in compare_run(m, r, **context)["metrics"])
    if path == "dataset_sha256":
        r[path] = value
    if path == "seed":
        r["split"][path] = value
    if path == "positive":
        r["model"]["parameters"][path] = value
    with pytest.raises(ValueError):
        compare_run(m, r, **context)


def test_report_parent_deadline_cleans_partial_publication(monkeypatch, report_cli_case):
    import time

    run, argv = report_cli_case
    before = {p.name: p.read_bytes() for p in run.glob("*.json")}
    syncing = []

    def delayed_sync(fd):
        syncing.append(fd)
        time.sleep(2)

    monkeypatch.setattr(cli.os, "fsync", delayed_sync)
    assert cli.main(argv + ["--max-seconds", "0.5"]) == 124
    assert syncing
    assert not (run / "report.md").exists()
    assert before == {p.name: p.read_bytes() for p in run.glob("*.json")}
