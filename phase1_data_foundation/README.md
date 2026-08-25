# Phase 1 — Data Foundation

Phase 1 inspects, preprocesses, and explores the IBM Transactions for Anti-Money Laundering dataset.

## Setup

From the repository root, create a virtual environment and install dependencies:

```bash
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r phase1_data_foundation/requirements.txt
```

On Git Bash, the interpreter path may be `.venv/Scripts/python.exe`; on other shells use the equivalent path inside `.venv`.

## Run

```bash
.venv/Scripts/python.exe phase1_data_foundation/run_phase1.py
```

The workflow uses chunked reads, so the 475 MB transaction file is not loaded into memory all at once. It creates:

- `phase1_data_foundation/outputs/reports/dataset_inspection.json`
- `phase1_data_foundation/outputs/reports/eda_summary.json`
- PNG charts under `phase1_data_foundation/outputs/figures/`

Generated outputs are ignored by Git. Raw data remains local and is also ignored by Git.

## Tests

```bash
.venv/Scripts/python.exe -m pytest phase1_data_foundation/tests -q
```
