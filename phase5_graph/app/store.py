from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from neo4j import Driver


CONSTRAINTS = (
    "CREATE CONSTRAINT account_id_unique IF NOT EXISTS FOR (account:Account) REQUIRE account.account_id IS UNIQUE",
    "CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (transaction:Transaction) REQUIRE transaction.transaction_id IS UNIQUE",
)


WRITE_BATCH_CYPHER = """
UNWIND $rows AS row
MERGE (sender:Account {account_id: row.from_account})
  ON CREATE SET sender.bank_id = row.from_bank
  ON MATCH SET sender.bank_id = coalesce(sender.bank_id, row.from_bank)
MERGE (receiver:Account {account_id: row.to_account})
  ON CREATE SET receiver.bank_id = row.to_bank
  ON MATCH SET receiver.bank_id = coalesce(receiver.bank_id, row.to_bank)
MERGE (transaction:Transaction {transaction_id: row.transaction_id})
SET transaction.timestamp = row.event_timestamp,
    transaction.amount_received = row.amount_received,
    transaction.amount_paid = row.amount_paid,
    transaction.receiving_currency = row.receiving_currency,
    transaction.payment_currency = row.payment_currency,
    transaction.payment_format = row.payment_format,
    transaction.risk_probability = row.risk_probability,
    transaction.prediction = row.prediction,
    transaction.alert = row.alert,
    transaction.threshold = row.threshold,
    transaction.model = row.model
MERGE (sender)-[:SENT]->(transaction)
MERGE (transaction)-[:RECEIVED_BY]->(receiver)
"""


class GraphStore:
    def __init__(self, driver: Driver):
        self.driver = driver

    def ensure_schema(self) -> None:
        with self.driver.session() as session:
            for statement in CONSTRAINTS:
                session.run(statement).consume()

    @staticmethod
    def _write_batch(tx: Any, rows: list[dict[str, Any]]) -> None:
        tx.run(WRITE_BATCH_CYPHER, rows=rows).consume()

    def write_rows(self, rows: Iterable[dict[str, Any]], batch_size: int = 500) -> int:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        total = 0
        batch: list[dict[str, Any]] = []
        with self.driver.session() as session:
            for row in rows:
                if not row.get("from_account") or not row.get("to_account"):
                    continue
                batch.append(row)
                if len(batch) >= batch_size:
                    session.execute_write(self._write_batch, batch)
                    total += len(batch)
                    batch = []
            if batch:
                session.execute_write(self._write_batch, batch)
                total += len(batch)
        return total

    def close(self) -> None:
        self.driver.close()
