"""
ml_pipeline/tests/test_training.py
──────────────────────────────────
Unit tests validating ModelTrainer search spaces and ModelEvaluator metrics calculations.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock

from ml_pipeline.training.trainer import ModelTrainer
from ml_pipeline.training.evaluator import ModelEvaluator


def test_model_trainer_search_space():
    """ModelTrainer should resolve valid estimators and parameter grids for all models."""
    trainer = ModelTrainer(random_state=42)

    for name in ["logistic_regression", "decision_tree", "random_forest", "xgboost", "lightgbm"]:
        estimator, grid = trainer.get_search_space(name)
        assert estimator is not None
        assert isinstance(grid, dict)
        assert len(grid) > 0


def test_model_evaluator_metrics():
    """ModelEvaluator should compute correct binary classification scores on prediction inputs."""
    # Create simple dummy test labels
    y_test = np.array([0, 0, 1, 1])
    # Predictions matching the labels
    y_pred = np.array([0, 0, 1, 1])
    # Probabilities for AUC calculations
    y_prob = np.array([0.1, 0.2, 0.8, 0.9])

    # Mock fitted model
    mock_model = MagicMock()
    mock_model.predict.return_value = y_pred
    mock_model.predict_proba.return_value = np.column_stack([1 - y_prob, y_prob])

    # Instantiate evaluator with mock temp output plots dir
    evaluator = ModelEvaluator(output_plots_dir="ml_pipeline/reports/figures")

    X_test = pd.DataFrame({"feat": [1, 2, 3, 4]})
    metrics = evaluator.evaluate(mock_model, X_test, y_test)

    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["roc_auc"] == 1.0
    assert metrics["pr_auc"] == 1.0
    assert metrics["confusion_matrix"]["true_positives"] == 2
    assert metrics["confusion_matrix"]["true_negatives"] == 2
    assert metrics["confusion_matrix"]["false_positives"] == 0
    assert metrics["confusion_matrix"]["false_negatives"] == 0
