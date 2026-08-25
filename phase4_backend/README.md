# Phase 4 — FastAPI and PostgreSQL

Phase 4 persists streaming predictions and AML alerts and exposes them through a FastAPI service.

## Architecture

```text
Kafka consumer -> POST /api/v1/predictions -> PostgreSQL
                                              |
                                    GET /api/v1/alerts
```

The consumer keeps its JSONL output and Kafka topics. Set `PREDICTIONS_API_URL` to additionally persist each scored event in the API.

## Install

```powershell
$env:PYTHONPATH = ""
uv pip install --python .venv\Scripts\python.exe -r phase4_backend\requirements.txt
```

## Run automated tests

```powershell
$env:PYTHONPATH = ""
.venv\Scripts\python.exe -m pytest phase4_backend\tests -q
```

## Start PostgreSQL

Set a local password in the current shell. Do not commit it:

```powershell
$env:AML_DB_PASSWORD = "choose-a-local-password"
docker compose -f phase4_backend\docker-compose.yml up -d
```

## Start the API

```powershell
$env:PYTHONPATH = ""
$env:DATABASE_URL = "postgresql+psycopg://aml_user:choose-a-local-password@localhost:5432/aml_platform"
.venv\Scripts\python.exe -m uvicorn phase4_backend.app.main:app --host 127.0.0.1 --port 8000
```

Open the interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Connect the Kafka consumer to the API

Run the consumer in another terminal with the same database-independent Kafka settings:

```powershell
$env:PYTHONPATH = ""
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:19092"
$env:PREDICTIONS_API_URL = "http://127.0.0.1:8000/api/v1/predictions"
.venv\Scripts\python.exe phase3_streaming\src\consumer.py --max-messages 1000
```

The consumer calls the API before committing each Kafka offset. If the API is unavailable, the event goes to the dead-letter path and its offset is still handled without stopping the consumer.

## API endpoints

- `GET /health` — service and database readiness.
- `POST /api/v1/predictions` — idempotently persist a transaction prediction and create an open alert when `alert=true`.
- `GET /api/v1/alerts` — list alerts; use `?status=open` to filter.

The database stores account and bank identifiers as text and retains the original transaction payload as JSON for later evidence retrieval.
