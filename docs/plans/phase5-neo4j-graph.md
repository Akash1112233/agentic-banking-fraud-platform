# Phase 5 — Neo4j financial graph implementation plan

**Goal:** Project persisted PostgreSQL transactions, predictions, and alerts into a queryable Neo4j graph for financial investigation.

**Architecture:** A batch loader reads the Phase 4 PostgreSQL tables and writes idempotent `Account` and `Transaction` nodes plus `SENT` and `RECEIVED_BY` relationships using Neo4j `UNWIND` batches. Investigation queries expose transaction history, account counterparties, and multi-hop transaction paths without inventing evidence.

**Tech Stack:** Neo4j 5, neo4j Python driver, SQLAlchemy, PostgreSQL, pytest.

---

### Task 1: Define graph row transformation

- Create failing tests for converting Phase 4 records into stable graph rows.
- Verify account IDs remain strings, transaction IDs are stable, and missing optional values become `None`.
- Implement pure transformation functions before adding database I/O.

### Task 2: Add Neo4j schema and idempotent batch loader

- Add uniqueness constraints for `Account.account_id` and `Transaction.transaction_id`.
- Use `MERGE` and `UNWIND` so rerunning the loader does not duplicate nodes or relationships.
- Read transaction/prediction/alert data from PostgreSQL through the existing SQLAlchemy models.

### Task 3: Add investigation graph queries

- Query account transaction history.
- Query direct counterparties.
- Query bounded multi-hop paths between accounts.
- Return only graph-retrieved records with stable IDs and risk metadata.

### Task 4: Add Neo4j Docker service and operator documentation

- Add a local Neo4j 5 container with browser and Bolt ports.
- Document environment variables, startup, loading, and verification commands.

### Task 5: Verify locally

- Run unit tests without Docker.
- Start PostgreSQL and Neo4j.
- Load the Phase 4 records.
- Verify graph counts and sample relationship queries in Neo4j Browser/CLI.

---
