"""
ml_pipeline/preprocessing/feature_selection.py
─────────────────────────────────────────────
Implements variance-threshold filters, pairwise correlation dropping,
and Mutual Information ranking with the target variable.
"""
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_selection import VarianceThreshold, mutual_info_classif

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class FeatureSelector:
    """
    Ranks and selects features using statistics and mutual information.
    """

    def __init__(self, target_column: str = "Class") -> None:
        self.target_column = target_column

    def compute_variance_threshold(self, df: pd.DataFrame, threshold: float = 0.0) -> List[str]:
        """Identifies features that fall below a given variance threshold."""
        numeric_df = df.select_dtypes(include=[np.number])
        if self.target_column in numeric_df.columns:
            numeric_df = numeric_df.drop(columns=[self.target_column])

        selector = VarianceThreshold(threshold=threshold)
        selector.fit(numeric_df)

        low_variance_cols = [
            col for col, var in zip(numeric_df.columns, selector.variances_)
            if var <= threshold
        ]
        logger.info(f"Identified {len(low_variance_cols)} low-variance feature(s) at threshold {threshold}.")
        return low_variance_cols

    def compute_correlation_based_selection(self, df: pd.DataFrame, threshold: float = 0.85) -> List[str]:
        """
        Identifies highly correlated feature pairs and suggests one for removal.
        """
        numeric_df = df.select_dtypes(include=[np.number])
        if self.target_column in numeric_df.columns:
            numeric_df = numeric_df.drop(columns=[self.target_column])

        corr_matrix = numeric_df.corr().abs()
        upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

        to_drop = [column for column in upper_tri.columns if any(upper_tri[column] > threshold)]
        logger.info(f"Identified {len(to_drop)} collinear feature(s) exceeding threshold {threshold}.")
        return to_drop

    def compute_mutual_information(self, df: pd.DataFrame) -> List[Tuple[str, float]]:
        """
        Computes Mutual Information scores between each numeric feature and the target.

        Returns:
            List of (feature_name, mi_score) tuples sorted in descending order of score.
        """
        if self.target_column not in df.columns:
            logger.warning(f"Target column '{self.target_column}' not found. Cannot calculate Mutual Info.")
            return []

        numeric_df = df.select_dtypes(include=[np.number])
        # Handle null values by backfilling/forward-filling temporarily for calculation
        filled_df = numeric_df.fillna(numeric_df.median())

        X = filled_df.drop(columns=[self.target_column])
        y = filled_df[self.target_column]

        logger.info("Computing Mutual Information scores (this may take a few seconds)...")
        mi_scores = mutual_info_classif(X, y, random_state=42)

        rankings = [(col, float(score)) for col, score in zip(X.columns, mi_scores)]
        rankings.sort(key=lambda x: x[1], reverse=True)

        logger.info("Mutual Information scores computed successfully.")
        return rankings
