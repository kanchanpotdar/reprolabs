"""Deterministic data contracts; synthetic expectations are independent of the code.

Only the optional final test reads the approved local XLS. No test fits a model.
"""

import hashlib
import tempfile
from pathlib import Path

import pytest

from reprolab import experiment
from reprolab.experiment import (
    ConcreteData,
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
