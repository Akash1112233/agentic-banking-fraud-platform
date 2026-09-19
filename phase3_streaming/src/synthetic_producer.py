"""Publish schema-valid synthetic AML transactions in real time."""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from typing import Iterator

from confluent_kafka import Producer

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
TRANSACTION_TOPIC = os.getenv("KAFKA_TRANSACTION_TOPIC", "aml.transactions")
SCENARIOS = ("normal", "high-value", "mule-chain")
CURRENCIES = ("USD", "EUR", "GBP", "Saudi Riyal")
PAYMENT_FORMATS = ("ACH", "Wire", "Cash", "Cheque")


def build_synthetic_transaction(
    index: int,
    scenario: str = "mixed",
    rng: random.Random | None = None,
    timestamp: datetime | None = None,
) -> dict[str, object]:
    """Build one source-shaped event; synthetic metadata is not used by inference."""
    if scenario not in {"mixed", *SCENARIOS}:
        raise ValueError(f"scenario must be mixed or one of {SCENARIOS}")
    rng = rng or random.Random()
    selected = rng.choice(SCENARIOS) if scenario == "mixed" else scenario
    event_time = timestamp or datetime.now(timezone.utc).replace(microsecond=0)

    if selected == "normal":
        amount_received = round(rng.uniform(250.0, 25_000.0), 2)
        amount_paid = round(amount_received * rng.uniform(0.96, 1.0), 2)
        currency = rng.choice(("USD", "EUR", "GBP"))
        payment_format = rng.choice(("Wire", "Cash", "Cheque"))
        from_account = f"SYN-NORMAL-F-{index:08d}"
        to_account = f"SYN-NORMAL-T-{index:08d}"
    elif selected == "high-value":
        amount_received = round(rng.uniform(25_000_000.0, 120_000_000.0), 2)
        amount_paid = round(amount_received * rng.uniform(0.35, 0.85), 2)
        currency = rng.choice(("Saudi Riyal", "EUR", "USD"))
        payment_format = rng.choice(("ACH", "Wire"))
        from_account = f"SYN-HIGH-F-{index:08d}"
        to_account = f"SYN-HIGH-T-{index:08d}"
    else:
        amount_received = round(rng.uniform(5_000_000.0, 60_000_000.0), 2)
        amount_paid = round(amount_received * rng.uniform(0.45, 0.9), 2)
        currency = rng.choice(("Saudi Riyal", "USD", "EUR"))
        payment_format = "ACH"
        # Repeated account prefixes make the scenario easy to trace in Neo4j.
        chain_id = index // 3
        from_account = f"SYN-MULE-{chain_id:06d}-{index % 3:02d}"
        to_account = f"SYN-MULE-{chain_id:06d}-{(index + 1) % 3:02d}"

    return {
        "transaction_id": f"synthetic-{index:012d}",
        "Timestamp": event_time.isoformat(),
        "From Bank": f"SYN-BANK-{rng.randint(1, 9):03d}",
        "From Account": from_account,
        "To Bank": f"SYN-BANK-{rng.randint(1, 9):03d}",
        "To Account": to_account,
        "Amount Received": amount_received,
        "Receiving Currency": currency,
        "Amount Paid": amount_paid,
        "Payment Currency": currency,
        "Payment Format": payment_format,
        # Audit metadata is retained in PostgreSQL raw_payload but ignored by model features.
        "synthetic": True,
        "synthetic_scenario": selected,
    }


def synthetic_records(
    count: int | None = None,
    scenario: str = "mixed",
    seed: int | None = None,
    start_index: int = 0,
) -> Iterator[dict[str, object]]:
    """Yield records forever when count is None, otherwise yield exactly count records."""
    rng = random.Random(seed)
    index = start_index
    while count is None or index < start_index + count:
        yield build_synthetic_transaction(index, scenario=scenario, rng=rng)
        index += 1


def publish(
    count: int | None = 20,
    interval_seconds: float = 1.0,
    scenario: str = "mixed",
    seed: int | None = None,
    start_index: int = 0,
) -> int:
    """Publish synthetic events at a human-visible real-time interval."""
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})
    published = 0

    def delivery_report(error, message) -> None:
        if error is not None:
            print(f"Delivery failed: {error}")

    try:
        for record in synthetic_records(count, scenario, seed, start_index):
            producer.produce(
                TRANSACTION_TOPIC,
                key=str(record["transaction_id"]),
                value=json.dumps(record),
                on_delivery=delivery_report,
            )
            producer.poll(0)
            published += 1
            print(
                f"Published {record['transaction_id']} "
                f"scenario={record['synthetic_scenario']} "
                f"amount={record['Amount Received']}"
            )
            producer.flush()
            if interval_seconds > 0:
                time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("Stopping synthetic producer...")
    finally:
        producer.flush()
    print(f"Published {published} synthetic transactions to {TRANSACTION_TOPIC}")
    return published


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=20, help="Number of events; omit --count for continuous mode")
    parser.add_argument("--continuous", action="store_true", help="Publish until Ctrl+C")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between events")
    parser.add_argument("--scenario", choices=("mixed", *SCENARIOS), default="mixed")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start-index", type=int, default=0)
    args = parser.parse_args()
    count = None if args.continuous else args.count
    publish(count, args.interval, args.scenario, args.seed, args.start_index)


if __name__ == "__main__":
    main()
