from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol


class EvidenceProvider(Protocol):
    def get_alert(self, transaction_id: str) -> dict[str, Any] | None: ...

    def get_transaction(self, transaction_id: str) -> dict[str, Any] | None: ...

    def get_graph_evidence(self, transaction: dict[str, Any]) -> dict[str, Any] | None: ...

    def get_explanation(self, transaction_id: str) -> dict[str, Any] | None: ...

    def get_account_history(self, account_id: str, limit: int = 100) -> list[dict[str, Any]]: ...

    def get_counterparties(self, account_id: str, limit: int = 100) -> list[dict[str, Any]]: ...

    def get_paths(self, source_account: str, target_account: str, max_hops: int = 3) -> list[dict[str, Any]]: ...


class InMemoryEvidenceProvider:
    """Deterministic provider for tests and local workflow demonstrations."""

    def __init__(
        self,
        alerts: dict[str, dict[str, Any]] | None = None,
        transactions: dict[str, dict[str, Any]] | None = None,
        graph: dict[str, dict[str, Any]] | None = None,
        explanations: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.alerts = alerts or {}
        self.transactions = transactions or {}
        self.graph = graph or {}
        self.explanations = explanations or {}

    def get_alert(self, transaction_id: str) -> dict[str, Any] | None:
        value = self.alerts.get(transaction_id)
        return deepcopy(value) if value is not None else None

    def get_transaction(self, transaction_id: str) -> dict[str, Any] | None:
        value = self.transactions.get(transaction_id)
        return deepcopy(value) if value is not None else None

    def get_graph_evidence(self, transaction: dict[str, Any]) -> dict[str, Any] | None:
        transaction_id = str(transaction.get("transaction_id", ""))
        value = self.graph.get(transaction_id)
        return deepcopy(value) if value is not None else None

    def get_explanation(self, transaction_id: str) -> dict[str, Any] | None:
        value = self.explanations.get(transaction_id)
        return deepcopy(value) if value is not None else None

    def get_account_history(self, account_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return []

    def get_counterparties(self, account_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return []

    def get_paths(self, source_account: str, target_account: str, max_hops: int = 3) -> list[dict[str, Any]]:
        return []
