"""Load the Phase 2 model and score streaming transaction records."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

import joblib

from features import build_model_features_from_record


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = ROOT / "phase2_ml_models" / "models" / "best_model_xgboost.joblib"
DEFAULT_THRESHOLD = float(os.getenv("AML_ALERT_THRESHOLD", "0.55"))


class TransactionScorer:
    """Online scorer using the persisted preprocessing-plus-model pipeline."""

    def __init__(self, model_path: str | Path = DEFAULT_MODEL_PATH, threshold: float = DEFAULT_THRESHOLD):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}. Run the Phase 2 notebook first."
            )
        self.model = joblib.load(self.model_path)
        self.threshold = float(threshold)
        self.inference_device = os.getenv("PHASE3_INFERENCE_DEVICE", "cpu").lower()
        if self.inference_device not in {"cpu", "cuda", "gpu"}:
            raise ValueError("PHASE3_INFERENCE_DEVICE must be cpu or cuda")
        if self.inference_device == "cpu":
            self._set_xgboost_inference_device("cpu")
        if not 0.0 < self.threshold < 1.0:
            raise ValueError("threshold must be between 0 and 1")

    def _set_xgboost_inference_device(self, device: str) -> None:
        """Avoid GPU/CPU DMatrix mismatch warnings for single-event inference."""
        try:
            estimator = self.model.named_steps["model"]
            estimator.get_booster().set_param({"device": device})
        except (AttributeError, KeyError):
            # The persisted model may be a non-XGBoost pipeline in later phases.
            pass

    def score(self, record: Mapping[str, object]) -> dict[str, object]:
        """Return a prediction event without inventing or modifying source evidence."""
        features = build_model_features_from_record(record)
        probability = float(self.model.predict_proba(features)[0, 1])
        alert = probability >= self.threshold
        return {
            "transaction_id": record.get("transaction_id"),
            "risk_probability": probability,
            "prediction": int(alert),
            "alert": bool(alert),
            "model": "xgboost",
            "threshold": self.threshold,
        }
