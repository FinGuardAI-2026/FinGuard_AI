"""
ml_pipeline/preprocessing/outliers.py
─────────────────────────────────────
Custom scikit-learn transformers for outlier treatment.
Implements IQR boundary capping and percentile-based Winsorization.
"""
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class IQROutlierCapper(BaseEstimator, TransformerMixin):
    """
    Caps numeric feature outliers to upper and lower bounds computed using the 1.5 IQR rule.

    Calculates limits on train set to prevent lookahead bias during transform.
    """

    def __init__(self, factor: float = 1.5, columns: Optional[List[str]] = None) -> None:
        self.factor = factor
        self.columns = columns
        self.bounds_: Dict[str, Tuple[float, float]] = {}

    def fit(self, X: pd.DataFrame, y: Optional[Union[pd.Series, np.ndarray]] = None) -> "IQROutlierCapper":
        self.bounds_ = {}
        cols = self.columns if self.columns is not None else X.select_dtypes(include=[np.number]).columns

        for col in cols:
            q25 = X[col].quantile(0.25)
            q75 = X[col].quantile(0.75)
            iqr = q75 - q25
            lower = q25 - (self.factor * iqr)
            upper = q75 + (self.factor * iqr)
            self.bounds_[col] = (float(lower), float(upper))

        logger.info(f"IQROutlierCapper fitted on {len(self.bounds_)} column(s).")
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_out = X.copy()
        for col, (lower, upper) in self.bounds_.items():
            if col in X_out.columns:
                X_out[col] = np.clip(X_out[col], lower, upper)
        return X_out


class Winsorizer(BaseEstimator, TransformerMixin):
    """
    Caps numeric features to specific percentile thresholds (e.g. 1st and 99th percentiles).
    """

    def __init__(
        self,
        lower_quantile: float = 0.01,
        upper_quantile: float = 0.99,
        columns: Optional[List[str]] = None,
    ) -> None:
        self.lower_quantile = lower_quantile
        self.upper_quantile = upper_quantile
        self.columns = columns
        self.bounds_: Dict[str, Tuple[float, float]] = {}

    def fit(self, X: pd.DataFrame, y: Optional[Union[pd.Series, np.ndarray]] = None) -> "Winsorizer":
        self.bounds_ = {}
        cols = self.columns if self.columns is not None else X.select_dtypes(include=[np.number]).columns

        for col in cols:
            lower = X[col].quantile(self.lower_quantile)
            upper = X[col].quantile(self.upper_quantile)
            self.bounds_[col] = (float(lower), float(upper))

        logger.info(
            f"Winsorizer fitted on {len(self.bounds_)} column(s) with thresholds "
            f"[{self.lower_quantile * 100}%, {self.upper_quantile * 100}%]."
        )
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_out = X.copy()
        for col, (lower, upper) in self.bounds_.items():
            if col in X_out.columns:
                X_out[col] = np.clip(X_out[col], lower, upper)
        return X_out
