# Review 2 demonstration runbook

This runbook starts the verified AML detection, evidence, LLM interpretation, and dashboard demo.

## 1. Start Docker services

Open Docker Desktop and wait for `Engine running`.

In PowerShell:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform

.\scripts\start-infrastructure.ps1 -DbPassword "your-local-postgres-password" -Neo4jPassword "your-local-neo4j-password"
```

The script checks Docker and Ollama, then starts Redpanda, PostgreSQL, and Neo4j. It does not save either password to disk.

Do not run `docker compose down -v`; named volumes contain the PostgreSQL and Neo4j data.

## 2. Start FastAPI

Open a second PowerShell terminal:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform
$env:PYTHONPATH = ""
$env:DATABASE_URL = "postgresql+psycopg://aml_user:your-local-postgres-password@localhost:5432/aml_platform"
# The default is local Ollama with qwen3:14b; no cloud API key is required.
$env:LLM_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "qwen3:14b"
$env:OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
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
2. Show the XGBoost model and alert threshold `0.55`.
3. Show the Kafka streaming architecture.
4. Show `/health` and `/docs` in FastAPI.
5. Show the synthetic producer publishing a new transaction in real time.
6. Show the consumer scoring it and creating an alert above threshold `0.55`.
7. Show the investigation endpoint and dashboard evidence.
8. Show the LLM analyst interpretation: conclusion, rationale, and recommended action.
9. Explain that SHAP and graph evidence ground the LLM response; the LLM cannot invent missing evidence.
10. State clearly that the output is a high-risk alert for human review, not proof of criminal activity.

## 6. LLM interpretation notes

The local Ollama step is enabled by default with `OLLAMA_MODEL=qwen3:14b`. It receives the alert, transaction, SHAP explanation, graph evidence, and evidence limitations as context. Set `LLM_PROVIDER=openai` only if you intentionally switch to the cloud adapter and provide `OPENAI_API_KEY`.

- `llm_status`: `available`, `not_configured`, or `error:<type>`
- `llm_interpretation.conclusion`
- `llm_interpretation.rationale`
- `llm_interpretation.recommended_action`
- `llm_interpretation.confidence`

If the key is absent or the provider fails, the evidence investigation still works and the dashboard clearly shows that the LLM interpretation is unavailable. Never commit the key or put it in screenshots.

Keep passwords only in the current PowerShell session. Never place them in GitHub, screenshots, or the presentation.
