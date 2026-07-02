"""
ml_pipeline/preprocessing/pipeline.py
─────────────────────────────────────
Unified preprocessing pipeline compatible with scikit-learn pipelines.
Encapsulates missing value imputation, outlier capping, and feature scaling.
Allows deployment using joblib serialization.
"""
from typing import List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

from ml_pipeline.preprocessing.outliers import IQROutlierCapper, Winsorizer
from ml_pipeline.utils.logger import get_logger
from sklearn.preprocessing import OneHotEncoder

logger = get_logger(__name__)


class FraudPreprocessor(BaseEstimator, TransformerMixin):
    """
    Production-ready pipeline combining imputation, outlier treatment, and scaling.

    Stores model artifacts internally for consistent application during batch
    training and online prediction APIs.
    """

    def __init__(
        self,
        scaler_type: str = "robust",
        outlier_method: str = "iqr",
        target_col: str = "Class",
    ) -> None:
        self.scaler_type = scaler_type.lower()
        self.outlier_method = outlier_method.lower()
        self.target_col = target_col

        # Preprocessing sub-transformers
        self.imputer: Optional[SimpleImputer] = None
        self.capper: Optional[Union[IQROutlierCapper, Winsorizer]] = None
        self.scaler: Optional[Union[StandardScaler, MinMaxScaler, RobustScaler]] = None
        self.encoder=None

        # Tracking columns list to enforce alignment at inference
        self.feature_cols_: List[str] = []

    def fit(self, X: pd.DataFrame, y: Optional[Union[pd.Series, np.ndarray]] = None) -> "FraudPreprocessor":
        """Fits imputation weights, outlier bounds, and scaling coefficients."""
        logger.info(
            f"Fitting FraudPreprocessor with scaler={self.scaler_type}, outlier_method={self.outlier_method}"
        )

        # Separate targets if accidentally included
        X_fit = X.copy()
        if self.target_col in X_fit.columns:
            X_fit = X_fit.drop(columns=[self.target_col])

        # Track feature names
        self.feature_cols_ = list(X_fit.columns)

        # Separate numeric and categorical columns
        self.numeric_cols_ = X_fit.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols_ = [c for c in X_fit.columns if c not in self.numeric_cols_]

        # 1. Imputation
        # self.imputer = SimpleImputer(strategy="median")
        # self.imputer.fit(X_fit)
        # X_imputed = pd.DataFrame(self.imputer.transform(X_fit), columns=self.feature_cols_)

        # Impute only numeric columns
        self.imputer = SimpleImputer(strategy="median")
        X_imputed = X_fit.copy()

        if self.numeric_cols_:
            self.imputer.fit(X_fit[self.numeric_cols_])
        X_imputed[self.numeric_cols_] = self.imputer.transform(
            X_fit[self.numeric_cols_]
        )

        # 2. Outlier treatment
        if self.outlier_method == "iqr":
            # self.capper = IQROutlierCapper(factor=1.5, columns=self.feature_cols_)
            self.capper = IQROutlierCapper(
                factor=1.5,
                columns=self.numeric_cols_,
            )
        elif self.outlier_method == "winsorize":
            # self.capper = Winsorizer(lower_quantile=0.01, upper_quantile=0.99, columns=self.feature_cols_)
            self.capper = Winsorizer(
                lower_quantile=0.01,
                upper_quantile=0.99,
                columns=self.numeric_cols_,
            )
        else:
            self.capper = None

        if self.capper:
            # self.capper.fit(X_imputed)
            # X_capped = self.capper.transform(X_imputed)
            X_capped = X_imputed.copy()
            if self.capper and self.numeric_cols_:
                self.capper.fit(X_imputed[self.numeric_cols_])
                X_capped[self.numeric_cols_] = self.capper.transform(
                    X_imputed[self.numeric_cols_]
                )
        else:
            X_capped = X_imputed

        # 3. Scaling
        if self.scaler_type == "standard":
            self.scaler = StandardScaler()
        elif self.scaler_type == "minmax":
            self.scaler = MinMaxScaler()
        else:
            self.scaler = RobustScaler()  # Default: RobustScaler resists outliers best

        # self.scaler.fit(X_capped)
        self.scaler.fit(X_capped[self.numeric_cols_])

        # 4. Fit One-Hot Encoder on categorical columns
        if self.categorical_cols_:
            self.encoder = OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            )
            self.encoder.fit(X_capped[self.categorical_cols_])
        logger.info("FraudPreprocessor fit completed successfully.")
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transforms a raw data frame using fitted parameters."""
        if not self.imputer or not self.scaler:
            raise RuntimeError("FraudPreprocessor must be fitted before running transform.")

        X_trans = X.copy()
        # Drop target column if present
        if self.target_col in X_trans.columns:
            X_trans = X_trans.drop(columns=[self.target_col])

        # Align columns check
        missing_cols = [c for c in self.feature_cols_ if c not in X_trans.columns]
        if missing_cols:
            raise ValueError(f"Input DataFrame is missing expected feature columns: {missing_cols}")

        # Slice/reorder to ensure identical column ordering as fit
        X_trans = X_trans[self.feature_cols_]

        # 1. Impute
        # X_imp = pd.DataFrame(self.imputer.transform(X_trans), columns=self.feature_cols_)
        X_imp = X_trans.copy()
        if self.numeric_cols_:
            X_imp[self.numeric_cols_] = self.imputer.transform(
                X_trans[self.numeric_cols_]
            )

        # 2. Cap outliers
        if self.capper:
            # X_cap = self.capper.transform(X_imp)
            X_cap = X_imp.copy()
            if self.capper and self.numeric_cols_:
                X_cap[self.numeric_cols_] = self.capper.transform(
                    X_imp[self.numeric_cols_]
                )
        else:
            X_cap = X_imp

        # 3. Scale
        # scaled_arr = self.scaler.transform(X_cap)
        # return pd.DataFrame(scaled_arr, columns=self.feature_cols_)
        X_final = X_cap.copy()
        if self.numeric_cols_:
            X_final[self.numeric_cols_] = self.scaler.transform(
                X_cap[self.numeric_cols_]
            )

        # 4. Encode categorical columns
        if self.categorical_cols_:
            encoded = self.encoder.transform(
                X_final[self.categorical_cols_]
            )
            encoded_df = pd.DataFrame(
                encoded,
                columns=self.encoder.get_feature_names_out(self.categorical_cols_),
                index=X_final.index,
            )
            # Keep scaled numeric columns + encoded categorical columns
            X_final = pd.concat(
                [
                    X_final[self.numeric_cols_],
                    encoded_df,
                ],
                axis=1,
            )

        return X_final