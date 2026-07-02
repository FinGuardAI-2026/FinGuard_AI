"""
ml_pipeline/utils/visualization_utils.py
────────────────────────────────────────
Visualization helpers to save ROC curves, confusion matrices, and feature importance
plots. Safe for headless environments (uses Agg backend).
"""
from pathlib import Path
from typing import List, Union
import matplotlib
# Use non-interactive backend for headless CLI environments
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def plot_class_distribution(
    labels: List[str],
    counts: List[int],
    output_path: Union[str, Path],
    title: str = "Class Distribution",
) -> None:
    """Plots a simple bar chart of class counts and saves it to a file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 4))
    bars = plt.bar(labels, counts, color=["#3B82F6", "#EF4444"])
    plt.title(title, fontsize=12, fontweight="bold")
    plt.ylabel("Number of Transactions")
    plt.xlabel("Class")

    # Add count labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2.0,
            yval + (max(counts) * 0.01),
            f"{yval:,}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()
    logger.info(f"Saved class distribution plot to '{path}'")


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str],
    output_path: Union[str, Path],
    title: str = "Confusion Matrix",
) -> None:
    """Plots a confusion matrix and saves it to a file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(6, 6))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title(title, fontsize=12, fontweight="bold")
    plt.colorbar()

    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)

    # Annotate numbers in cells
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
    plt.savefig(path, dpi=300)
    plt.close()
    logger.info(f"Saved confusion matrix plot to '{path}'")


def plot_roc_curve(
    fpr: np.ndarray,
    tpr: np.ndarray,
    roc_auc: float,
    output_path: Union[str, Path],
    title: str = "Receiver Operating Characteristic (ROC)",
) -> None:
    """Plots the ROC curve and saves it to a file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7, 6))
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(title, fontsize=12, fontweight="bold")
    plt.legend(loc="lower right")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()
    logger.info(f"Saved ROC curve plot to '{path}'")


def plot_feature_importance(
    feature_names: List[str],
    importances: List[float],
    output_path: Union[str, Path],
    title: str = "Feature Importance",
    top_n: int = 15,
) -> None:
    """Plots feature importance as a horizontal bar chart and saves it to a file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Sort indices
    indices = np.argsort(importances)[::-1][:top_n]
    sorted_features = [feature_names[i] for i in indices]
    sorted_importances = [importances[i] for i in indices]

    plt.figure(figsize=(10, 6))
    y_pos = np.arange(len(sorted_features))
    plt.barh(y_pos, sorted_importances, align="center", color="#3B82F6")
    plt.yticks(y_pos, sorted_features)
    plt.gca().invert_yaxis()  # top-down view
    plt.xlabel("Importance Score")
    plt.title(title, fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()
    logger.info(f"Saved feature importance plot to '{path}'")
