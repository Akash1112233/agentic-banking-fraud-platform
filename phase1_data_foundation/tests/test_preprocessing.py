import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from preprocess import normalize_transaction_columns, preprocess_transaction_chunk


def test_duplicate_account_columns_are_named_by_direction():
    columns = ["Timestamp", "From Bank", "Account", "To Bank", "Account", "Is Laundering"]
    assert normalize_transaction_columns(columns) == [
        "Timestamp", "From Bank", "From Account", "To Bank", "To Account", "Is Laundering"
    ]


def test_transaction_chunk_preprocessing_adds_derived_fields():
    frame = pd.DataFrame(
        [["2022/09/01 00:20", "010", "A", "020", "B", "10.5", "Euro", "10.0", "Euro", "ACH", 1]],
        columns=[
            "Timestamp", "From Bank", "Account", "To Bank", "Account", "Amount Received",
            "Receiving Currency", "Amount Paid", "Payment Currency", "Payment Format", "Is Laundering",
        ],
    )
    result = preprocess_transaction_chunk(frame)
    assert result.loc[0, "From Account"] == "A"
    assert result.loc[0, "To Account"] == "B"
    assert result.loc[0, "Hour"] == 0
    assert result.loc[0, "Is Laundering"] == 1
    assert result.loc[0, "Amount Difference"] == 0.5
