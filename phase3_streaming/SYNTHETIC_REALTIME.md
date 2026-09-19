# Real-time synthetic transaction demo

This demo sends schema-valid synthetic transactions to the existing `aml.transactions` topic. The existing consumer scores them; no second model or detection path is created.

## Event path

```text
synthetic_producer.py
  -> aml.transactions
  -> consumer.py
  -> model score + threshold
  -> aml.predictions / aml.alerts
  -> FastAPI PostgreSQL persistence (when PREDICTIONS_API_URL is set)
  -> React investigator dashboard
```

Synthetic events contain `synthetic_scenario` metadata for demo auditing. The Phase 3 feature builder ignores this field, so it cannot leak the synthetic label into the model.

## Run the demo

Start Redpanda and the existing services first. In PowerShell terminal 1, start the consumer with a fresh group so it reads the demo events:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform
$env:PYTHONPATH = ""
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:19092"
$env:KAFKA_CONSUMER_GROUP = "aml-synthetic-demo-v1"
$env:KAFKA_AUTO_OFFSET_RESET = "latest"
$env:PREDICTIONS_API_URL = "http://127.0.0.1:8000/api/v1/predictions"
.venv\Scripts\python.exe phase3_streaming\src\consumer.py --max-messages 20
```

In PowerShell terminal 2, publish one transaction per second:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform
$env:PYTHONPATH = ""
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:19092"
.venv\Scripts\python.exe phase3_streaming\src\synthetic_producer.py --count 20 --interval 1 --scenario mixed --seed 42
```

For a continuous demo, replace `--count 20` with `--continuous` and stop with `Ctrl+C`.

To demonstrate a deliberately high-risk pattern:

```powershell
.venv\Scripts\python.exe phase3_streaming\src\synthetic_producer.py --count 10 --interval 1 --scenario high-value --seed 7 --start-index 1000
```

To demonstrate a traceable multi-hop/mule-account pattern:

```powershell
.venv\Scripts\python.exe phase3_streaming\src\synthetic_producer.py --count 12 --interval 1 --scenario mule-chain --seed 8 --start-index 2000
```

## Verify

Check local outputs:

```powershell
Get-Content phase3_streaming\outputs\predictions.jsonl -Tail 10
Get-Content phase3_streaming\outputs\alerts.jsonl -Tail 10
```

Check persisted alerts:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/alerts?status=open&limit=10"
```

Then open the dashboard at `http://localhost:5173` and select a `synthetic-*` alert.

A high model score means **high-risk/suspected**, not confirmed fraud. Synthetic scenarios are demonstration labels; the consumer does not use them for inference.
