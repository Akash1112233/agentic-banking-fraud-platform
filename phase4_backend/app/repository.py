from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Alert, Prediction, Transaction
from .schemas import PredictionRequest


def _text(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value is not None and value != "":
            return str(value)
    return None


def _float(payload: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = payload.get(key)
        if value is not None and value != "":
            return float(value)
    return None


def _timestamp(payload: dict[str, Any]) -> datetime | None:
    value = payload.get("Timestamp")
    if value is None or value == "":
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed


def persist_prediction(db: Session, request: PredictionRequest) -> tuple[Prediction, Alert | None]:
    payload = request.transaction
    transaction = db.scalar(select(Transaction).where(Transaction.transaction_id == request.transaction_id))
    if transaction is None:
        transaction = Transaction(
            transaction_id=request.transaction_id,
            event_timestamp=_timestamp(payload),
            from_bank=_text(payload, "From Bank"),
            from_account=_text(payload, "From Account", "Account"),
            to_bank=_text(payload, "To Bank"),
            to_account=_text(payload, "To Account", "Account.1"),
            amount_received=_float(payload, "Amount Received"),
            amount_paid=_float(payload, "Amount Paid"),
            receiving_currency=_text(payload, "Receiving Currency"),
            payment_currency=_text(payload, "Payment Currency"),
            payment_format=_text(payload, "Payment Format"),
            raw_payload=payload,
        )
        db.add(transaction)
        db.flush()

    prediction = db.scalar(select(Prediction).where(Prediction.transaction_id == request.transaction_id))
    if prediction is None:
        prediction = Prediction(
            transaction_id=request.transaction_id,
            risk_probability=request.risk_probability,
            prediction=request.prediction,
            alert=request.alert,
            model=request.model,
            threshold=request.threshold,
        )
        db.add(prediction)
    else:
        prediction.risk_probability = request.risk_probability
        prediction.prediction = request.prediction
        prediction.alert = request.alert
        prediction.model = request.model
        prediction.threshold = request.threshold
    db.flush()

    alert_record = db.scalar(select(Alert).where(Alert.transaction_id == request.transaction_id))
    if request.alert and alert_record is None:
        alert_record = Alert(
            transaction_id=request.transaction_id,
            prediction_id=prediction.id,
            risk_probability=request.risk_probability,
            status="open",
        )
        db.add(alert_record)
    elif alert_record is not None:
        alert_record.risk_probability = request.risk_probability
    db.commit()
    db.refresh(prediction)
    if alert_record is not None:
        db.refresh(alert_record)
    return prediction, alert_record
