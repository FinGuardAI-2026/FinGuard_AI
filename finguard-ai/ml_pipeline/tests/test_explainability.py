"""
ml_pipeline/tests/test_explainability.py
────────────────────────────────────────
Unit tests validating FinGuardSHAPExplainer attribution calculations,
attributions plotting interfaces, and analyst text summaries.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock

from ml_pipeline.explainability.shap_explainer import FinGuardSHAPExplainer


def test_shap_explainer_simulated_attributions():
    """FinGuardSHAPExplainer should compute simulated Shapley matrices when SHAP is disabled."""
    # Create simple background data
    X_bg = pd.DataFrame({
        "Amount": [10.0, 20.0, 30.0],
        "V1": [0.5, -0.2, 0.1],
        "V2": [1.2, 0.4, -0.5],
    })

    # Mock fitted model
    mock_model = MagicMock()
    mock_model.feature_importances_ = np.array([0.5, 0.3, 0.2])

    xai = FinGuardSHAPExplainer(mock_model, X_bg)
    # Force simulation mode for validation
    xai.active = False

    X_test = pd.DataFrame({
        "Amount": [15.0, 25.0],
        "V1": [0.1, -0.1],
        "V2": [0.5, 0.2],
    })

    shap_values = xai.calculate_shap_values(X_test)
    assert shap_values.shape == (2, 3)  # 2 samples, 3 features
    assert not np.isnan(shap_values).any()


def test_shap_explainer_analyst_narrative():
    """FinGuardSHAPExplainer should create structured risk driver and mitigating factor narratives."""
    X_bg = pd.DataFrame({
        "Amount": [100.0],
        "V1": [0.1],
        "V2": [-0.5],
    })

    mock_model = MagicMock()
    xai = FinGuardSHAPExplainer(mock_model, X_bg)

    # Positive SHAP value indicates risk driver; Negative indicates mitigating factor
    shap_vector = np.array([0.15, -0.08, 0.001])
    sample_row = pd.Series([100.0, 0.1, -0.5], index=["Amount", "V1", "V2"])

    narrative = xai.generate_analyst_narrative(shap_vector, sample_row)

    assert "base_value" in narrative
    assert "positive_drivers" in narrative
    assert "negative_drivers" in narrative
    assert "analyst_narrative" in narrative

    # Amount (0.15 > 0.005) must be classified as risk driver
    risk_drivers = narrative["analyst_narrative"]["risk_drivers"]
    assert len(risk_drivers) == 1
    assert "Amount" in risk_drivers[0]
    assert "+15.00%" in risk_drivers[0]

    # V1 (-0.08 < -0.005) must be classified as mitigating factor
    mitigating = narrative["analyst_narrative"]["mitigating_factors"]
    assert len(mitigating) == 1
    assert "V1" in mitigating[0]
    assert "-8.00%" in mitigating[0]
