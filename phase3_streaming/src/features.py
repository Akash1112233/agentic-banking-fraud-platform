"""Feature construction shared by offline training and online scoring."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

PHASE1_SRC = Path(__file__).resolve().parents[2] / "phase1_data_foundation" / "src"
import sys
sys.path.insert(0, str(PHASE1_SRC))
from preprocess import preprocess_transaction_chunk  # noqa: E402


NUMERIC_FEATURES = [
    "log_amount_received",
    "log_amount_paid",
    "amount_difference",
    "hour",
    "hour_sin",
    "hour_cos",
    "same_bank",
    "same_currency",
]
CATEGORICAL_FEATURES = [
    "payment_format",
    "receiving_currency",
    "payment_currency",
]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def build_model_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Build the exact feature columns expected by the Phase 2 Joblib pipeline."""
    frame = frame.copy()
    if "Is Laundering" not in frame.columns:
        frame["Is Laundering"] = 0
    clean = preprocess_transaction_chunk(frame)
    received = clean["Amount Received"].astype(float).clip(lower=0)
    paid = clean["Amount Paid"].astype(float).clip(lower=0)
    features = pd.DataFrame(index=clean.index)
    features["log_amount_received"] = np.log1p(received)
    features["log_amount_paid"] = np.log1p(paid)
    features["amount_difference"] = clean["Amount Difference"].astype(float)
    features["hour"] = clean["Hour"].astype(float)
    features["hour_sin"] = np.sin(2 * np.pi * features["hour"] / 24)
    features["hour_cos"] = np.cos(2 * np.pi * features["hour"] / 24)
    features["same_bank"] = (clean["From Bank"] == clean["To Bank"]).astype(int)
    features["same_currency"] = (
        clean["Receiving Currency"] == clean["Payment Currency"]
    ).astype(int)
    features["payment_format"] = clean["Payment Format"].astype("string")
    features["receiving_currency"] = clean["Receiving Currency"].astype("string")
    features["payment_currency"] = clean["Payment Currency"].astype("string")
    return features[FEATURE_COLUMNS]


def build_model_features_from_record(record: Mapping[str, object]) -> pd.DataFrame:
    """Build a one-row feature frame from a Kafka JSON record."""
    return build_model_features(pd.DataFrame([dict(record)]))
