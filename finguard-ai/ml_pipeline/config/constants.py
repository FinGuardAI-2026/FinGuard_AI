"""
ml_pipeline/config/constants.py
────────────────────────────────
Domain-level constants shared across modules.
Centralising them here prevents typos from spreading through the codebase
and makes future schema changes a single-file update.
"""

# ── Target Label ──────────────────────────────────────────────────────────────
TARGET_COLUMN   = "is_fraud"
FRAUD_LABEL     = 1
GENUINE_LABEL   = 0

# ── Column Groups ─────────────────────────────────────────────────────────────
NUMERIC_COLUMNS = [
    "amount",
    "latitude",
    "longitude",
]

CATEGORICAL_COLUMNS = [
    "merchant_category",
    "payment_method",
    "transaction_type",
    "country",
    "currency",
    "browser",
    "operating_system",
]

DATETIME_COLUMNS = [
    "transaction_time",
    "created_at",
]

HIGH_CARDINALITY_THRESHOLD = 50  # Unique-value count above which a column is
                                  # considered high-cardinality and may need
                                  # special encoding strategies.

# ── Risk Classification Thresholds ────────────────────────────────────────────
RISK_LOW_MAX      = 30
RISK_MEDIUM_MAX   = 60
RISK_HIGH_MAX     = 85
# Scores above RISK_HIGH_MAX are Critical


# ── Investigation Lifecycle States ───────────────────────────────────────────
INVESTIGATION_STATUSES = [
    "PENDING_REVIEW",
    "UNDER_REVIEW",
    "CONFIRMED_FRAUD",
    "FALSE_POSITIVE",
    "ESCALATED",
    "RESOLVED",
]


# ── Model Artefact Filenames ──────────────────────────────────────────────────
MODEL_FILENAMES = {
    "logistic_regression": "logistic_regression.joblib",
    "decision_tree":       "decision_tree.joblib",
    "random_forest":       "random_forest.joblib",
    "xgboost":             "xgboost.joblib",
    "lightgbm":            "lightgbm.joblib",
    "champion":            "champion_model.joblib",
    "preprocessor":        "preprocessor.joblib",
}


# ── Report & Figure Filenames ────────────────────────────────────────────────
REPORT_DATASET_SUMMARY   = "dataset_summary.md"
REPORT_DATASET_STATS     = "dataset_statistics.json"
REPORT_MODEL_COMPARISON  = "model_comparison.json"
FIGURE_CONFUSION_MATRIX  = "confusion_matrix_{model}.png"
FIGURE_ROC_CURVE         = "roc_curve_{model}.png"
FIGURE_SHAP_SUMMARY      = "shap_summary_{model}.png"
FIGURE_FEATURE_IMPORTANCE = "feature_importance_{model}.png"
