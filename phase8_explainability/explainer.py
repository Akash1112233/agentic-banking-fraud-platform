from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Sequence

import joblib
import numpy as np

from phase3_streaming.src.features import build_model_features_from_record


class ModelExplainer:
    def __init__(
        self,
        model_path: str | Path,
        threshold: float = 0.55,
        shap_explainer_factory: Callable[[Any], Any] | None = None,
    ) -> None:
        self.model_path = Path(model_path)
        self.model = joblib.load(self.model_path)
        self.threshold = float(threshold)
        self._shap_explainer_factory = shap_explainer_factory

    def explain(self, record: dict[str, Any], top_k: int = 5) -> dict[str, Any]:
        if not 1 <= top_k <= 20:
            raise ValueError("top_k must be between 1 and 20")
        features = build_model_features_from_record(record)
        preprocessor = self.model.named_steps["preprocessor"]
        estimator = self.model.named_steps["model"]
        self._set_cpu_device(estimator)
        probability = float(self.model.predict_proba(features)[0, 1])
        transformed = preprocessor.transform(features)
        if hasattr(transformed, "toarray"):
            transformed_values = transformed.toarray()
        else:
            transformed_values = np.asarray(transformed)
        feature_names = [str(value) for value in preprocessor.get_feature_names_out()]
        factory = self._shap_explainer_factory or self._default_factory
        shap_explainer = factory(estimator)
        shap_values = _first_row_values(shap_explainer.shap_values(transformed_values))
        base_value = _first_scalar(shap_explainer.expected_value)
        ranked = rank_contributions(feature_names, shap_values, transformed_values[0], top_k)
        return {
            "source": "shap",
            "model": "xgboost",
            "threshold": self.threshold,
            "risk_probability": probability,
            "base_value": base_value,
            "top_positive": [item for item in ranked if item["contribution"] > 0],
            "top_negative": [item for item in ranked if item["contribution"] < 0],
        }

    @staticmethod
    def _set_cpu_device(estimator: Any) -> None:
        try:
            estimator.get_booster().set_param({"device": "cpu"})
        except (AttributeError, KeyError):
            pass

    @staticmethod
    def _default_factory(estimator: Any) -> Any:
        import shap

        return shap.TreeExplainer(estimator)


def rank_contributions(
    feature_names: Sequence[str], values: Sequence[float], feature_values: Sequence[Any], top_k: int
) -> list[dict[str, Any]]:
    if not (len(feature_names) == len(values) == len(feature_values)):
        raise ValueError("feature names, values, and feature values must have equal lengths")
    items = [
        {
            "feature": str(name),
            "contribution": float(value),
            "value": _json_value(feature_value),
        }
        for name, value, feature_value in zip(feature_names, values, feature_values)
        if float(value) != 0.0
    ]
    positives = sorted((item for item in items if item["contribution"] > 0), key=lambda item: item["contribution"], reverse=True)
    negatives = sorted((item for item in items if item["contribution"] < 0), key=lambda item: item["contribution"])
    return positives[:top_k] + negatives[:top_k]


def _first_row_values(values: Any) -> np.ndarray:
    if isinstance(values, list):
        values = values[0]
    array = np.asarray(values)
    return array[0] if array.ndim > 1 else array


def _first_scalar(value: Any) -> float:
    if isinstance(value, (list, tuple, np.ndarray)):
        return float(np.asarray(value).reshape(-1)[0])
    return float(value)


def _json_value(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value
