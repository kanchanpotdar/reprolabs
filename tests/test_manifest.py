"""S11 gaps: required manifest facts and population-normalized metric consistency."""

import json
import math

import pytest
from pydantic import ValidationError

from reprolab.experiment import evaluate_predictions
from reprolab.manifest import LockedManifest, development_manifest


@pytest.mark.parametrize(
    "section,field",
    [
        ("split", "seed"),
        ("model", "fit_intercept"),
        ("model", "positive"),
        ("model", "copy_X"),
        ("model", "n_jobs"),
        ("paper", "evidence"),
        ("nRMSE", "ddof"),
        ("MAPE", "zero_target_policy"),
    ],
    ids=[
        "split-seed",
        "lr-fit-intercept",
        "lr-positive",
        "lr-copy-X",
        "lr-n-jobs",
        "paper-evidence",
        "nrmse-ddof",
        "mape-zero-policy",
    ],
)
def test_manifest_rejects_missing_setting_or_evidence(section, field):
    # A synthetic lock digest keeps this schema test entirely in memory.
    payload = development_manifest("0" * 64).model_dump(mode="json")
    if section in {"MAPE", "nRMSE"}:
        index = next(i for i, metric in enumerate(payload["metrics"]) if metric["name"] == section)
        parent = payload["metrics"][index]
        expected_location = ("metrics", index, field)
    else:
        parent = payload[section]
        expected_location = (section, field)
    del parent[field]

    with pytest.raises(ValidationError) as exc:
        LockedManifest.model_validate_json(json.dumps(payload))
    assert any(
        error["type"] == "missing" and error["loc"] == expected_location
        for error in exc.value.errors()
    )


@pytest.mark.parametrize(
    "predictions,expected_r2,expected_nrmse",
    [
        ((2.0, 4.0, 6.0), 1.0, 0.0),
        ((2.0, 4.0, 8.0), 0.5, 100 / math.sqrt(2)),
        ((6.0, 8.0, 10.0), -5.0, 100 * math.sqrt(6)),
    ],
    ids=["perfect", "imperfect", "negative-r2"],
)
def test_population_nrmse_r2_identity(predictions, expected_r2, expected_nrmse):
    """Same aligned, unweighted test population; n>=2, nonzero variance, ddof=0.

    Hand calculation: y=(2,4,6), mean=4, SST=8, population variance=8/3.
    The three SSEs are 0, 4, 48. R2=1-SSE/8; nRMSE=100*sqrt(SSE/8).
    Hence nRMSE/100=sqrt(1-R2), including negative R2. This does not
    establish the paper's unknown ddof or hold for another normalization.
    """
    result = evaluate_predictions(
        (2.0, 4.0, 6.0),
        predictions,
        mape_zero_policy="exclude_zero_targets",
        nrmse_ddof=0,
    )
    r2, nrmse = result["R2"], result["nRMSE"]
    assert r2["status"] == nrmse["status"] == "COMPUTED"
    assert r2["unit"] == "dimensionless" and nrmse["unit"] == "percent"
    assert r2["denominator"]["count"] == nrmse["denominator"]["count"] == 3
    assert nrmse["denominator"]["ddof"] == 0
    assert nrmse["denominator"]["test_std"] == pytest.approx(math.sqrt(8 / 3), rel=1e-12, abs=1e-12)
    assert r2["value"] == pytest.approx(expected_r2, rel=1e-12, abs=1e-12)
    assert nrmse["value"] == pytest.approx(expected_nrmse, rel=1e-12, abs=1e-12)
    assert nrmse["value"] / 100 == pytest.approx(math.sqrt(1 - r2["value"]), rel=1e-12, abs=1e-12)
