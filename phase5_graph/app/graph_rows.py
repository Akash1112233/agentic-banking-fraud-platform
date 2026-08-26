from __future__ import annotations

from datetime import datetime
from typing import Any


GRAPH_ROW_FIELDS = (
    "transaction_id",
    "event_timestamp",
    "from_bank",
    "from_account",
    "to_bank",
    "to_account",
    "amount_received",
    "amount_paid",
    "receiving_currency",
    "payment_currency",
    "payment_format",
    "risk_probability",
    "prediction",
    "alert",
    "threshold",
    "model",
)


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def transaction_to_graph_row(source: dict[str, Any]) -> dict[str, Any]:
    transaction_id = source.get("transaction_id")
    if not transaction_id:
        raise ValueError("transaction_id is required")
    timestamp = source.get("event_timestamp")
    if isinstance(timestamp, datetime):
        timestamp = timestamp.isoformat()
    return {
        "transaction_id": str(transaction_id),
        "event_timestamp": str(timestamp) if timestamp is not None else None,
        "from_bank": None if source.get("from_bank") is None else str(source["from_bank"]),
        "from_account": None if source.get("from_account") is None else str(source["from_account"]),
        "to_bank": None if source.get("to_bank") is None else str(source["to_bank"]),
        "to_account": None if source.get("to_account") is None else str(source["to_account"]),
        "amount_received": _optional_float(source.get("amount_received")),
        "amount_paid": _optional_float(source.get("amount_paid")),
        "receiving_currency": source.get("receiving_currency"),
        "payment_currency": source.get("payment_currency"),
        "payment_format": source.get("payment_format"),
        "risk_probability": _optional_float(source.get("risk_probability")),
        "prediction": int(source["prediction"]) if source.get("prediction") is not None else None,
        "alert": bool(source.get("alert", False)),
        "threshold": _optional_float(source.get("threshold")),
        "model": source.get("model"),
    }
