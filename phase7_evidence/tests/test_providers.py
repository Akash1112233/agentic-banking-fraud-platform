from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from phase4_backend.app.models import Alert, Base, Prediction, Transaction
from phase7_evidence.providers import PostgresEvidenceProvider


def make_provider():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        transaction = Transaction(
            transaction_id="tx-db-1",
            from_account="A1",
            to_account="A2",
            amount_paid=100.0,
            raw_payload={"From Account": "A1"},
        )
        db.add(transaction)
        db.flush()
        prediction = Prediction(
            transaction_id="tx-db-1",
            risk_probability=0.8,
            prediction=1,
            alert=True,
            model="xgboost",
            threshold=0.55,
            scored_at=datetime.now(timezone.utc),
        )
        db.add(prediction)
        db.flush()
        db.add(Alert(transaction_id="tx-db-1", prediction_id=prediction.id, risk_probability=0.8, status="open"))
        db.commit()
    return PostgresEvidenceProvider(factory)


def test_postgres_provider_returns_alert_and_transaction_evidence():
    provider = make_provider()

    alert = provider.get_alert("tx-db-1")
    transaction = provider.get_transaction("tx-db-1")
    explanation = provider.get_explanation("tx-db-1")

    assert alert["status"] == "open"
    assert transaction["from_account"] == "A1"
    assert transaction["prediction"]["threshold"] == 0.55
    assert explanation["risk_probability"] == 0.8


def test_postgres_provider_returns_none_for_unknown_transaction():
    provider = make_provider()

    assert provider.get_alert("unknown") is None
    assert provider.get_transaction("unknown") is None
    assert provider.get_explanation("unknown") is None
