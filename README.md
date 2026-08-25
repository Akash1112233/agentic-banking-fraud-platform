# Agentic AI Platform for Real-Time Banking Fraud Detection and Financial Forensics

This project builds an evidence-based agentic AI platform for real-time anti-money-laundering and suspicious-transaction investigation.

## Current status

- Project scaffold created
- Dataset files are not committed to GitHub
- Phase 1: Data Foundation is next

## Dataset setup

Place the downloaded files locally in `data/raw/`:

- `HI-Small_Trans.csv`
- `HI-Small_accounts.csv`
- `HI-Small_Patterns.txt`

Do not open and save the CSV files through Excel. The files will be inspected and processed with Python so account and entity identifiers are preserved.

## Development phases

1. Dataset, preprocessing, and EDA
2. ML model comparison
3. Kafka real-time streaming
4. FastAPI and PostgreSQL
5. Neo4j financial graph
6. LangGraph multi-agent workflow
7. Evidence-based agent tools
8. SHAP explainability
9. React dashboard
10. Integration and testing

## Principle

Agents must use retrieved evidence from the database, graph, transaction history, and ML model. They must not invent banking information or evidence.
