# AML Investigator Dashboard

## Run locally

Start the Phase 4 API first:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform
$env:PYTHONPATH = ""
$env:DATABASE_URL = "postgresql+psycopg://aml_user:your-local-postgres-password@localhost:5432/aml_platform"
$env:NEO4J_URI = "bolt://localhost:7687"
$env:NEO4J_USER = "neo4j"
$env:NEO4J_PASSWORD = "your-local-neo4j-password"
.venv\Scripts\python.exe -m uvicorn phase4_backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd C:\Users\akash\agentic-banking-fraud-platform\frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The Vite development server proxies `/api` and `/health` to the FastAPI service on port 8000.

## Production build

```powershell
npm run build
```
