from pathlib import Path
import os

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from phase6_agents.workflow import run_investigation
from phase7_evidence.providers import CompositeEvidenceProvider, Neo4jEvidenceProvider, PostgresEvidenceProvider

from .models import Alert, Base, create_database_engine
from .repository import persist_prediction
from .schemas import AlertListResponse, AlertResponse, HealthResponse, PredictionRequest, PredictionResponse

DEFAULT_DATABASE_URL = "sqlite:///./phase4_backend/aml_platform.db"


def create_app(database_url: str | None = None, evidence_provider=None) -> FastAPI:
    url = database_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    engine = create_database_engine(url)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    app = FastAPI(title="Agentic AML Platform API", version="0.1.0")

    if evidence_provider is None:
        model_explainer = None
        model_path = Path(__file__).resolve().parents[2] / "phase2_ml_models" / "models" / "best_model_xgboost.joblib"
        if model_path.exists():
            from phase8_explainability.explainer import ModelExplainer

            model_explainer = ModelExplainer(model_path)
        postgres_provider = PostgresEvidenceProvider(session_factory, model_explainer=model_explainer)
        neo4j_uri = os.getenv("NEO4J_URI")
        if neo4j_uri:
            from neo4j import GraphDatabase

            neo4j_driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "")),
            )
            evidence_provider = CompositeEvidenceProvider(
                postgres_provider,
                Neo4jEvidenceProvider(neo4j_driver),
            )
        else:
            evidence_provider = postgres_provider

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

    @app.get("/api/v1/investigations/{transaction_id}")
    def investigate(transaction_id: str):
        return run_investigation(transaction_id, evidence_provider)

    @app.get("/api/v1/explanations/{transaction_id}")
    def explanation(transaction_id: str):
        result = evidence_provider.get_explanation(transaction_id)
        if result is None:
            raise HTTPException(status_code=404, detail="No model explanation found")
        return result

    @app.get("/api/v1/evidence/transactions/{transaction_id}")
    def transaction_evidence(transaction_id: str):
        transaction = evidence_provider.get_transaction(transaction_id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {
            "transaction_id": transaction_id,
            "alert": evidence_provider.get_alert(transaction_id),
            "transaction": transaction,
            "graph": evidence_provider.get_graph_evidence(transaction),
            "explanation": evidence_provider.get_explanation(transaction_id),
        }

    @app.get("/api/v1/evidence/accounts/{account_id}/history")
    def account_history(account_id: str, limit: int = Query(default=100, ge=1, le=1000)):
        return {"account_id": account_id, "items": evidence_provider.get_account_history(account_id, limit)}

    @app.get("/api/v1/evidence/accounts/{account_id}/counterparties")
    def account_counterparties(account_id: str, limit: int = Query(default=100, ge=1, le=1000)):
        return {"account_id": account_id, "items": evidence_provider.get_counterparties(account_id, limit)}

    @app.get("/api/v1/evidence/paths")
    def account_paths(source_account: str, target_account: str, max_hops: int = Query(default=3, ge=1, le=6)):
        return {
            "source_account": source_account,
            "target_account": target_account,
            "items": evidence_provider.get_paths(source_account, target_account, max_hops),
        }

    return app


app = create_app()
