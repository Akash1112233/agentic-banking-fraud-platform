"""Reusable preprocessing helpers for the IBM AML transaction dataset."""

from __future__ import annotations

from typing import Iterable

import pandas as pd


TRANSACTION_COLUMNS = [
    "Timestamp",
    "From Bank",
    "From Account",
    "To Bank",
    "To Account",
    "Amount Received",
    "Receiving Currency",
    "Amount Paid",
    "Payment Currency",
    "Payment Format",
    "Is Laundering",
]


def normalize_transaction_columns(columns: Iterable[str]) -> list[str]:
    """Return stable names, including distinct sender/receiver account names."""
    names = list(columns)
    normalized: list[str] = []
    account_seen = 0
    for name in names:
        # pandas mangles duplicate CSV headers as Account and Account.1.
        if name == "Account" or name.startswith("Account."):
            account_seen += 1
            normalized.append("From Account" if account_seen == 1 else "To Account")
        else:
            normalized.append(name.strip())
    return normalized


def preprocess_transaction_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Clean one transaction chunk without loading the full 475 MB file."""
    chunk = chunk.copy()
    chunk.columns = normalize_transaction_columns(chunk.columns)
    missing = set(TRANSACTION_COLUMNS) - set(chunk.columns)
    if missing:
        raise ValueError(f"Missing transaction columns: {sorted(missing)}")

    chunk["Timestamp"] = pd.to_datetime(chunk["Timestamp"], errors="coerce")
    for column in ["Amount Received", "Amount Paid", "Is Laundering"]:
        chunk[column] = pd.to_numeric(chunk[column], errors="coerce")
    for column in ["From Bank", "From Account", "To Bank", "To Account"]:
        chunk[column] = chunk[column].astype("string").str.strip()
    for column in ["Receiving Currency", "Payment Currency", "Payment Format"]:
        chunk[column] = chunk[column].astype("string").str.strip()

    chunk["Hour"] = chunk["Timestamp"].dt.hour
    chunk["Date"] = chunk["Timestamp"].dt.date.astype("string")
    chunk["Amount Difference"] = chunk["Amount Received"] - chunk["Amount Paid"]
    return chunk


def read_transaction_chunks(path: str, chunksize: int = 250_000):
    """Yield cleaned transaction chunks from a CSV file."""
    for chunk in pd.read_csv(path, chunksize=chunksize, low_memory=False):
        yield preprocess_transaction_chunk(chunk)
