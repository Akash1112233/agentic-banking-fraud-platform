# Phase 5 — Neo4j financial graph

Phase 5 projects Phase 4 PostgreSQL evidence into Neo4j for relationship-based investigation.

## Graph model

```text
(:Account)-[:SENT]->(:Transaction)-[:RECEIVED_BY]->(:Account)
```

Account and transaction IDs are unique. The loader uses `MERGE`, so rerunning it is safe and does not duplicate graph entities or relationships.

## Install

```powershell
$env:PYTHONPATH = ""
uv pip install --python .venv\Scripts\python.exe -r phase5_graph\requirements.txt
```

## Start Neo4j

Use a local-only password and keep it out of Git:

```powershell
$env:NEO4J_PASSWORD = "choose-a-local-neo4j-password"
docker compose -f phase5_graph\docker-compose.yml up -d
```

Neo4j Browser:

```text
http://localhost:7474
```

Bolt URI:

```text
bolt://localhost:7687
```

Browser credentials are `neo4j` and the password from `NEO4J_PASSWORD`.

## Load Phase 4 records

Use the same PostgreSQL password that was used for Phase 4:

```powershell
$env:PYTHONPATH = ""
$env:DATABASE_URL = "postgresql+psycopg://aml_user:choose-a-local-password@localhost:5432/aml_platform"
$env:NEO4J_URI = "bolt://localhost:7687"
$env:NEO4J_USER = "neo4j"
$env:NEO4J_PASSWORD = "choose-a-local-neo4j-password"

.venv\Scripts\python.exe -m phase5_graph.load_graph
```

Expected output for the current Phase 4 test data:

```text
Loaded 1,000 transaction rows into Neo4j
```

## Verify the graph

In Neo4j Browser, run:

```cypher
MATCH (a:Account) RETURN count(a) AS accounts;
MATCH (t:Transaction) RETURN count(t) AS transactions;
MATCH ()-[r:SENT]->() RETURN count(r) AS sent_relationships;
MATCH ()-[r:RECEIVED_BY]->() RETURN count(r) AS received_relationships;
```

Sample account history query:

```cypher
MATCH (a:Account {account_id: 'A001'})-[:SENT|RECEIVED_BY]-(t:Transaction)
RETURN t.transaction_id, t.risk_probability, t.alert
ORDER BY t.timestamp DESC;
```

The loader preserves prediction probability, alert flag, model name, threshold, payment metadata, and original account/bank identifiers as graph properties.
