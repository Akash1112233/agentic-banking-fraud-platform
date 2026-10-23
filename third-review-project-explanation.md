# Third Review Project Explanation

## Project title

**Agentic AI Platform for Real-Time Banking Fraud Detection and Financial Forensics**

## Team and academic context

| Student ID | Team member |
| --- | --- |
| 23MIA1112 | Annam Akash |
| 23MIA1101 | B Hema |
| 23MIA1105 | Guru Raghav Raj |

Developed as part of **Forensic Analytics (CSE4074)** at **Vellore Institute of Technology, Chennai**, during **Fall 2026-27**, under **Dr. S. Johanan Joysingh**.

## Problem statement

Banking fraud and money laundering investigations require more than a binary prediction. An investigator needs to know which transaction is suspicious, which model signals contributed to the risk estimate, how the involved accounts are connected, and what evidence supports the alert.

The project addresses this gap by connecting real-time machine-learning scoring with structured evidence retrieval and a human-readable investigation workflow.

## Proposed solution

The platform follows this sequence:

1. A transaction is read from an AML dataset or produced as a real-time event.
2. A trained XGBoost pipeline produces a laundering-risk probability.
3. Transactions above the operational threshold generate alerts.
4. Predictions and alerts are persisted in PostgreSQL.
5. Account and transaction relationships are represented in Neo4j.
6. Evidence providers retrieve transaction history, graph relationships, alert data, and SHAP explanations.
7. LangGraph coordinates the investigation steps.
8. A local Ollama model converts the retrieved evidence into a concise investigation explanation.
9. The React dashboard presents the alert and evidence to a human investigator.

## System components

| Component | Role in the project |
| --- | --- |
| Data foundation | Inspects the AML data, normalizes fields, creates derived features, and performs EDA. |
| Machine learning | Compares Logistic Regression, Random Forest, and XGBoost; selects and saves the operational pipeline. |
| Streaming | Uses a Kafka-compatible broker to transport transaction events and score them continuously. |
| Backend | Exposes health, prediction, and alert APIs and persists records in PostgreSQL. |
| Financial graph | Uses Neo4j to connect sending accounts, transactions, and receiving accounts. |
| Agent workflow | Retrieves relevant evidence and coordinates the investigation sequence. |
| Explainability | Uses SHAP to show which input features influenced the model output. |
| Dashboard | Gives an investigator a single interface for alerts, risk, evidence, and interpretation. |

## Evidence-grounding principle

The language model is not treated as the source of truth. It receives evidence retrieved from the platform and must distinguish between known facts, model-derived signals, and unavailable information. This reduces unsupported explanations and makes the final report auditable.

The system also makes an important forensic distinction: a high risk score identifies activity for review; it does not establish criminal intent or guilt. Human investigators remain responsible for the final decision.

## Demonstration story

For the presentation, the platform can be demonstrated as an investigation story:

1. Start the Kafka-compatible broker, PostgreSQL, and Neo4j services.
2. Start the FastAPI service and verify its health endpoint.
3. Produce a controlled set of transactions.
4. Show the scoring consumer publishing predictions and alerts.
5. Open the dashboard and select a high-risk alert.
6. Inspect the transaction fields, model probability, SHAP explanation, and account graph.
7. Run the evidence-grounded agent workflow and compare its explanation with the retrieved facts.
8. Emphasize that the analyst makes the final case decision.

The full commands are available in [`demo-runbook.md`](demo-runbook.md), while [`../project-summary.md`](../project-summary.md) contains the detailed phase-by-phase presentation guide.

## Expected academic contribution

The project demonstrates how forensic analytics can combine predictive modelling with traceable evidence. Its contribution is the integration of:

- real-time risk scoring;
- relational and graph-based evidence;
- model explainability;
- agentic orchestration;
- local language-model interpretation; and
- a human-in-the-loop investigator interface.

## Scope and limitations

- The included AML dataset is not a complete representation of every banking fraud scenario.
- Raw datasets, generated model files, credentials, and local infrastructure state remain outside the repository.
- A model score is a prioritization signal and must not be reported as proof of wrongdoing.
- Device, IP, or location claims require an appropriate data source; they must not be inferred from the AML dataset alone.
- The local LLM is used for interpretation of retrieved evidence, not for independently inventing evidence.

## Repository status

The repository contains the implementation and review documentation needed for the project demonstration. A research paper intended for publication is not included in the repository at this stage.
