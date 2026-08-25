# Phase 2 — ML Model Comparison

This phase trains and compares Logistic Regression, Random Forest, and XGBoost for the `Is Laundering` target.

## Why controlled sampling is used

The transaction file contains more than 5 million rows, but only 5,177 laundering transactions. The notebook keeps all positive examples and samples a configurable number of legitimate transactions for training. This keeps the experiment feasible on a laptop while preserving the rare class. The sampling configuration is recorded in the notebook output.

The untouched validation split is created after sampling and is used for model comparison. For a production model, we can later evaluate on the complete chronological holdout.

## Install

From the repository root:

```powershell
$env:PYTHONPATH = ""
uv pip install --python .venv/Scripts/python.exe -r phase2_ml_models/requirements.txt
```

## Open the notebook

```powershell
$env:PYTHONPATH = ""
.venv\Scripts\python.exe -m jupyter lab notebooks\phase2_ml_model_comparison.ipynb
```

Open `notebooks/phase2_ml_model_comparison.ipynb` and run the cells in order.

## GPU

The notebook detects an NVIDIA GPU and attempts XGBoost GPU training with `device="cuda"` and `tree_method="hist"`. If CUDA support is unavailable, it automatically retries XGBoost on the CPU. Logistic Regression and Random Forest use the CPU.

## Outputs

The notebook writes metrics, charts, and the selected model under:

```text
phase2_ml_models/outputs/
phase2_ml_models/models/
```

The notebook also creates `threshold_metrics.json` and `threshold_tuning.png` after threshold tuning.

These generated artifacts are ignored by Git. The notebook and documentation are committed.
