import numpy as np
import pytest

from phase8_explainability.explainer import rank_contributions


def test_rank_contributions_separates_top_positive_and_negative_features():
    result = rank_contributions(
        ["amount", "hour", "currency", "format"],
        np.array([0.2, -0.8, 0.4, -0.1]),
        [100.0, 23.0, "USD", "ACH"],
        top_k=2,
    )

    assert [item["feature"] for item in result] == ["currency", "amount", "hour", "format"]
    assert result[0]["value"] == "USD"
    assert result[2]["contribution"] == -0.8


def test_rank_contributions_rejects_mismatched_inputs():
    with pytest.raises(ValueError, match="equal lengths"):
        rank_contributions(["a"], [0.1, 0.2], [1], top_k=1)
