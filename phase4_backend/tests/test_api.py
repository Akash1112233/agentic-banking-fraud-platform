import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "phase4_backend"))

from app.main import create_app  # noqa: E402


@pytest.fixture
def client():
    app = create_app("sqlite+pysqlite:///:memory:")
    with TestClient(app) as test_client:
        yield test_client


def prediction_payload(alert: bool = True) -> dict:
    return {
        "transaction_id": "tx-phase4-001",
        "risk_probability": 0.91 if alert else 0.12,
        "prediction": 1 if alert else 0,
        "alert": alert,
        "model": "xgboost",
        "threshold": 0.55,
        "transaction": {
            "Timestamp": "2022-09-01 12:30:00",
            "From Bank": "001",
            "From Account": "A001",
            "To Bank": "002",
            "To Account": "B002",
            "Amount Received": 100.0,
            "Receiving Currency": "USD",
            "Amount Paid": 95.0,
            "Payment Currency": "USD",
            "Payment Format": "ACH",
        },
    }


def test_health_reports_database_ready(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ready"}


def test_prediction_is_persisted_and_creates_alert(client):
    response = client.post("/api/v1/predictions", json=prediction_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["transaction_id"] == "tx-phase4-001"
    assert body["alert_id"] is not None

    alerts = client.get("/api/v1/alerts").json()
    assert alerts["total"] == 1
    assert alerts["items"][0]["transaction_id"] == "tx-phase4-001"
    assert alerts["items"][0]["status"] == "open"


def test_non_alert_prediction_is_persisted_without_alert(client):
    response = client.post("/api/v1/predictions", json=prediction_payload(alert=False))

    assert response.status_code == 201
    assert response.json()["alert_id"] is None
    assert client.get("/api/v1/alerts").json()["total"] == 0


def test_probability_must_be_between_zero_and_one(client):
    payload = prediction_payload()
    payload["risk_probability"] = 1.5

    response = client.post("/api/v1/predictions", json=payload)

    assert response.status_code == 422


def test_investigation_endpoint_returns_persisted_evidence(client):
    client.post("/api/v1/predictions", json=prediction_payload())

    response = client.get("/api/v1/investigations/tx-phase4-001")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["evidence"]["alert"]["transaction_id"] == "tx-phase4-001"
    assert body["evidence"]["transaction"]["from_account"] == "A001"
    assert "graph evidence unavailable" in body["limitations"]
