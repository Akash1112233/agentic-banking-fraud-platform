from fastapi.testclient import TestClient

from phase4_backend.app.main import create_app
from phase6_agents.evidence import InMemoryEvidenceProvider


def test_alert_to_evidence_grounded_investigation_report():
    provider = InMemoryEvidenceProvider(
        alerts={"tx-e2e": {"transaction_id": "tx-e2e", "status": "open", "risk_probability": 0.88}},
        transactions={"tx-e2e": {"transaction_id": "tx-e2e", "from_account": "A1", "to_account": "A2", "amount_paid": 250.0}},
        graph={"tx-e2e": {"source": "neo4j", "paths": [{"sender": "A1", "receiver": "A2", "hops": 2}]}},
        explanations={"tx-e2e": {"source": "shap", "top_positive": [{"feature": "amount_paid", "contribution": 0.7}], "top_negative": []}},
    )
    client = TestClient(create_app("sqlite+pysqlite:///:memory:", evidence_provider=provider))

    response = client.get("/api/v1/investigations/tx-e2e")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "complete"
    assert body["evidence"]["graph"]["source"] == "neo4j"
    assert body["evidence"]["explanation"]["source"] == "shap"
    assert body["limitations"] == []
