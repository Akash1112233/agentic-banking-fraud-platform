# Project overview

The platform detects suspicious banking transactions in real time and automatically performs an evidence-based financial-forensics investigation.

The ML layer produces an initial risk estimate. High-risk events trigger specialized LangGraph agents that retrieve and reason over transaction history, PostgreSQL records, Neo4j relationships, and model explanations. A human investigator makes the final case decision.

The initial dataset is the IBM Transactions for Anti-Money Laundering dataset. It is primarily an AML dataset, so device, IP, and location features must not be presented as real evidence unless they are supplied by an additional source or explicitly simulated.
