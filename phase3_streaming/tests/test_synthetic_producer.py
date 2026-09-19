from datetime import datetime, timezone
import random

from phase3_streaming.src.synthetic_producer import build_synthetic_transaction, synthetic_records


def test_synthetic_transaction_matches_streaming_schema():
    record = build_synthetic_transaction(
        7,
        scenario="normal",
        rng=random.Random(1),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert record["transaction_id"] == "synthetic-000000000007"
    assert record["synthetic"] is True
    assert record["synthetic_scenario"] == "normal"
    assert record["Timestamp"] == "2026-01-01T00:00:00+00:00"
    assert record["Amount Received"] > 0
    assert record["From Account"] != record["To Account"]
    assert {"From Bank", "To Bank", "Payment Format"}.issubset(record)


def test_synthetic_records_are_reproducible_and_numbered():
    first = list(synthetic_records(count=3, scenario="high-value", seed=42, start_index=10))
    second = list(synthetic_records(count=3, scenario="high-value", seed=42, start_index=10))

    assert first == second
    assert [record["transaction_id"] for record in first] == [
        "synthetic-000000000010",
        "synthetic-000000000011",
        "synthetic-000000000012",
    ]
    assert all(record["synthetic_scenario"] == "high-value" for record in first)
    assert all(record["Amount Received"] > 25_000_000 for record in first)


def test_mule_chain_reuses_traceable_account_group():
    records = list(synthetic_records(count=6, scenario="mule-chain", seed=3))

    assert all("SYN-MULE-" in str(record["From Account"]) for record in records)
    assert len({str(record["From Account"]).split("-")[2] for record in records}) == 2
