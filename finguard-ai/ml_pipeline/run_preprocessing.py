"""
ml_pipeline/run_preprocessing.py
────────────────────────────────
Runs the complete feature selection, outlier handling, scaling comparisons,
resampling comparisons, splits dataset, fits the pipeline, and saves report documents.
"""
import sys
import os
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import joblib

# Add project root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ml_pipeline.preprocessing.data_loader import DataLoader
from ml_pipeline.preprocessing.pipeline import FraudPreprocessor
from ml_pipeline.preprocessing.outliers import IQROutlierCapper, Winsorizer
from ml_pipeline.preprocessing.feature_selection import FeatureSelector
from ml_pipeline.preprocessing.imbalance import ImbalanceHandler
from ml_pipeline.utils.logger import get_logger
from ml_pipeline.utils.file_utils import save_json, save_joblib
from ml_pipeline.config.paths import paths

logger = get_logger("run_preprocessing")


def run_scaling_comparison(X_train: pd.DataFrame) -> dict:
    """Compares StandardScaler, MinMaxScaler, and RobustScaler output properties."""
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

    results = {}
    # amount_col = "Amount" if "Amount" in X_train.columns else (X_train.columns[0] if len(X_train.columns) > 0 else "")
    if "Amount" in X_train.columns:
        amount_col = "Amount"
    elif "amount" in X_train.columns:
        amount_col = "amount"
    else:
        numeric_cols = X_train.select_dtypes(include=["number"]).columns.tolist()
        amount_col = numeric_cols[0] if numeric_cols else ""
    if amount_col:
        series = X_train[amount_col].dropna().values.reshape(-1, 1)

        std = StandardScaler().fit_transform(series)
        mms = MinMaxScaler().fit_transform(series)
        rbs = RobustScaler().fit_transform(series)

        results[amount_col] = {
            "original_range": [float(series.min()), float(series.max())],
            "standard_scaler": {
                "mean": float(std.mean()),
                "std": float(std.std()),
                "range": [float(std.min()), float(std.max())],
            },
            "minmax_scaler": {
                "mean": float(mms.mean()),
                "std": float(mms.std()),
                "range": [float(mms.min()), float(mms.max())],
            },
            "robust_scaler": {
                "median": float(np.median(rbs)),
                "iqr_range": [float(rbs.min()), float(rbs.max())],
            },
        }

    return results


def run_outlier_comparison(X_train: pd.DataFrame) -> dict:
    """Compares values capped by IQR Outlier Capper vs Winsorizer."""
    # amount_col = "Amount" if "Amount" in X_train.columns else (X_train.columns[0] if len(X_train.columns) > 0 else "")
    if "Amount" in X_train.columns:
        amount_col = "Amount"
    elif "amount" in X_train.columns:
        amount_col = "amount"
    else:
        numeric_cols = X_train.select_dtypes(include=["number"]).columns.tolist()
        amount_col = numeric_cols[0] if numeric_cols else ""
    results = {}

    if amount_col:
        series = X_train[[amount_col]].dropna()

        # Fit IQR
        iqr_capper = IQROutlierCapper(factor=1.5).fit(series)
        iqr_capped = iqr_capper.transform(series)
        iqr_lower, iqr_upper = iqr_capper.bounds_[amount_col]

        # Fit Winsorizer
        winsorizer = Winsorizer(lower_quantile=0.01, upper_quantile=0.99).fit(series)
        win_capped = winsorizer.transform(series)
        win_lower, win_upper = winsorizer.bounds_[amount_col]

        # Count capped elements
        iqr_capped_count = int(((series[amount_col] < iqr_lower) | (series[amount_col] > iqr_upper)).sum())
        win_capped_count = int(((series[amount_col] < win_lower) | (series[amount_col] > win_upper)).sum())

        results[amount_col] = {
            "iqr": {
                "bounds": [iqr_lower, iqr_upper],
                "capped_count": iqr_capped_count,
            },
            "winsorization": {
                "bounds": [win_lower, win_upper],
                "capped_count": win_capped_count,
            },
        }

    return results


