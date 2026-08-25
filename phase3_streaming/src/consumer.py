"""Consume Kafka transactions, score them, and publish AML alerts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from confluent_kafka import Consumer, KafkaError, KafkaException, Producer

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
from inference import DEFAULT_MODEL_PATH, TransactionScorer  # noqa: E402

ROOT = SRC.parents[1]
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
TRANSACTION_TOPIC = os.getenv("KAFKA_TRANSACTION_TOPIC", "aml.transactions")
PREDICTION_TOPIC = os.getenv("KAFKA_PREDICTION_TOPIC", "aml.predictions")
ALERT_TOPIC = os.getenv("KAFKA_ALERT_TOPIC", "aml.alerts")
DEAD_LETTER_TOPIC = os.getenv("KAFKA_DEAD_LETTER_TOPIC", "aml.dead_letter")
PREDICTIONS_API_URL = os.getenv("PREDICTIONS_API_URL", "").strip()
OUTPUT_DIR = ROOT / "phase3_streaming" / "outputs"


def _persist_to_api(result: dict[str, object], transaction: dict[str, object]) -> None:
    if not PREDICTIONS_API_URL:
        return
    payload = {**result, "transaction": transaction}
    request = Request(
        PREDICTIONS_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if response.status >= 300:
                raise RuntimeError(f"prediction API returned HTTP {response.status}")
    except (HTTPError, URLError) as error:
        raise RuntimeError(f"prediction API request failed: {error}") from error


def _publish(producer: Producer, topic: str, value: dict[str, object], key: object = None) -> None:
    producer.produce(topic, key=str(key) if key is not None else None, value=json.dumps(value))
    producer.poll(0)


def consume(
    model_path: str | Path = DEFAULT_MODEL_PATH,
    threshold: float = 0.55,
    max_messages: int | None = None,
) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scorer = TransactionScorer(model_path=model_path, threshold=threshold)
    consumer = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "group.id": os.getenv("KAFKA_CONSUMER_GROUP", "aml-scorer-v1"),
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})
    consumer.subscribe([TRANSACTION_TOPIC])
    count = 0
    predictions_path = OUTPUT_DIR / "predictions.jsonl"
    alerts_path = OUTPUT_DIR / "alerts.jsonl"
    dead_letter_path = OUTPUT_DIR / "dead_letter.jsonl"

    try:
        with predictions_path.open("a", encoding="utf-8") as predictions_file, alerts_path.open(
            "a", encoding="utf-8"
        ) as alerts_file, dead_letter_path.open("a", encoding="utf-8") as dead_letter_file:
            while max_messages is None or count < max_messages:
                message = consumer.poll(1.0)
                if message is None:
                    continue
                if message.error():
                    if message.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaException(message.error())
                try:
                    record = json.loads(message.value().decode("utf-8"))
                    result = scorer.score(record)
                    _persist_to_api(result, record)
                    predictions_file.write(json.dumps(result) + "\n")
                    predictions_file.flush()
                    _publish(producer, PREDICTION_TOPIC, result, result.get("transaction_id"))
                    if result["alert"]:
                        alerts_file.write(json.dumps(result) + "\n")
                        alerts_file.flush()
                        _publish(producer, ALERT_TOPIC, result, result.get("transaction_id"))
                    producer.flush()
                    consumer.commit(message=message, asynchronous=False)
                    count += 1
                    if count % 100 == 0:
                        print(f"Scored {count:,} transactions")
                except Exception as error:
                    dead_letter = {
                        "error_type": type(error).__name__,
                        "error": str(error),
                        "raw_value": message.value().decode("utf-8", errors="replace"),
                    }
                    dead_letter_file.write(json.dumps(dead_letter) + "\n")
                    dead_letter_file.flush()
                    _publish(producer, DEAD_LETTER_TOPIC, dead_letter)
                    producer.flush()
                    consumer.commit(message=message, asynchronous=False)
                    print(f"Sent invalid message to {DEAD_LETTER_TOPIC}: {error}", file=sys.stderr)
    except KeyboardInterrupt:
        print("Stopping consumer...")
    finally:
        producer.flush()
        consumer.close()
    print(f"Consumed and scored {count:,} transactions")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--threshold", type=float, default=float(os.getenv("AML_ALERT_THRESHOLD", "0.55")))
    parser.add_argument("--max-messages", type=int, default=None)
    args = parser.parse_args()
    consume(args.model_path, args.threshold, args.max_messages)


if __name__ == "__main__":
    main()
