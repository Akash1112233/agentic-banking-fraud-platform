from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from phase4_backend.app.models import Alert, Prediction, Transaction

from .app.graph_rows import transaction_to_graph_row
from .app.store import GraphStore


def postgres_rows(database_url: str) -> Iterator[dict[str, Any]]:
    engine = create_engine(database_url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine)
    try:
        with factory() as session:
            statement = (
                select(Transaction, Prediction, Alert)
                .join(Prediction, Prediction.transaction_id == Transaction.transaction_id)
                .outerjoin(Alert, Alert.transaction_id == Transaction.transaction_id)
                .order_by(Transaction.id)
            )
            for transaction, prediction, alert in session.execute(statement):
                yield transaction_to_graph_row(
                    {
                        "transaction_id": transaction.transaction_id,
                        "event_timestamp": transaction.event_timestamp,
                        "from_bank": transaction.from_bank,
                        "from_account": transaction.from_account,
                        "to_bank": transaction.to_bank,
                        "to_account": transaction.to_account,
                        "amount_received": transaction.amount_received,
                        "amount_paid": transaction.amount_paid,
                        "receiving_currency": transaction.receiving_currency,
                        "payment_currency": transaction.payment_currency,
                        "payment_format": transaction.payment_format,
                        "risk_probability": prediction.risk_probability,
                        "prediction": prediction.prediction,
                        "alert": prediction.alert,
                        "threshold": prediction.threshold,
                        "model": prediction.model,
                    }
                )
    finally:
        engine.dispose()


def load_graph(
    database_url: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    batch_size: int = 500,
) -> int:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    store = GraphStore(driver)
    try:
        store.ensure_schema()
        return store.write_rows(postgres_rows(database_url), batch_size=batch_size)
    finally:
        store.close()


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL must point to the Phase 4 PostgreSQL database")
    count = load_graph(
        database_url=database_url,
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.environ["NEO4J_PASSWORD"],
        batch_size=int(os.getenv("NEO4J_BATCH_SIZE", "500")),
    )
    print(f"Loaded {count:,} transaction rows into Neo4j")


if __name__ == "__main__":
    main()