def compile_preprocessing_report(
    summary_data: dict,
    mi_rankings: list,
    outlier_comp: dict,
    scaling_comp: dict,
    imbalance_comp: dict,
    output_dir: Path,
) -> None:
    """Saves preprocessing_report.md and feature_engineering_report.md summarizing runs."""
    pre_path = output_dir / "preprocessing_report.md"
    feat_path = output_dir / "feature_engineering_report.md"

    # Preprocessing Report Builder
    pre_content = []
    pre_content.append("# FinGuard AI – Data Preprocessing Report")
    pre_content.append("")
    pre_content.append(f"- **Total Rows Deduplicated**: {summary_data['original_shape'][0] - summary_data['deduplicated_shape'][0]:,}")
    pre_content.append(f"- **Final Preprocessing Shape**: {summary_data['deduplicated_shape']}")
    pre_content.append("")
    pre_content.append("## Outlier Capping Comparison")
    pre_content.append("")
    pre_content.append("| Feature | Method | Lower Bound | Upper Bound | Records Capped |")
    pre_content.append("| :--- | :--- | :--- | :--- | :--- |")
    for f, details in outlier_comp.items():
        pre_content.append(
            f"| `{f}` | IQR Capper | {details['iqr']['bounds'][0]:.2f} | {details['iqr']['bounds'][1]:.2f} | "
            f"{details['iqr']['capped_count']:,} |"
        )
        pre_content.append(
            f"| `{f}` | Winsorizer (1%-99%) | {details['winsorization']['bounds'][0]:.2f} | {details['winsorization']['bounds'][1]:.2f} | "
            f"{details['winsorization']['capped_count']:,} |"
        )
    pre_content.append("")
    pre_content.append("## Scaling Performance Comparison")
    pre_content.append("")
    for f, details in scaling_comp.items():
        pre_content.append(f"### Feature: `{f}`")
        pre_content.append(f"- **Raw Range**: `[{details['original_range'][0]:.2f}, {details['original_range'][1]:.2f}]`")
        pre_content.append(f"- **StandardScaler**: Range `[{details['standard_scaler']['range'][0]:.2f}, {details['standard_scaler']['range'][1]:.2f}]` (Mean: {details['standard_scaler']['mean']:.2f}, Std: {details['standard_scaler']['std']:.2f})")
        pre_content.append(f"- **MinMaxScaler**: Range `[{details['minmax_scaler']['range'][0]:.2f}, {details['minmax_scaler']['range'][1]:.2f}]` (Mean: {details['minmax_scaler']['mean']:.2f}, Std: {details['minmax_scaler']['std']:.2f})")
        pre_content.append(f"- **RobustScaler**: Median centered near `{details['robust_scaler']['median']:.2f}`, Range `[{details['robust_scaler']['iqr_range'][0]:.2f}, {details['robust_scaler']['iqr_range'][1]:.2f}]`")
    pre_content.append("")
    pre_content.append("### Scaler Recommendation")
    pre_content.append(f"- **Recommended Scaler**: `{summary_data['recommended_scaler'].upper()}`")
    pre_content.append("> [!TIP]")
    pre_content.append("> **RobustScaler** is recommended because transaction amount displays extreme outlier ranges which would shrink variance of standard scales down to near-zero.")
    pre_content.append("")

    # Feature Engineering Report Builder
    feat_content = []
    feat_content.append("# FinGuard AI – Feature Selection & Engineering Report")
    feat_content.append("")
    feat_content.append("## Resampling Balancing Strategies Comparison")
    feat_content.append("")
    feat_content.append("| Strategy | Train Shape | Genuine Count | Fraud Count | Ratio |")
    feat_content.append("| :--- | :--- | :--- | :--- | :--- |")
    o_dist = imbalance_comp["original"]["distribution"]
    feat_content.append(f"| Original | {imbalance_comp['original']['shape']} | {o_dist.get('0', 0):,} | {o_dist.get('1', 0):,} | 1:{int(o_dist.get('0',0)/o_dist.get('1',1))} |")
    ros_dist = imbalance_comp["random_over_sampling"]["distribution"]
    feat_content.append(f"| Random Over Sampler (ROS) | {imbalance_comp['random_over_sampling']['shape']} | {ros_dist.get('0', 0):,} | {ros_dist.get('1', 0):,} | 1:1 |")
    rus_dist = imbalance_comp["random_under_sampling"]["distribution"]
    feat_content.append(f"| Random Under Sampler (RUS) | {imbalance_comp['random_under_sampling']['shape']} | {rus_dist.get('0', 0):,} | {rus_dist.get('1', 0):,} | 1:1 |")
    if "smote" in imbalance_comp:
        s_dist = imbalance_comp["smote"]["distribution"]
        feat_content.append(f"| SMOTE | {imbalance_comp['smote']['shape']} | {s_dist.get('0', 0):,} | {s_dist.get('1', 0):,} | 1:1 |")
    feat_content.append("")
    feat_content.append(f"- **Recommended Resampling Strategy**: `{summary_data['recommended_balancing'].upper()}`")
    feat_content.append("")
    feat_content.append("## Feature Relevance Rankings (Mutual Information)")
    feat_content.append("")
    feat_content.append("| Rank | Feature Name | Mutual Information Score |")
    feat_content.append("| :--- | :--- | :--- |")
    for idx, (f, score) in enumerate(mi_rankings[:15]):
        feat_content.append(f"| {idx+1} | `{f}` | {score:.6f} |")
    feat_content.append("")
    feat_content.append(f"- **Dropped Constant Columns**: {summary_data['dropped_constant_columns']}")
    feat_content.append(f"- **Dropped Collinear Columns**: {summary_data['dropped_collinear_columns']}")
    feat_content.append("")

    with open(pre_path, "w", encoding="utf-8") as f:
        f.write("\n".join(pre_content))
    with open(feat_path, "w", encoding="utf-8") as f:
        f.write("\n".join(feat_content))

    logger.info("Markdown report files written.")


