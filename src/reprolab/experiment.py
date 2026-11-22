"""Load the approved UCI snapshot; prepare data without fitting any model.

The checksum/schema are human-reviewed development fixtures, not extracted paper
claims. Only load_concrete performs file I/O; the remaining functions are pure.
Row identifiers are original Excel row numbers (2 through 1031, header excluded).
"""

import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Real
from pathlib import Path

import xlrd
from sklearn.model_selection import train_test_split

CONCRETE_SHA256 = "710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4"
CONCRETE_COLUMNS = (
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


@dataclass(frozen=True)
class ConcreteData:
    """Unscaled numeric rows and their aligned original worksheet identifiers."""

    rows: tuple[tuple[float, ...], ...]
    row_ids: tuple[int, ...]


def _validate_data(data: ConcreteData) -> None:
    """Check processing inputs without changing their values or identifiers."""
    if len(data.rows) != len(data.row_ids):
        raise ValueError("Row values and row identifiers must have equal lengths")
    if any(type(row_id) is not int or not 2 <= row_id <= 1031 for row_id in data.row_ids):
        raise ValueError("Row identifiers must be original Excel row numbers 2 through 1031")
    if len(set(data.row_ids)) != len(data.row_ids):
        raise ValueError("Row identifiers must be unique")
    for row_id, row in zip(data.row_ids, data.rows, strict=True):
        if len(row) != len(CONCRETE_COLUMNS):
            raise ValueError(f"Excel row {row_id}: expected 9 columns, got {len(row)}")
        for column, value in enumerate(row, start=1):
            if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
                raise ValueError(f"Excel row {row_id}, column {column}: expected a finite number")


def validate_concrete(headers: Sequence[str], rows: Sequence[Sequence[float]]) -> ConcreteData:
    """Validate the exact raw schema and 1030 rows; assign original Excel IDs."""
    if tuple(headers) != CONCRETE_COLUMNS:
        raise ValueError("Concrete schema mismatch: expected the exact nine ordered XLS headers")
    if len(rows) != 1030:
        raise ValueError(f"Expected 1030 raw data rows, got {len(rows)}")
    data = ConcreteData(tuple(tuple(row) for row in rows), tuple(range(2, 1032)))
    _validate_data(data)
    return data


def load_concrete(path: str | Path) -> ConcreteData:
    """Read and verify the approved XLS bytes before parsing; never write them."""
    raw = Path(path).read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != CONCRETE_SHA256:
        raise ValueError(f"Concrete SHA-256 mismatch: expected {CONCRETE_SHA256}, got {observed}")

    # Parse the very bytes hashed above, avoiding a second filesystem read.
    with xlrd.open_workbook(file_contents=raw, on_demand=True) as workbook:
        if workbook.sheet_names() != ["Sheet1", "Sheet2", "Sheet3"]:
            raise ValueError("Expected Sheet1 and the two empty source workbook tabs")
        if any(workbook.sheet_by_name(name).nrows for name in ("Sheet2", "Sheet3")):
            raise ValueError("Expected Sheet2 and Sheet3 to be empty")
        sheet = workbook.sheet_by_name("Sheet1")
        if (sheet.nrows, sheet.ncols) != (1031, 9):
            raise ValueError("Expected Sheet1 dimensions 1031 x 9 including its header")
        for row in range(1, sheet.nrows):
            for column in range(sheet.ncols):
                if sheet.cell_type(row, column) != xlrd.XL_CELL_NUMBER:
                    raise ValueError(f"Excel row {row + 1}, column {column + 1}: nonnumeric cell")
        return validate_concrete(
            sheet.row_values(0), [sheet.row_values(row) for row in range(1, sheet.nrows)]
        )


def remove_duplicates(
    data: ConcreteData, *, expected_rows: int = 1005
) -> tuple[ConcreteData, dict[int, int]]:
    """Keep each full row's first occurrence and map removed IDs to retained IDs.

    Full-row equality includes the target, matching the inspected author policy.
    No sorting, feature-only merging, or changes to source identifiers occur.
    """
    _validate_data(data)
    first_ids: dict[tuple[float, ...], int] = {}
    kept_rows = []
    kept_ids = []
    duplicate_of = {}
    for row_id, row in zip(data.row_ids, data.rows, strict=True):
        if row in first_ids:
            duplicate_of[row_id] = first_ids[row]
        else:
            first_ids[row] = row_id
            kept_rows.append(row)
            kept_ids.append(row_id)
    if len(kept_rows) != expected_rows:
        raise ValueError(f"Expected {expected_rows} distinct full rows, got {len(kept_rows)}")
    return ConcreteData(tuple(kept_rows), tuple(kept_ids)), duplicate_of


def select_features_target(
    data: ConcreteData,
) -> tuple[tuple[tuple[float, ...], ...], tuple[float, ...]]:
    """Return eight predictors and strength in MPa, in the same row order.

    Ingredient units remain kg/m³ and age remains days. No rounding or scaling.
    """
    _validate_data(data)
    return tuple(row[:8] for row in data.rows), tuple(row[8] for row in data.rows)


def split_data(data: ConcreteData, *, seed: int) -> tuple[ConcreteData, ConcreteData]:
    """Return a shuffled, unstratified 70/30 split with aligned original IDs.

    The caller must supply an integer seed. The approved development call uses
    123 from author code; this is not a verified published split configuration.
    """
    _validate_data(data)
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("seed must be an explicitly supplied integer in [0, 2**32)")
    if len(data.rows) < 2:
        raise ValueError("A train/test split requires at least two rows")
    if len(set(data.rows)) != len(data.rows):
        raise ValueError("Remove duplicate full rows before splitting")
    # Split rows and IDs in one call so features, targets, and identity stay aligned.
    train_rows, test_rows, train_ids, test_ids = train_test_split(
        data.rows, data.row_ids, test_size=0.30, random_state=seed, shuffle=True, stratify=None
    )
    return (
        ConcreteData(tuple(train_rows), tuple(train_ids)),
        ConcreteData(tuple(test_rows), tuple(test_ids)),
    )
