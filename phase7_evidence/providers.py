from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from phase4_backend.app.models import Alert, Prediction, Transaction
from phase5_graph.app.queries import fetch_account_history, fetch_counterparties, fetch_paths


class PostgresEvidenceProvider:
    def __init__(self, session_factory: Callable[[], Session], model_explainer: Any | None = None) -> None:
        self.session_factory = session_factory
        self.model_explainer = model_explainer

    def get_alert(self, transaction_id: str) -> dict[str, Any] | None:
        with self.session_factory() as db:
            alert = db.scalar(select(Alert).where(Alert.transaction_id == transaction_id))
            if alert is None:
                return None
            return {
                "id": alert.id,
                "transaction_id": alert.transaction_id,
                "risk_probability": alert.risk_probability,
                "status": alert.status,
                "analyst_notes": alert.analyst_notes,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }

    def get_transaction(self, transaction_id: str) -> dict[str, Any] | None:
        with self.session_factory() as db:
            transaction = db.scalar(select(Transaction).where(Transaction.transaction_id == transaction_id))
            if transaction is None:
                return None
            prediction = db.scalar(select(Prediction).where(Prediction.transaction_id == transaction_id))
            return {
                "transaction_id": transaction.transaction_id,
                "event_timestamp": transaction.event_timestamp.isoformat() if transaction.event_timestamp else None,
                "from_bank": transaction.from_bank,
                "from_account": transaction.from_account,
                "to_bank": transaction.to_bank,
                "to_account": transaction.to_account,
                "amount_received": transaction.amount_received,
                "amount_paid": transaction.amount_paid,
                "receiving_currency": transaction.receiving_currency,
                "payment_currency": transaction.payment_currency,
                "payment_format": transaction.payment_format,
                "raw_payload": transaction.raw_payload,
                "prediction": (
                    {
                        "risk_probability": prediction.risk_probability,
                        "prediction": prediction.prediction,
                        "alert": prediction.alert,
                        "model": prediction.model,
                        "threshold": prediction.threshold,
                        "scored_at": prediction.scored_at.isoformat() if prediction.scored_at else None,
                    }
                    if prediction is not None
                    else None
                ),
            }

    def get_graph_evidence(self, transaction: dict[str, Any]) -> None:
        return None

    def get_explanation(self, transaction_id: str) -> dict[str, Any] | None:
        with self.session_factory() as db:
            prediction = db.scalar(select(Prediction).where(Prediction.transaction_id == transaction_id))
            transaction = db.scalar(select(Transaction).where(Transaction.transaction_id == transaction_id))
            if prediction is None:
                return None
            if self.model_explainer is not None and transaction is not None:
                return self.model_explainer.explain(transaction.raw_payload)
            return {
                "source": "postgresql",
                "risk_probability": prediction.risk_probability,
                "prediction": prediction.prediction,
                "model": prediction.model,
                "threshold": prediction.threshold,
                "shap": None,
            }


class Neo4jEvidenceProvider:
    def __init__(self, driver: Any) -> None:
        self.driver = driver

    def get_graph_evidence(self, transaction: dict[str, Any]) -> dict[str, Any] | None:
        transaction_id = str(transaction["transaction_id"])
        query = """
        MATCH p=(sender:Account)-[:SENT]->(t:Transaction {transaction_id: $transaction_id})-[:RECEIVED_BY]->(receiver:Account)
        RETURN sender.account_id AS sender,
               sender.bank_id AS sender_bank,
               receiver.account_id AS receiver,
               receiver.bank_id AS receiver_bank,
               length(p) AS hops
        """
        with self.driver.session() as session:
            rows = [record.data() for record in session.run(query, transaction_id=transaction_id)]
        if not rows:
            return None
        return {"paths": rows, "source": "neo4j"}

    def get_account_history(self, account_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            return fetch_account_history(session, account_id, limit)

    def get_counterparties(self, account_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            return fetch_counterparties(session, account_id, limit)

    def get_paths(self, source_account: str, target_account: str, max_hops: int = 3) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            return fetch_paths(session, source_account, target_account, max_hops)

    def get_alert(self, transaction_id: str) -> None:
        return None

    def get_transaction(self, transaction_id: str) -> None:
        return None

    def get_explanation(self, transaction_id: str) -> None:
        return None


class CompositeEvidenceProvider:
    def __init__(self, postgres: PostgresEvidenceProvider, neo4j: Neo4jEvidenceProvider | None = None) -> None:
        self.postgres = postgres
        self.neo4j = neo4j

    def get_alert(self, transaction_id: str) -> dict[str, Any] | None:
        return self.postgres.get_alert(transaction_id)

    def get_transaction(self, transaction_id: str) -> dict[str, Any] | None:
        return self.postgres.get_transaction(transaction_id)

    def get_graph_evidence(self, transaction: dict[str, Any]) -> dict[str, Any] | None:
        return self.neo4j.get_graph_evidence(transaction) if self.neo4j else None

    def get_explanation(self, transaction_id: str) -> dict[str, Any] | None:
        return self.postgres.get_explanation(transaction_id)

    def get_account_history(self, account_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return self.neo4j.get_account_history(account_id, limit) if self.neo4j else []

    def get_counterparties(self, account_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return self.neo4j.get_counterparties(account_id, limit) if self.neo4j else []

    def get_paths(self, source_account: str, target_account: str, max_hops: int = 3) -> list[dict[str, Any]]:
        return self.neo4j.get_paths(source_account, target_account, max_hops) if self.neo4j else []
