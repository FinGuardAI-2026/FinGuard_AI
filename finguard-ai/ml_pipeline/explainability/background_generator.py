"""
ml_pipeline/explainability/background_generator.py
─────────────────────────────────────────────────
Utility to generate a representative background dataset for SHAP explanations.
Supports random sampling and k-means summarization from transaction data.
Saves the resulting dataset to ml_pipeline/models/background_data.joblib.
"""
import argparse
import os
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

def generate_background_dataset(
    data_path: Path,
    output_path: Path,
    n_samples: int = 100,
    method: str = "kmeans",
    feature_cols: list = None
) -> None:
    """
    Generates a representative background dataset for SHAP from raw/processed data.
    """
    print(f"Loading transaction dataset from {data_path}...")
    if not data_path.exists():
        # Generate dummy data for fallback utility when no training dataset exists
        print("Dataset not found. Generating realistic synthetic training data to build background model...")
        np.random.seed(42)
        n_dummy = 1000
        dummy_data = {
            "Time": np.random.uniform(0, 172792, n_dummy),
            "Amount": np.random.exponential(88.0, n_dummy)
        }
        for i in range(1, 29):
            dummy_data[f"V{i}"] = np.random.normal(0, 1.0, n_dummy)
        df = pd.DataFrame(dummy_data)
    else:
        if data_path.suffix == ".csv":
            df = pd.read_csv(data_path)
        else:
            df = joblib.load(data_path)

    # Filter to feature columns
    if feature_cols:
        cols = [c for c in feature_cols if c in df.columns]
        df = df[cols]
    else:
        # Default columns matching model training
        cols = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
        cols = [c for c in cols if c in df.columns]
        df = df[cols]

    print(f"Dataset shape: {df.shape}. Generating background dataset using '{method}'...")

    if method == "kmeans":
        try:
            import shap
            # Summarize dataset using k-means
            summary = shap.kmeans(df, n_samples)
            # joblib requires a raw dataframe or standard array representation for serialisation
            background_df = pd.DataFrame(summary.data, columns=df.columns)
        except Exception as e:
            print(f"K-means summarization failed: {e}. Falling back to random sampling.")
            background_df = df.sample(n=min(n_samples, len(df)), random_state=42).copy()
    else:
        background_df = df.sample(n=min(n_samples, len(df)), random_state=42).copy()

    # Ensure output dir exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(background_df, output_path)
    print(f"Success: SHAP background dataset saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SHAP Background Dataset")
    parser.add_argument("--data-path", type=str, default="ml_pipeline/data/processed/creditcard.csv")
    parser.add_argument("--output-path", type=str, default="ml_pipeline/models/background_data.joblib")
    parser.add_argument("--n-samples", type=int, default=100)
    parser.add_argument("--method", type=str, choices=["kmeans", "random"], default="kmeans")
    args = parser.parse_args()

    generate_background_dataset(
        data_path=Path(args.data_path),
        output_path=Path(args.output_path),
        n_samples=args.n_samples,
        method=args.method
    )
