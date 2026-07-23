import joblib
from pathlib import Path

MODELS_DIR = Path("ml_pipeline/models")

print("=" * 60)

# Load preprocessor
preprocessor = joblib.load(MODELS_DIR / "preprocessor.joblib")

print("PREPROCESSOR TYPE:")
print(type(preprocessor))

print("=" * 60)

# feature_cols_
print("\nfeature_cols_")
print(getattr(preprocessor, "feature_cols_", "NOT FOUND"))

# numeric_cols_
print("\nnumeric_cols_")
print(getattr(preprocessor, "numeric_cols_", "NOT FOUND"))

# categorical_cols_
print("\ncategorical_cols_")
print(getattr(preprocessor, "categorical_cols_", "NOT FOUND"))

print("=" * 60)

# Load model
model = joblib.load(MODELS_DIR / "xgboost.joblib")

print("MODEL TYPE:")
print(type(model))

print("\nfeature_names_in_")
print(getattr(model, "feature_names_in_", "NOT FOUND"))