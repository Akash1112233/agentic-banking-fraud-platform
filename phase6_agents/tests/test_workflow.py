from datetime import datetime, timezone

import pytest

from phase6_agents.evidence import InMemoryEvidenceProvider
from phase6_agents.workflow import run_investigation


def provider() -> InMemoryEvidenceProvider:
    return InMemoryEvidenceProvider(
        alerts={"tx-001": {"transaction_id": "tx-001", "status": "open", "risk_probability": 0.91}},
        transactions={"tx-001": {"transaction_id": "tx-001", "from_account": "A1", "to_account": "A2", "amount_paid": 900.0}},
        graph={"tx-001": {"counterparties": ["A2"], "paths": [{"nodes": ["Account:A1", "Transaction:tx-001", "Account:A2"], "hops": 2}]}},
        explanations={"tx-001": {"top_positive": [{"feature": "amount_paid", "contribution": 1.2}], "top_negative": []}},
    )


def test_complete_investigation_contains_only_retrieved_evidence():
    result = run_investigation("tx-001", provider())

    assert result["status"] == "complete"
    assert result["transaction_id"] == "tx-001"
    assert result["evidence"]["alert"]["risk_probability"] == 0.91
    assert result["evidence"]["graph"]["paths"][0]["hops"] == 2
    assert result["evidence"]["explanation"]["top_positive"][0]["feature"] == "amount_paid"
    assert result["limitations"] == []


def test_missing_optional_sources_are_reported_as_unavailable():
    result = run_investigation(
        "tx-002",
        InMemoryEvidenceProvider(
            alerts={"tx-002": {"transaction_id": "tx-002", "status": "open"}},
            transactions={"tx-002": {"transaction_id": "tx-002"}},
        ),
    )

    assert result["status"] == "partial"
    assert "graph evidence unavailable" in result["limitations"]
    assert "model explanation unavailable" in result["limitations"]
    assert result["evidence"]["graph"] is None


def test_missing_alert_does_not_create_a_report_from_assumptions():
    result = run_investigation("unknown", InMemoryEvidenceProvider())

    assert result["status"] == "not_found"
    assert result["evidence"] == {"alert": None, "transaction": None, "graph": None, "explanation": None}
    assert "alert not found" in result["limitations"]


def test_workflow_rejects_blank_transaction_id():
    with pytest.raises(ValueError, match="transaction_id is required"):
        run_investigation("", provider())


def test_llm_interpreter_receives_grounded_evidence_and_returns_analysis():
    class FakeInterpreter:
        def __init__(self):
            self.received = None

        def interpret(self, evidence, limitations):
            self.received = (evidence, limitations)
            return {
                "conclusion": "High priority review",
                "rationale": "The risk score exceeds the configured threshold.",
                "recommended_action": "Review account history and counterparties.",
                "confidence": "high",
                "evidence_used": ["alert", "transaction", "explanation"],
                "limitations": limitations,
            }

    interpreter = FakeInterpreter()
    result = run_investigation("tx-001", provider(), interpreter)

    assert result["llm_status"] == "available"
    assert result["llm_interpretation"]["conclusion"] == "High priority review"
    assert interpreter.received[0]["alert"]["risk_probability"] == 0.91
