"""
ml_pipeline/utils/metrics_utils.py
──────────────────────────────────
Calculates and formats all required binary classification performance metrics
for model validation and benchmarking.
"""
from typing import Dict, Any, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_metrics(
    y_true: Union[np.ndarray, list],
    y_pred: Union[np.ndarray, list],
    y_prob: Union[np.ndarray, list] = None,
) -> Dict[str, Any]:
    """
    Computes standard performance metrics for binary classification models.

    Includes accuracy, precision, recall, f1-score, and optionally roc_auc / average_precision
    if probability estimates are provided.
    """
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)

    metrics = {
        "accuracy": float(accuracy_score(y_true_arr, y_pred_arr)),
        "precision": float(precision_score(y_true_arr, y_pred_arr, zero_division=0)),
        "recall": float(recall_score(y_true_arr, y_pred_arr, zero_division=0)),
        "f1": float(f1_score(y_true_arr, y_pred_arr, zero_division=0)),
    }

    # Confusion matrix extraction
    tn, fp, fn, tp = confusion_matrix(y_true_arr, y_pred_arr).ravel()
    metrics["confusion_matrix"] = {
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
    }

    # Add probability-based metrics if provided
    if y_prob is not None:
        y_prob_arr = np.asarray(y_prob)
        metrics["roc_auc"] = float(roc_auc_score(y_true_arr, y_prob_arr))
        metrics["average_precision"] = float(average_precision_score(y_true_arr, y_prob_arr))

    logger.info(
        f"Computed performance metrics: F1={metrics['f1']:.4f}, "
        f"Recall={metrics['recall']:.4f}, Precision={metrics['precision']:.4f}"
    )
    return metrics
