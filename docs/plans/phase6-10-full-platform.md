# Full Platform Completion Plan: Phases 6–10

> **For Hermes:** Execute this plan phase by phase. Preserve the verified Phase 1–5 contracts and run focused tests before live integration.

**Goal:** Extend the verified fraud-detection foundation into an evidence-grounded investigation platform with agent orchestration, retrieval tools, explainability, dashboard, and end-to-end integration.

**Architecture:** Phase 6 provides a deterministic LangGraph investigation workflow. Phase 7 supplies PostgreSQL, Neo4j, and model-evidence tools behind explicit interfaces. Phase 8 adds SHAP explanations from the saved XGBoost pipeline. Phase 9 provides a lightweight React investigator dashboard over new FastAPI investigation endpoints. Phase 10 verifies the full path from persisted alert to investigation report and dashboard API.

**Tech Stack:** Python 3.11, LangGraph, SQLAlchemy, Neo4j driver, SHAP, FastAPI, React, Vite, Docker Compose, pytest.

---

## Acceptance criteria

- An alert ID or transaction ID produces an investigation report from retrieved evidence.
- The agent workflow never invents evidence; missing sources are marked unavailable.
- PostgreSQL evidence, Neo4j graph evidence, and model explanation are independently testable.
- SHAP output identifies positive and negative feature contributions for a transaction.
- FastAPI exposes investigation and explanation endpoints.
- React dashboard lists alerts and displays a selected investigation report.
- A full integration test verifies alert → evidence → report.
- Existing Phase 1–5 tests remain green.

## Phase 6 — LangGraph investigation workflow

1. Define a typed investigation state.
2. Add nodes for alert retrieval, transaction retrieval, graph retrieval, explanation retrieval, and report synthesis.
3. Use a deterministic report synthesizer first; keep an LLM adapter optional.
4. Add tests for complete evidence, partial evidence, missing alert, and bounded graph traversal.

## Phase 7 — Evidence tools

1. Implement PostgreSQL alert/transaction evidence access.
2. Implement Neo4j account history, counterparties, and path access.
3. Implement model metadata and score access.
4. Add safe limits and explicit unavailable-source responses.
5. Add FastAPI endpoints for investigations and evidence.

## Phase 8 — Explainability

1. Reconstruct the model feature row from the stored raw payload.
2. Load the saved XGBoost pipeline.
3. Calculate SHAP contributions with a CPU-safe TreeExplainer or compatible fallback.
4. Return top positive and negative contributors with model score and threshold.
5. Add unit tests without requiring GPU.

## Phase 9 — React dashboard

1. Create a Vite React TypeScript app under `frontend/`.
2. Add alert list and status/risk filters.
3. Add investigation detail view.
4. Add graph evidence and explanation panels.
5. Add Docker/dev instructions and a production build check.

## Phase 10 — Integration and delivery

1. Add a bounded integration test with seeded SQLite/fake graph evidence.
2. Verify live PostgreSQL and Neo4j read-back using the existing containers.
3. Verify dashboard build and API contract.
4. Update README, runbook, and presentation.
5. Run the complete test/build checks.
6. Commit and push each validated phase.
