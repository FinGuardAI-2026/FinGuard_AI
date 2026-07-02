"""
ml_pipeline/utils/mlflow_tracker.py
───────────────────────────────────
MLflow wrapper module that tracks parameters, metrics, models, and charts.
Gracefully falls back to local logging if MLflow is not installed.
"""
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np

from ml_pipeline.utils.logger import get_logger
from ml_pipeline.config.paths import paths

logger = get_logger(__name__)

# Try importing MLflow packages, flag if missing
HAS_MLFLOW = False
try:
    import mlflow
    import mlflow.sklearn
    from mlflow.tracking import MlflowClient
    HAS_MLFLOW = True
except ImportError:
    logger.warning("mlflow package not detected. MLflow tracking will run in offline simulation mode.")


class MLflowTracker:
    """
    Manages connections to the MLflow local or remote server.
    Logs metrics, parameters, plots, and handles Model Registry operations.
    """

    def __init__(self, experiment_name: str = "FinGuard_AI_Fraud_Detection") -> None:
        self.experiment_name = experiment_name
        self.active = HAS_MLFLOW
        self.current_run = None

        if self.active:
            try:
                # Set tracking directory locally in the workspace experiments/mlruns/
                tracking_dir = paths.experiments_dir / "mlruns"
                tracking_uri = f"file:///{tracking_dir.resolve().as_posix()}"
                mlflow.set_tracking_uri(tracking_uri)

                # Set or create the experiment
                mlflow.set_experiment(self.experiment_name)
                logger.info(f"MLflow tracking active. Tracking URI: {tracking_uri}")
            except Exception as e:
                logger.warning(f"Failed to initialize MLflow URI: {e}. Switching to offline mode.")
                self.active = False

    def start_run(self, run_name: str) -> None:
        """Starts a new experiment tracking run context."""
        if self.active:
            try:
                self.current_run = mlflow.start_run(run_name=run_name)
                logger.info(f"Started MLflow run: '{run_name}'")
            except Exception as e:
                logger.warning(f"Error starting MLflow run: {e}")
        else:
            logger.info(f"[Offline Run] Started run context: '{run_name}'")

    def log_params(self, params: Dict[str, Any]) -> None:
        """Logs configuration parameters (hyperparameters, split ratios, etc.)."""
        if self.active:
            try:
                # Convert list parameter structures or complex dicts to string representation
                cleaned_params = {
                    k: (str(v) if isinstance(v, (list, dict)) else v)
                    for k, v in params.items()
                }
                mlflow.log_params(cleaned_params)
            except Exception as e:
                logger.warning(f"Failed to log parameters to MLflow: {e}")
        else:
            logger.info(f"[Offline Run Params]: {params}")

    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        """Logs scalar evaluation metrics."""
        if self.active:
            try:
                # Exclude dict objects like the confusion matrix from scalars
                scalar_metrics = {
                    k: float(v) for k, v in metrics.items()
                    if isinstance(v, (int, float, np.integer, np.floating))
                }
                mlflow.log_metrics(scalar_metrics)
            except Exception as e:
                logger.warning(f"Failed to log metrics to MLflow: {e}")
        else:
            # Format outputs for console verification
            formatted_metrics = {
                k: (f"{v:.4f}" if isinstance(v, float) else v)
                for k, v in metrics.items() if k != "y_prob" and k != "y_pred"
            }
            logger.info(f"[Offline Run Metrics]: {formatted_metrics}")

    def log_figure(self, fig_path: Union[str, Path], artifact_path: str = "plots") -> None:
        """Logs generated chart figures to the run's artifact storage."""
        path = Path(fig_path)
        if not path.is_file():
            logger.warning(f"Figure file '{path}' does not exist. Cannot log.")
            return

        if self.active:
            try:
                mlflow.log_artifact(str(path), artifact_path)
                logger.info(f"Logged figure '{path.name}' to MLflow run.")
            except Exception as e:
                logger.warning(f"Failed to log figure artifact to MLflow: {e}")
        else:
            logger.info(f"[Offline Run Artifact]: Saved '{path.name}' to local path '{path}'")

    def log_model(self, model: Any, artifact_path: str, registered_name: Optional[str] = None) -> None:
        """
        Serializes and logs a fitted scikit-learn model,
        optionally registering it in the Model Registry.
        """
        if self.active:
            try:
                # Log model via MLflow's standard scikit-learn serialization handler
                mlflow.sklearn.log_model(
                    sk_model=model,
                    artifact_path=artifact_path,
                    registered_model_name=registered_name,
                )
                if registered_name:
                    logger.info(f"Registered model '{registered_name}' in MLflow Registry.")
                else:
                    logger.info(f"Logged model artifact '{artifact_path}' to MLflow.")
            except Exception as e:
                logger.warning(f"Failed to log model to MLflow: {e}")
        else:
            logger.info(
                f"[Offline Run Model]: Saved model structure to '{artifact_path}'"
                + (f" (Registry Name: {registered_name})" if registered_name else "")
            )

    def end_run(self) -> None:
        """Closes the current active run context."""
        if self.active:
            try:
                mlflow.end_run()
                self.current_run = None
                logger.info("Ended MLflow run context.")
            except Exception as e:
                logger.warning(f"Error ending MLflow run: {e}")
        else:
            logger.info("[Offline Run] Closed run context.")
