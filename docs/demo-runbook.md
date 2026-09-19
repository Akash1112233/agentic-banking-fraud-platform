# Review 2 demonstration runbook

This runbook restores the verified Phase 1–5 demo without changing code.

## 1. Start Docker services

Open Docker Desktop and wait for `Engine running`.

In PowerShell:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform

$env:AML_DB_PASSWORD = "your-local-postgres-password"
$env:NEO4J_PASSWORD = "your-local-neo4j-password"

docker compose -f phase3_streaming\docker-compose.yml up -d
docker compose -f phase4_backend\docker-compose.yml up -d
docker compose -f phase5_graph\docker-compose.yml up -d
```

Do not run `docker compose down -v`; named volumes contain the PostgreSQL and Neo4j data.

## 2. Start FastAPI

Open a second PowerShell terminal:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform
$env:PYTHONPATH = ""
$env:DATABASE_URL = "postgresql+psycopg://aml_user:your-local-postgres-password@localhost:5432/aml_platform"
.venv\Scripts\python.exe -m uvicorn phase4_backend.app.main:app --host 127.0.0.1 --port 8000
```

Keep this terminal open.

## 3. Verify the backend

Open a third terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/alerts
```

Open the interactive API page:

```text
http://127.0.0.1:8000/docs
```

Expected health result: `ok` and `ready`.

## 4. Verify the graph

Open:

```text
http://localhost:7474
```

Log in as `neo4j` with the local Neo4j password, then run:

```cypher
MATCH (a:Account) RETURN count(a) AS accounts;
MATCH (t:Transaction) RETURN count(t) AS transactions;
MATCH ()-[r:SENT]->() RETURN count(r) AS sent_relationships;
MATCH ()-[r:RECEIVED_BY]->() RETURN count(r) AS received_relationships;
```

Expected verified values:

```text
Accounts:                    872
Transactions:              1,000
SENT relationships:        1,000
RECEIVED_BY relationships: 1,000
```

## 5. Demonstration story

Use this order during the review:

1. Show the project roadmap and completed phases.
2. Show the XGBoost model and provisional threshold `0.55`.
3. Show the Kafka streaming architecture.
4. Show `/health` and `/docs` in FastAPI.
5. Show 21 persisted alerts from `/api/v1/alerts`.
6. Show Neo4j account and transaction counts.
7. Show one graph relationship query.
8. Explain that Phases 6–10 are the remaining roadmap.

## 6. Remaining project work

- Phase 6: LangGraph investigation agents.
- Phase 7: Evidence retrieval tools.
- Phase 8: SHAP explanations and investigation reports.
- Phase 9: React investigator dashboard.
- Phase 10: Full human-in-the-loop integration testing.

Keep passwords only in the current PowerShell session. Never place them in GitHub, screenshots, or the presentation.
