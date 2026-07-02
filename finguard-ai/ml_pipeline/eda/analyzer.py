"""
ml_pipeline/eda/analyzer.py
───────────────────────────
Performs non-visual statistical analysis, data quality checks, outlier detection,
and correlation matrix operations on data frames.
"""
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class EDAAnalyzer:
    """
    Computes data audit statistics, metrics, correlations, and outliers.
    """

    def __init__(self, target_column: str = "Class") -> None:
        self.target_column = target_column

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Runs the statistical profiling pipeline on the dataset."""
        logger.info("Starting EDA statistical calculations...")

        results = {
            "overview": self._analyze_overview(df),
            "quality": self._analyze_quality(df),
            "statistics": self._analyze_statistics(df),
            "target": self._analyze_target(df),
            "correlations": self._analyze_correlations(df),
            "outliers": self._analyze_outliers(df),
            "transaction_analysis": self._analyze_transactions(df),
        }

        logger.info("EDA statistical calculations finished.")
        return results

    def _analyze_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Dataset overview statistics."""
        return {
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "total_features": df.shape[1] - (1 if self.target_column in df.columns else 0),
            "feature_names": [col for col in df.columns if col != self.target_column],
            "target_variable": self.target_column if self.target_column in df.columns else None,
            "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }

    def _analyze_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Missing values, duplicates, and constant columns."""
        num_rows = len(df)
        missing_report = {}
        unique_counts = {}
        constant_columns = []

        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            null_pct = float((null_count / num_rows) * 100) if num_rows > 0 else 0.0
            missing_report[col] = {"null_count": null_count, "null_percentage": null_pct}

            u_count = int(df[col].nunique())
            unique_counts[col] = u_count
            if u_count <= 1:
                constant_columns.append(col)

        duplicate_count = int(df.duplicated().sum())

        return {
            "missing_report": missing_report,
            "duplicate_count": duplicate_count,
            "constant_columns": constant_columns,
            "unique_counts": unique_counts,
        }

    def _analyze_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Quartiles, skewness, kurtosis, and basic statistics for numeric columns."""
        stats = {}
        numeric_df = df.select_dtypes(include=[np.number])

        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            if series.empty:
                continue

            q25 = float(series.quantile(0.25))
            q50 = float(series.quantile(0.50))
            q75 = float(series.quantile(0.75))

            # Mode handling (could be multiple, pick the first)
            modes = series.mode()
            mode_val = float(modes.iloc[0]) if not modes.empty else 0.0

            stats[col] = {
                "mean": float(series.mean()),
                "median": float(q50),
                "mode": mode_val,
                "std": float(series.std()) if len(series) > 1 else 0.0,
                "min": float(series.min()),
                "max": float(series.max()),
                "q25": q25,
                "q50": q50,
                "q75": q75,
                "skewness": float(series.skew()) if len(series) > 2 else 0.0,
                "kurtosis": float(series.kurtosis()) if len(series) > 3 else 0.0,
            }

        return stats

    def _analyze_target(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Imbalance ratios for the target class."""
        if self.target_column not in df.columns:
            return {"error": f"Target column '{self.target_column}' is missing from the dataset."}

        counts = df[self.target_column].value_counts().to_dict()
        total = sum(counts.values())

        # Ensure keys are converted to strings for json serialization
        target_stats = {}
        for key, val in counts.items():
            str_key = str(int(key)) if isinstance(key, (int, float, np.integer)) else str(key)
            target_stats[str_key] = {
                "count": int(val),
                "percentage": float((val / total) * 100) if total > 0 else 0.0,
            }

        # Fraud is usually marked as 1
        fraud_count = counts.get(1, counts.get(1.0, counts.get("1", 0)))
        genuine_count = counts.get(0, counts.get(0.0, counts.get("0", 0)))

        imbalance_ratio = float(genuine_count / fraud_count) if fraud_count > 0 else float("inf")

        return {
            "counts": target_stats,
            "fraud_count": int(fraud_count),
            "genuine_count": int(genuine_count),
            "fraud_percentage": float((fraud_count / total) * 100) if total > 0 else 0.0,
            "imbalance_ratio": imbalance_ratio,
        }

    def _analyze_correlations(self, df: pd.DataFrame, threshold: float = 0.5) -> Dict[str, Any]:
        """Computes Pearson correlation and lists strongly correlated features."""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {"correlation_matrix": {}, "highly_correlated_pairs": []}

        corr_matrix = numeric_df.corr(method="pearson")

        # Extract highly correlated pairs
        pairs = []
        cols = corr_matrix.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr_matrix.iloc[i, j]
                if abs(val) >= threshold:
                    pairs.append({
                        "feature_1": cols[i],
                        "feature_2": cols[j],
                        "correlation": float(val),
                    })

        # Sort pairs by absolute correlation strength descending
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        # Convert matrix to serialized dictionary format
        corr_dict = {
            col: {index: float(val) for index, val in row.items()}
            for col, row in corr_matrix.to_dict().items()
        }

        return {
            "correlation_matrix": corr_dict,
            "highly_correlated_pairs": pairs,
        }

    def _analyze_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detects outliers using IQR and Z-score methods."""
        numeric_df = df.select_dtypes(include=[np.number])
        report = {}

        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            if series.empty:
                continue

            # IQR Method
            q25, q75 = series.quantile([0.25, 0.75])
            iqr = q75 - q25
            lower_bound = q25 - (1.5 * iqr)
            upper_bound = q75 + (1.5 * iqr)

            iqr_outliers = series[(series < lower_bound) | (series > upper_bound)]
            iqr_count = len(iqr_outliers)
            iqr_pct = float((iqr_count / len(series)) * 100)

            # Z-Score Method
            mean = series.mean()
            std = series.std()
            z_count = 0
            z_pct = 0.0
            if std > 0:
                z_scores = (series - mean) / std
                z_outliers = series[abs(z_scores) > 3.0]
                z_count = len(z_outliers)
                z_pct = float((z_count / len(series)) * 100)

            report[col] = {
                "iqr": {
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "outlier_count": int(iqr_count),
                    "outlier_percentage": iqr_pct,
                },
                "z_score": {
                    "outlier_count": int(z_count),
                    "outlier_percentage": z_pct,
                },
            }

        return report

    def _analyze_transactions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Dedicated statistics comparing Fraud vs Genuine for Amount and Time."""
        analysis = {}

        # Look for standard Kaggle Credit Card columns
        amount_col = "Amount" if "Amount" in df.columns else ("amount" if "amount" in df.columns else None)
        time_col = "Time" if "Time" in df.columns else ("transaction_time" if "transaction_time" in df.columns else None)

        if self.target_column in df.columns:
            fraud_mask = df[self.target_column] == 1
            gen_mask = df[self.target_column] == 0

            for col_name, col_key in [("amount", amount_col), ("time", time_col)]:
                if col_key:
                    series_f = df.loc[fraud_mask, col_key].dropna()
                    series_g = df.loc[gen_mask, col_key].dropna()

                    analysis[col_name] = {
                        "fraud": {
                            "mean": float(series_f.mean()) if not series_f.empty else 0.0,
                            "median": float(series_f.median()) if not series_f.empty else 0.0,
                            "max": float(series_f.max()) if not series_f.empty else 0.0,
                            "min": float(series_f.min()) if not series_f.empty else 0.0,
                            "total": float(series_f.sum()) if not series_f.empty else 0.0,
                        },
                        "genuine": {
                            "mean": float(series_g.mean()) if not series_g.empty else 0.0,
                            "median": float(series_g.median()) if not series_g.empty else 0.0,
                            "max": float(series_g.max()) if not series_g.empty else 0.0,
                            "min": float(series_g.min()) if not series_g.empty else 0.0,
                            "total": float(series_g.sum()) if not series_g.empty else 0.0,
                        },
                    }

        return analysis
