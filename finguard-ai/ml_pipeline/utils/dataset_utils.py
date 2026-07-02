"""
ml_pipeline/utils/dataset_utils.py
──────────────────────────────────
Dataset-specific manipulation utilities, including stratified splitters
and data balance calculations.
"""
from typing import Tuple, Dict, Any
import pandas as pd
from sklearn.model_selection import train_test_split

from ml_pipeline.config.config import config
from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_class_distribution(df: pd.DataFrame, target_col: str) -> Dict[str, Any]:
    """
    Computes class counts and percentage distributions for the target column.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")

    counts = df[target_col].value_counts()
    percentages = df[target_col].value_counts(normalize=True) * 100

    distribution = {}
    for label in counts.index:
        distribution[str(label)] = {
            "count": int(counts[label]),
            "percentage": float(percentages[label]),
        }
    return distribution


def stratified_split(
    df: pd.DataFrame,
    target_col: str,
    train_size: float = 0.70,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits a DataFrame into Train, Validation, and Test sets using stratified sampling.

    Enforces that train_size + val_size + test_size == 1.0.
    """
    # Quick sanity check on split ratios
    if not abs((train_size + val_size + test_size) - 1.0) < 1e-9:
        raise ValueError("Train, validation, and test split ratios must sum to 1.0.")

    logger.info(
        f"Splitting dataset of size {df.shape[0]} into train ({train_size:.2f}), "
        f"val ({val_size:.2f}), test ({test_size:.2f}) with stratify on '{target_col}'"
    )

    # First split: Separate out the test set
    # test_size is test_size of the total dataset
    val_plus_test_ratio = val_size + test_size
    df_train, df_temp = train_test_split(
        df,
        test_size=val_plus_test_ratio,
        random_state=random_state,
        stratify=df[target_col],
    )

    # Second split: Separate temp (val_plus_test) into val and test
    # test_size / (val_size + test_size) is the fraction of temp that should go to test
    test_ratio_of_temp = test_size / val_plus_test_ratio
    df_val, df_test = train_test_split(
        df_temp,
        test_size=test_ratio_of_temp,
        random_state=random_state,
        stratify=df_temp[target_col],
    )

    logger.info(
        f"Split complete. Train shape: {df_train.shape}, "
        f"Val shape: {df_val.shape}, Test shape: {df_test.shape}"
    )

    return df_train, df_val, df_test
