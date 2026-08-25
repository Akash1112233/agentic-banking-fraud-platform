from pathlib import Path
import os

from fastapi import Depends, FastAPI, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Alert, Base, create_database_engine
from .repository import persist_prediction
from .schemas import AlertListResponse, AlertResponse, HealthResponse, PredictionRequest, PredictionResponse

DEFAULT_DATABASE_URL = "sqlite:///./phase4_backend/aml_platform.db"


def create_app(database_url: str | None = None) -> FastAPI:
    url = database_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    engine = create_database_engine(url)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    app = FastAPI(title="Agentic AML Platform API", version="0.1.0")

    def get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    @app.get("/health", response_model=HealthResponse)
    def health(db: Session = Depends(get_db)):
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ready"}

    @app.post("/api/v1/predictions", response_model=PredictionResponse, status_code=201)
    def create_prediction(request: PredictionRequest, db: Session = Depends(get_db)):
        prediction, alert = persist_prediction(db, request)
        return {
            "prediction_id": prediction.id,
            "transaction_id": prediction.transaction_id,
            "alert_id": alert.id if alert else None,
            "status": "alert_created" if alert else "scored",
        }

    @app.get("/api/v1/alerts", response_model=AlertListResponse)
    def list_alerts(
        status: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=1000),
        db: Session = Depends(get_db),
    ):
        statement = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
        if status:
            statement = statement.where(Alert.status == status)
        items = list(db.scalars(statement))
        total_statement = select(func.count(Alert.id))
        if status:
            total_statement = total_statement.where(Alert.status == status)
        total = db.scalar(total_statement) or 0
        return {"total": total, "items": items}

    return app


app = create_app()
