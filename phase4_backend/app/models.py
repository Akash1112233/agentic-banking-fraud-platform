from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    event_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    from_bank: Mapped[str | None] = mapped_column(String(128), nullable=True)
    from_account: Mapped[str | None] = mapped_column(String(256), nullable=True)
    to_bank: Mapped[str | None] = mapped_column(String(128), nullable=True)
    to_account: Mapped[str | None] = mapped_column(String(256), nullable=True)
    amount_received: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_paid: Mapped[float | None] = mapped_column(Float, nullable=True)
    receiving_currency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_currency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_format: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    prediction: Mapped["Prediction | None"] = relationship(back_populates="transaction", uselist=False)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.transaction_id"), unique=True, index=True)
    risk_probability: Mapped[float] = mapped_column(Float)
    prediction: Mapped[int] = mapped_column(Integer)
    alert: Mapped[bool] = mapped_column(default=False)
    model: Mapped[str] = mapped_column(String(128))
    threshold: Mapped[float] = mapped_column(Float)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    transaction: Mapped[Transaction] = relationship(back_populates="prediction")
    alert_record: Mapped["Alert | None"] = relationship(back_populates="prediction", uselist=False)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.transaction_id"), unique=True, index=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), unique=True)
    risk_probability: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    prediction: Mapped[Prediction] = relationship(back_populates="alert_record")


def create_database_engine(database_url: str):
    kwargs: dict[str, Any] = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            from sqlalchemy.pool import StaticPool

            kwargs["poolclass"] = StaticPool
    return create_engine(database_url, **kwargs)
