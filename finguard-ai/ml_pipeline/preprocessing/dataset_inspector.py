"""
ml_pipeline/preprocessing/dataset_inspector.py
──────────────────────────────────────────────
Analyzes pandas DataFrames to inspect shape, types, missing values, duplicates,
and label distributions, producing serializable inspection reports.
"""
from typing import Any, Dict
import pandas as pd

from ml_pipeline.config.config import config
from ml_pipeline.utils.logger import get_logger
from ml_pipeline.utils.dataset_utils import calculate_class_distribution

logger = get_logger(__name__)


class DatasetInspector:
    """
    Performs data audit profiles on raw/processed fraud detection datasets.
    """

    def __init__(self, target_column: str = None) -> None:
        self.target_column = target_column or config.target_column

    def inspect(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs full inspection suite on the DataFrame.

        Returns:
            Dict containing shape, types, duplicates, class distributions,
            null values, and numeric statistical summaries.
        """
        logger.info("Executing dataset inspection checks...")

        # Dimensions & Memory
        shape = df.shape
        num_rows, num_cols = shape
        memory_usage_bytes = df.memory_usage(deep=True).sum()
        memory_usage_mb = float(memory_usage_bytes / (1024 * 1024))

        # Duplicates
        duplicate_count = int(df.duplicated().sum())

        # Data types and null counts
        columns_meta = {}
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            null_percentage = float((null_count / num_rows) * 100) if num_rows > 0 else 0.0
            columns_meta[col] = {
                "dtype": str(df[col].dtype),
                "null_count": null_count,
                "null_percentage": null_percentage,
                "unique_count": int(df[col].nunique()),
            }

        # Class distribution if target present
        class_dist = None
        fraud_percentage = None
        if self.target_column in df.columns:
            try:
                class_dist = calculate_class_distribution(df, self.target_column)
                # Assume fraud is represented by 1/true-like values
                fraud_percentage = 0.0
                for k, v in class_dist.items():
                    if k in ("1", "1.0", "True", "true"):
                        fraud_percentage = v["percentage"]
            except Exception as e:
                logger.warning(f"Could not compute target distribution: {e}")

        # Statistical summary for numeric columns
        numeric_summary = {}
        numeric_df = df.select_dtypes(include=["number"])
        if not numeric_df.empty:
            desc = numeric_df.describe().to_dict()
            for col, stats in desc.items():
                numeric_summary[col] = {k: float(v) for k, v in stats.items()}

        inspection_report = {
            "dataset_shape": {
                "rows": num_rows,
                "columns": num_cols,
            },
            "memory_usage_mb": memory_usage_mb,
            "duplicate_rows": duplicate_count,
            "target_column": self.target_column,
            "fraud_percentage": fraud_percentage,
            "class_distribution": class_dist,
            "columns": columns_meta,
            "numeric_summary": numeric_summary,
        }

        logger.info("Dataset inspection completed successfully.")
        return inspection_report