def main() -> int:
    """Preprocesses dataset, analyzes scaler/outlier metrics, saves pipeline preprocessor.joblib."""
    logger.info("Initializing Preprocessing Pipeline Script...")

    reports_dir = Path("ml_pipeline/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load raw dataset
        loader = DataLoader()
        df = loader.load_dataset()
        original_shape = df.shape

        # 2. Duplicate Removal
        df_clean = df.drop_duplicates()
        deduplicated_shape = df_clean.shape
        logger.info(f"Deduplication complete. Rows removed: {original_shape[0] - deduplicated_shape[0]}")

        target_col = "Class" if "Class" in df_clean.columns else "is_fraud"

        # 3. Train/Test Split (80/20 default)
        # X = df_clean.drop(columns=[target_col])
        drop_cols = [target_col]
        if "transaction_id" in df_clean.columns:
            drop_cols.append("transaction_id")
        X = df_clean.drop(columns=drop_cols)
        y = df_clean[target_col]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )
        logger.info(f"Stratified Split Complete. X_train: {X_train.shape}, X_test: {X_test.shape}")

        # 4. Outliers analysis
        outlier_comp = run_outlier_comparison(X_train)

        # 5. Scalers analysis
        scaling_comp = run_scaling_comparison(X_train)

        # 6. Class Imbalance Resampling comparison
        imbalance_handler = ImbalanceHandler(random_state=42)
        imbalance_comp = imbalance_handler.compare_strategies(X_train, y_train)
        recommended_balancing = imbalance_handler.recommend_strategy(X_train, y_train)

        # 7. Feature Selection rankings
        selector = FeatureSelector(target_column=target_col)
        dropped_const = selector.compute_variance_threshold(df_clean, threshold=0.0)
        dropped_coll = selector.compute_correlation_based_selection(df_clean, threshold=0.90)
        mi_rankings = selector.compute_mutual_information(df_clean)

        # Recommend Scaler
        recommended_scaler = "robust"  # High outlier rate typical in fraud amount

        # Save summary JSON
        summary_data = {
            "original_shape": original_shape,
            "deduplicated_shape": deduplicated_shape,
            "train_shape": X_train.shape,
            "test_shape": X_test.shape,
            "recommended_scaler": recommended_scaler,
            "recommended_balancing": recommended_balancing,
            "dropped_constant_columns": dropped_const,
            "dropped_collinear_columns": dropped_coll,
        }
        save_json(summary_data, reports_dir / "preprocessing_summary.json")

        # 8. Fit Final Pipeline preprocessor
        preprocessor = FraudPreprocessor(
            scaler_type=recommended_scaler,
            outlier_method="iqr",
            target_col=target_col,
        )
        preprocessor.fit(X_train)

        # Transform split datasets
        X_train_trans = preprocessor.transform(X_train)
        X_test_trans = preprocessor.transform(X_test)

        # 9. Save preprocessor object
        models_dir = Path("ml_pipeline/models")
        models_dir.mkdir(parents=True, exist_ok=True)
        save_joblib(preprocessor, models_dir / "preprocessor.joblib")

        # 10. Generate Markdown Reports
        compile_preprocessing_report(
            summary_data=summary_data,
            mi_rankings=mi_rankings,
            outlier_comp=outlier_comp,
            scaling_comp=scaling_comp,
            imbalance_comp=imbalance_comp,
            output_dir=reports_dir,
        )

        logger.info("Preprocessing step finished successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"FileNotFound: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation failure: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
