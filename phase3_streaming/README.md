# Phase 3 — Kafka real-time streaming

Phase 3 connects the Phase 2 XGBoost model to a Kafka-compatible transaction stream.

## Architecture

```text
IBM AML CSV -> transaction producer -> aml.transactions
                                      |
                                      v
                              prediction consumer
                                      |
                         +------------+------------+
                         v                         v
                  aml.predictions              aml.alerts
```

The consumer uses the same feature columns as Phase 2 and applies the saved operational threshold (`0.55` by default). PostgreSQL is intentionally deferred to Phase 4.

## Prerequisites

- Docker Desktop installed and running
- Phase 2 model generated at `phase2_ml_models/models/best_model_xgboost.joblib`
- Python virtual environment created at `.venv`

## Install dependencies

From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = ""
uv pip install --python .venv\Scripts\python.exe -r phase3_streaming\requirements.txt
```

## Start the Kafka-compatible broker

```powershell
docker compose -f phase3_streaming\docker-compose.yml up -d
```

Check that the broker is running:

```powershell
docker compose -f phase3_streaming\docker-compose.yml ps
```

## Start the prediction consumer

Open a second terminal:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform
$env:PYTHONPATH = ""
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:19092"
.venv\Scripts\python.exe phase3_streaming\src\consumer.py --max-messages 1000
```

The consumer loads the saved model and writes local test results to:

```text
phase3_streaming/outputs/predictions.jsonl
phase3_streaming/outputs/alerts.jsonl
```

## Start the producer

Open a third terminal:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform
$env:PYTHONPATH = ""
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:19092"
.venv\Scripts\python.exe phase3_streaming\src\producer.py --limit 1000
```

Start with 1,000 messages. Only stream the full dataset after the small test works.

## Important details

- The producer sends source transactions; it does not use `Is Laundering` for prediction.
- The label is retained only in local test payloads when present, so offline results can be checked later. The consumer ignores it.
- Account IDs and bank IDs are serialized as strings.
- The consumer commits Kafka offsets only after successful scoring and output publication.
- Invalid records are written to `aml.dead_letter` and do not stop the consumer.
- GPU acceleration is mainly useful for training. Single-event inference normally runs adequately on CPU.
