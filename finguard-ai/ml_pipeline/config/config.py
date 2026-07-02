"""
ml_pipeline/config/config.py
────────────────────────────
Centralized, frozen configuration object for the entire ML workspace.
All scripts import from here — no hard-coded paths or magic numbers elsewhere.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MLConfig:
    """
    Immutable ML workspace configuration.

    frozen=True prevents accidental mutation during long training runs.
    """

    # ── Identity ──────────────────────────────────────────────────────────
    project_name: str = "FinGuard AI – Fraud Detection"
    version: str = "1.0.0"

    # ── Reproducibility ───────────────────────────────────────────────────
    random_seed: int = 42

    # ── Dataset ───────────────────────────────────────────────────────────
    raw_data_filename: str = "transactions.csv"
    target_column: str = "is_fraud"

    # Minimum required columns — dataset loader validates these
    required_columns: List[str] = field(default_factory=lambda: [
        "transaction_id",
        "amount",
        "merchant_category",
        "payment_method",
        "transaction_type",
        "country",
        "is_fraud",
    ])

    # ── Train / Validation / Test Split ───────────────────────────────────
    train_size: float = 0.70   # 70 % training
    val_size:   float = 0.15   # 15 % validation
    test_size:  float = 0.15   # 15 % hold-out test

    # ── Models ────────────────────────────────────────────────────────────
    # Names used as keys throughout the pipeline
    model_names: List[str] = field(default_factory=lambda: [
        "logistic_regression",
        "decision_tree",
        "random_forest",
        "xgboost",
        "lightgbm",
    ])

    # ── Evaluation ────────────────────────────────────────────────────────
    primary_metric: str = "f1"       # Champion model selection metric
    cv_folds:       int = 5           # Cross-validation folds

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: str = "INFO"


# Singleton — import this throughout the pipeline
config = MLConfig()
