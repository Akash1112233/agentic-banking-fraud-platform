# Agentic AI Platform for Real-Time Banking Fraud Detection and Financial Forensics

Developed as part of the course on "Forensic Analytics" at Vellore Institute of Technology, Chennai.
by Annam Akash, B Hema, Guru Raghav Raj
Subject Code: CSE4074
Semester: Fall 2026-27
Professor: Dr. S. Johanan Joysingh

## Project overview

This project is an evidence-based agentic AI platform for real-time banking fraud detection and financial forensics. It scores incoming transactions, identifies high-risk activity, stores the supporting records, builds account-to-account relationship evidence, explains the model decision, and presents a grounded investigation summary for a human analyst.

The system is designed to support an investigator rather than replace one. A model probability is a risk signal, not proof that a person committed a crime. Final decisions remain with a qualified human reviewer.

## Why this project matters

Traditional fraud models often stop at a score such as `0.887`. That score does not explain which transaction was flagged, why it was considered risky, how the accounts are connected, or what evidence an investigator should review next. This platform combines machine learning, streaming, databases, graph analysis, explainability, and an evidence-grounded agent workflow to provide that context.

## Architecture

```text
AML dataset or synthetic transaction producer
                    |
                    v
          Kafka-compatible event stream
                    |
                    v
        XGBoost real-time scoring consumer
              /              |              \\
             v               v               v
      predictions        alerts          FastAPI API
                                             |
                         +-------------------+-------------------+
                         |                   |                   |
                         v                   v                   v
                    PostgreSQL            Neo4j                SHAP
                   transaction data     relationship graph   model evidence
                         \\                   |                   /
                          +-----------------+------------------+
                                            |
                                            v
                              LangGraph investigation workflow
                                            |
                                            v
                                  Local Ollama language model
                                            |
                                            v
                                    React investigator dashboard
```

The central design principle is grounded interpretation: the language model receives retrieved alert, transaction, graph, SHAP, and limitation data and is instructed not to invent missing banking evidence.

## Implemented development phases

| Phase | Capability | Main technologies |
| --- | --- | --- |
| 1 | Data inspection, preprocessing, and EDA | Python, pandas |
| 2 | Model comparison and threshold tuning | scikit-learn, XGBoost |
| 3 | Real-time transaction streaming and scoring | Redpanda/Kafka, `confluent-kafka` |
| 4 | Prediction and alert persistence | FastAPI, PostgreSQL, SQLAlchemy |
| 5 | Account and transaction relationship graph | Neo4j |
| 6 | Multi-step investigation workflow | LangGraph |
| 7 | Evidence retrieval from operational stores | PostgreSQL and Neo4j providers |
| 8 | Prediction explanation | SHAP |
| 9 | Investigator-facing dashboard | React, TypeScript, Vite |
| 10 | End-to-end verification | pytest and integration tests |

## Repository guide

- `phase1_data_foundation/` — dataset inspection, preprocessing, and exploratory analysis.
- `phase2_ml_models/` and `notebooks/` — model comparison, threshold tuning, and model artifacts generated locally.
- `phase3_streaming/` — producer, scoring consumer, feature creation, and Kafka-compatible infrastructure.
- `phase4_backend/` — FastAPI service, persistence models, repository layer, and PostgreSQL setup.
- `phase5_graph/` — Neo4j schema, idempotent graph loading, and investigation queries.
- `phase6_agents/` — LangGraph workflow and local LLM interpretation.
- `phase7_evidence/` — evidence-provider interfaces and database/graph retrieval.
- `phase8_explainability/` — SHAP-based model explanations.
- `frontend/` — React dashboard for alerts and investigations.
- `docs/` — architecture, dataset, development, and demonstration documentation.
- `project-summary.md` — detailed lecturer presentation guide with phase-by-phase implementation notes.
- `docs/third-review-project-explanation.md` — concise project explanation prepared as a companion to the presentation.

## Dataset and privacy

The project is built around the IBM Transactions for Anti-Money Laundering dataset. Dataset files are intentionally not committed. Place the following files locally under `data/raw/` when running the data and streaming phases:

- `HI-Small_Trans.csv`
- `HI-Small_accounts.csv`
- `HI-Small_Patterns.txt`

Do not commit credentials, database passwords, local model artifacts, raw datasets, or generated output files. The repository includes `.env.example` and `.gitignore` for local setup.

The dataset is primarily an AML dataset. Device, IP, and location attributes must not be presented as real evidence unless supplied by an additional source or explicitly simulated.

## Local setup

Create or activate the project virtual environment and install only the requirements for the phase you want to run. For example, from PowerShell:

```powershell
uv venv .venv
uv pip install --python .venv\Scripts\python.exe -r phase1_data_foundation\requirements.txt
$env:PYTHONPATH = ""
```

The complete demonstration sequence, including Docker services, FastAPI, Neo4j, Ollama, and the frontend, is documented in [`docs/demo-runbook.md`](docs/demo-runbook.md). The frontend can be started with:

```powershell
cd frontend
npm install
npm run dev
```

The dashboard is available at `http://localhost:5173` when the API is running on port `8000`.

## Tests

Run the relevant phase tests from the repository root after installing that phase's dependencies:

```powershell
$env:PYTHONPATH = ""
.venv\Scripts\python.exe -m pytest phase1_data_foundation\tests phase3_streaming\tests phase4_backend\tests phase5_graph\tests phase6_agents\tests phase7_evidence\tests phase8_explainability\tests phase10_integration\tests -q
```

## Academic and repository note

This repository contains the project implementation and review documentation. A separate research paper, if prepared for publication, is intentionally not included at this stage.

## Team

- 23MIA1112 — Annam Akash
- 23MIA1101 — B Hema
- 23MIA1105 — Guru Raghav Raj

## Course and supervision

Forensic Analytics (`CSE4074`)
Fall 2026-27
Vellore Institute of Technology, Chennai
Professor: Dr. S. Johanan Joysingh (`johananj`)
