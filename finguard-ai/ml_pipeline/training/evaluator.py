"""
ml_pipeline/training/evaluator.py
─────────────────────────────────
Measures model accuracy, precision, recall, f1, ROC-AUC, PR-AUC,
confusion matrix properties, and execution timings. Saves ROC/PR charts.
"""
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    precision_recall_curve,
    auc,
    roc_curve,
    confusion_matrix,
)

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class ModelEvaluator:
    """
    Computes performance metrics and saves evaluation plots.
    """

    def __init__(self, output_plots_dir: Union[str, Path]) -> None:
        self.plots_dir = Path(output_plots_dir)
        self.plots_dir.mkdir(parents=True, exist_ok=True)

    def evaluate(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: Union[pd.Series, np.ndarray],
    ) -> Dict[str, Any]:
        """Runs predictions, records execution times, and computes classification metrics."""
        y_true = np.asarray(y_test)

        # 1. Measure inference time
        start_time = time.time()
        y_pred = model.predict(X_test)
        inference_time_total = time.time() - start_time
        inference_time_per_sample_ms = (inference_time_total / len(X_test)) * 1000.0

        # Get probabilities for AUC metrics
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_test)[:, 1]
        elif hasattr(model, "decision_function"):
            y_prob = model.decision_function(X_test)
        else:
            y_prob = y_pred.astype(float)

        # 2. Compute performance metrics
        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        roc_auc = float(roc_auc_score(y_true, y_prob))

        # Precision-Recall AUC calculation
        precisions, recalls, _ = precision_recall_curve(y_true, y_prob)
        pr_auc = float(auc(recalls, precisions))

        # Confusion Matrix elements
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        logger.info(
            f"Evaluation result: Acc={acc:.4f}, Prec={prec:.4f}, Rec={rec:.4f}, "
            f"F1={f1:.4f}, ROC-AUC={roc_auc:.4f}, PR-AUC={pr_auc:.4f}"
        )

        return {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "confusion_matrix": {
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_positives": int(tp),
            },
            "inference_time_total_s": inference_time_total,
            "inference_time_per_sample_ms": inference_time_per_sample_ms,
            "y_prob": y_prob.tolist(),  # save raw list for curve plotting
            "y_pred": y_pred.tolist(),
        }

    def save_plots(
        self,
        model_name: str,
        y_test: Union[pd.Series, np.ndarray],
        y_prob: List[float],
        y_pred: List[float],
    ) -> None:
        """Saves ROC, Precision-Recall, and Confusion Matrix charts to the figures folder."""
        y_true = np.asarray(y_test)
        probs = np.asarray(y_prob)
        preds = np.asarray(y_pred)

        # ── 1. ROC Curve ──
        fpr, tpr, _ = roc_curve(y_true, probs)
        roc_val = roc_auc_score(y_true, probs)

        plt.figure(figsize=(6, 5))
        plt.plot(fpr, tpr, color="#EF4444", lw=2, label=f"ROC Curve (AUC = {roc_val:.4f})")
        plt.plot([0, 1], [0, 1], color="gray", lw=1, linestyle="--")
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title(f"ROC Curve - {model_name.upper()}", fontsize=11, fontweight="bold")
        plt.legend(loc="lower right")
        plt.grid(True, linestyle=":", alpha=0.5)
        plt.tight_layout()
        roc_path = self.plots_dir / f"roc_curve_{model_name}.png"
        plt.savefig(roc_path, dpi=300)
        plt.close()

        # ── 2. Precision-Recall Curve ──
        precisions, recalls, _ = precision_recall_curve(y_true, probs)
        pr_auc = auc(recalls, precisions)

        plt.figure(figsize=(6, 5))
        plt.plot(recalls, precisions, color="#3B82F6", lw=2, label=f"PR Curve (AUC = {pr_auc:.4f})")
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title(f"Precision-Recall Curve - {model_name.upper()}", fontsize=11, fontweight="bold")
        plt.legend(loc="lower left")
        plt.grid(True, linestyle=":", alpha=0.5)
        plt.tight_layout()
        pr_path = self.plots_dir / f"pr_curve_{model_name}.png"
        plt.savefig(pr_path, dpi=300)
        plt.close()

        # ── 3. Confusion Matrix Heatmap ──
        cm = confusion_matrix(y_true, preds)
        plt.figure(figsize=(5, 5))
        plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Reds)
        plt.title(f"Confusion Matrix - {model_name.upper()}", fontsize=11, fontweight="bold")
        plt.colorbar()
        classes = ["Genuine", "Fraud"]
        tick_marks = np.arange(len(classes))
        plt.xticks(tick_marks, classes)
        plt.yticks(tick_marks, classes)

        thresh = cm.max() / 2.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                plt.text(
                    j,
                    i,
                    format(cm[i, j], "d"),
                    ha="center",
                    va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontweight="bold",
                )

        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        cm_path = self.plots_dir / f"confusion_matrix_{model_name}.png"
        plt.savefig(cm_path, dpi=300)
        plt.close()

        logger.info(f"Saved ROC, PR, and Confusion Matrix charts for '{model_name}'.")
