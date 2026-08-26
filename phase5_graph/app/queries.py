from __future__ import annotations

from typing import Any


def _limit(value: int) -> int:
    if not 1 <= value <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    return value


def _hops(value: int) -> int:
    if not 1 <= value <= 6:
        raise ValueError("max_hops must be between 1 and 6")
    return value


def account_history_parameters(account_id: str, limit: int = 100) -> dict[str, Any]:
    if not account_id:
        raise ValueError("account_id is required")
    return {"account_id": str(account_id), "limit": _limit(limit)}


def counterparty_parameters(account_id: str, limit: int = 100) -> dict[str, Any]:
    if not account_id:
        raise ValueError("account_id is required")
    return {"account_id": str(account_id), "limit": _limit(limit)}


def path_parameters(source_account: str, target_account: str, max_hops: int = 3) -> dict[str, Any]:
    if not source_account or not target_account:
        raise ValueError("source_account and target_account are required")
    return {
        "source_account": str(source_account),
        "target_account": str(target_account),
        "max_hops": _hops(max_hops),
    }


ACCOUNT_HISTORY_CYPHER = """
MATCH (account:Account {account_id: $account_id})-[rel:SENT|RECEIVED_BY]-(transaction:Transaction)
RETURN transaction.transaction_id AS transaction_id,
       transaction.timestamp AS timestamp,
       transaction.amount_paid AS amount_paid,
       transaction.payment_currency AS payment_currency,
       transaction.risk_probability AS risk_probability,
       transaction.alert AS alert,
       type(rel) AS relationship
ORDER BY transaction.timestamp DESC
LIMIT $limit
"""


COUNTERPARTIES_CYPHER = """
MATCH (account:Account {account_id: $account_id})-[:SENT|RECEIVED_BY]-(transaction:Transaction)-[:SENT|RECEIVED_BY]-(counterparty:Account)
WHERE counterparty.account_id <> account.account_id
RETURN DISTINCT counterparty.account_id AS account_id,
       counterparty.bank_id AS bank_id,
       count(DISTINCT transaction) AS transaction_count
ORDER BY transaction_count DESC
LIMIT $limit
"""


def path_cypher(max_hops: int) -> str:
    hops = _hops(max_hops)
    return f"""
MATCH path=(source:Account {{account_id: $source_account}})-[*1..{hops}]-(target:Account {{account_id: $target_account}})
RETURN [node IN nodes(path) | labels(node)[0] + ':' + coalesce(node.account_id, node.transaction_id)] AS nodes,
       length(path) AS hops
ORDER BY hops ASC
LIMIT 25
"""


def fetch_account_history(session: Any, account_id: str, limit: int = 100) -> list[dict[str, Any]]:
    result = session.run(ACCOUNT_HISTORY_CYPHER, account_history_parameters(account_id, limit))
    return [record.data() for record in result]


def fetch_counterparties(session: Any, account_id: str, limit: int = 100) -> list[dict[str, Any]]:
    result = session.run(COUNTERPARTIES_CYPHER, counterparty_parameters(account_id, limit))
    return [record.data() for record in result]


def fetch_paths(session: Any, source_account: str, target_account: str, max_hops: int = 3) -> list[dict[str, Any]]:
    params = path_parameters(source_account, target_account, max_hops)
    result = session.run(path_cypher(params["max_hops"]), params)
    return [record.data() for record in result]
