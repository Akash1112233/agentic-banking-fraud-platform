import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "phase5_graph"))

from phase5_graph.app.graph_rows import transaction_to_graph_row  # noqa: E402
from phase5_graph.app.queries import account_history_parameters, counterparty_parameters, path_parameters  # noqa: E402


def test_transaction_row_preserves_account_and_risk_evidence():
    row = transaction_to_graph_row(
        {
            "transaction_id": "tx-000000000001",
            "event_timestamp": "2022-09-01T12:30:00",
            "from_bank": "001",
            "from_account": "A001",
            "to_bank": "002",
            "to_account": "B002",
            "amount_received": 100.0,
            "amount_paid": 95.0,
            "receiving_currency": "USD",
            "payment_currency": "USD",
            "payment_format": "ACH",
            "risk_probability": 0.91,
            "prediction": 1,
            "alert": True,
            "threshold": 0.55,
            "model": "xgboost",
        }
    )

    assert row["transaction_id"] == "tx-000000000001"
    assert row["from_account"] == "A001"
    assert row["to_account"] == "B002"
    assert row["risk_probability"] == 0.91
    assert row["alert"] is True


def test_transaction_row_converts_missing_values_to_none():
    row = transaction_to_graph_row({"transaction_id": "tx-empty"})

    assert row["transaction_id"] == "tx-empty"
    assert row["from_account"] is None
    assert row["amount_paid"] is None
    assert row["alert"] is False


def test_investigation_parameters_are_explicit_and_bounded():
    assert account_history_parameters("A001", 25) == {"account_id": "A001", "limit": 25}
    assert counterparty_parameters("A001", 10) == {"account_id": "A001", "limit": 10}
    assert path_parameters("A001", "B002", 3) == {
        "source_account": "A001",
        "target_account": "B002",
        "max_hops": 3,
    }


def test_query_limits_reject_invalid_values():
    for function in (account_history_parameters, counterparty_parameters):
        try:
            function("A001", 0)
        except ValueError:
            pass
        else:
            raise AssertionError("expected invalid limit to raise ValueError")

    try:
        path_parameters("A001", "B002", 0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected invalid hop count to raise ValueError")
