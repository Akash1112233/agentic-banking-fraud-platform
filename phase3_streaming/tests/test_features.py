import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "phase3_streaming" / "src"))
from features import FEATURE_COLUMNS, build_model_features_from_record  # noqa: E402


def sample_record():
    return {
        "Timestamp": "2022-09-01 12:30:00",
        "From Bank": "001",
        "From Account": "A001",
        "To Bank": "002",
        "To Account": "B002",
        "Amount Received": 100.0,
        "Receiving Currency": "USD",
        "Amount Paid": 95.0,
        "Payment Currency": "USD",
        "Payment Format": "ACH",
        "transaction_id": "tx-test-1",
    }


def test_online_features_match_phase2_schema():
    features = build_model_features_from_record(sample_record())
    assert list(features.columns) == FEATURE_COLUMNS
    assert features.loc[0, "same_bank"] == 0
    assert features.loc[0, "same_currency"] == 1
    assert features.loc[0, "hour"] == 12
    assert features.loc[0, "payment_format"] == "ACH"


def test_online_features_are_one_row_and_numeric_values_are_finite():
    features = build_model_features_from_record(sample_record())
    numeric = features.select_dtypes(include="number")
    assert features.shape == (1, len(FEATURE_COLUMNS))
    assert numeric.notna().all().all()
    assert pd.Series(numeric.to_numpy().ravel()).map(pd.api.types.is_number).all()
