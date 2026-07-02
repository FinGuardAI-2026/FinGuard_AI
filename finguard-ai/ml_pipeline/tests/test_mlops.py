"""
ml_pipeline/tests/test_mlops.py
───────────────────────────────
Unit tests for the MLflowTracker wrapper, ensuring clean logging
in both mock-active and simulated-offline environments.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from ml_pipeline.utils.mlflow_tracker import MLflowTracker


def test_mlflow_tracker_offline_fallback():
    """MLflowTracker should run in offline simulation mode without raising exceptions if MLflow is missing."""
    # Force tracker.active to False (offline mode simulator)
    tracker = MLflowTracker()
    tracker.active = False

    # Call all tracker APIs; they should log messages locally and not raise errors
    try:
        tracker.start_run("test_simulated_run")
        tracker.log_params({"alpha": 0.1, "l1_ratio": 0.5})
        tracker.log_metrics({"f1": 0.85, "precision": 0.82})
        tracker.log_figure("ghost_file_path.png", "plots")
        tracker.log_model(None, "model_path", "FinGuard_Simulated_Model")
        tracker.end_run()
    except Exception as e:
        pytest.fail(f"MLflowTracker offline fallback threw an unexpected exception: {e}")


@patch("ml_pipeline.utils.mlflow_tracker.HAS_MLFLOW", True)
@patch("ml_pipeline.utils.mlflow_tracker.mlflow")
def test_mlflow_tracker_online_mock(mock_mlflow):
    """MLflowTracker should execute standard MLflow SDK calls when online mode is active."""
    # Mock MLflow dependencies
    mock_mlflow.start_run = MagicMock()
    mock_mlflow.log_params = MagicMock()
    mock_mlflow.log_metrics = MagicMock()
    mock_mlflow.log_artifact = MagicMock()
    mock_mlflow.end_run = MagicMock()

    tracker = MLflowTracker()
    tracker.active = True  # force active mode for test

    tracker.start_run("test_online_run")
    mock_mlflow.start_run.assert_called_once_with(run_name="test_online_run")

    tracker.log_params({"param1": "val1"})
    mock_mlflow.log_params.assert_called_once_with({"param1": "val1"})

    tracker.log_metrics({"metric1": 99.0})
    mock_mlflow.log_metrics.assert_called_once_with({"metric1": 99.0})

    tracker.end_run()
    mock_mlflow.end_run.assert_called_once()
