from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=1, max_length=128)
    risk_probability: float = Field(ge=0.0, le=1.0)
    prediction: int = Field(ge=0, le=1)
    alert: bool
    model: str = Field(min_length=1, max_length=128)
    threshold: float = Field(gt=0.0, lt=1.0)
    transaction: dict[str, Any] = Field(default_factory=dict)


class PredictionResponse(BaseModel):
    prediction_id: int
    transaction_id: str
    alert_id: int | None
    status: str


class AlertResponse(BaseModel):
    id: int
    transaction_id: str
    risk_probability: float
    status: str
    created_at: datetime


class AlertListResponse(BaseModel):
    total: int
    items: list[AlertResponse]


class HealthResponse(BaseModel):
    status: str
    database: str
