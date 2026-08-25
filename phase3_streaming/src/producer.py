"""Publish local AML transaction records to a Kafka topic."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterator

import pandas as pd
from confluent_kafka import Producer

SRC = Path(__file__).resolve().parents[2] / "phase1_data_foundation" / "src"
sys.path.insert(0, str(SRC))
from preprocess import TRANSACTION_COLUMNS, read_transaction_chunks  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "data" / "raw" / "HI-Small_Trans.csv"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
TRANSACTION_TOPIC = os.getenv("KAFKA_TRANSACTION_TOPIC", "aml.transactions")


def _json_value(value: object) -> object:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def transaction_records(csv_path: str | Path, limit: int | None = None) -> Iterator[dict[str, object]]:
    """Yield JSON-safe normalized records without loading the full CSV."""
    emitted = 0
    for chunk in read_transaction_chunks(str(csv_path)):
        for row_number, (_, row) in enumerate(chunk.iterrows()):
            record = {column: _json_value(row[column]) for column in TRANSACTION_COLUMNS}
            record["transaction_id"] = f"tx-{emitted:012d}"
            yield record
            emitted += 1
            if limit is not None and emitted >= limit:
                return


def publish(csv_path: str | Path, limit: int | None = None) -> int:
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})
    count = 0

    def delivery_report(error, message) -> None:
        if error is not None:
            print(f"Delivery failed: {error}", file=sys.stderr)

    for record in transaction_records(csv_path, limit=limit):
        producer.produce(
            TRANSACTION_TOPIC,
            key=str(record["transaction_id"]),
            value=json.dumps(record),
            on_delivery=delivery_report,
        )
        producer.poll(0)
        count += 1
        if count % 1000 == 0:
            print(f"Published {count:,} transactions")
    producer.flush()
    print(f"Published {count:,} transactions to {TRANSACTION_TOPIC}")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    publish(args.csv_path, args.limit)


if __name__ == "__main__":
    main()
