"""
ml_pipeline/tests/test_preprocessing.py
────────────────────────────────────────
Unit tests verifying the preprocessing pipeline, outlier cappers,
feature selectors, and class imbalance handlers.
"""
import pytest
import pandas as pd
import numpy as np

from ml_pipeline.preprocessing.outliers import IQROutlierCapper, Winsorizer
from ml_pipeline.preprocessing.pipeline import FraudPreprocessor
from ml_pipeline.preprocessing.feature_selection import FeatureSelector
from ml_pipeline.preprocessing.imbalance import ImbalanceHandler


def test_iqr_outlier_capper():
    """IQROutlierCapper should correctly fit outlier bounds and clip values."""
    X = pd.DataFrame({"feat": [1.0, 1.1, 1.05, 1.2, 1.15, 100.0, -100.0]})  # Extreme outliers
    capper = IQROutlierCapper(factor=1.5)
    capper.fit(X)

    lower, upper = capper.bounds_["feat"]
    # Check that bounds are reasonable (excluding 100 and -100)
    assert lower < 1.0
    assert upper > 1.2

    X_trans = capper.transform(X)
    assert X_trans["feat"].max() == upper
    assert X_trans["feat"].min() == lower


def test_winsorizer():
    """Winsorizer should cap elements to defined percentile limits."""
    # 10 values, 10th and 90th percentiles should cap the extremes
    X = pd.DataFrame({"feat": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
    win = Winsorizer(lower_quantile=0.1, upper_quantile=0.9)
    win.fit(X)

    X_trans = win.transform(X)
    assert X_trans["feat"].min() == 2.0  # 10th percentile
    assert X_trans["feat"].max() == 9.0  # 90th percentile


def test_feature_selector_variance():
    """FeatureSelector should correctly flag zero or near-zero variance columns."""
    df = pd.DataFrame({
        "constant_col": [1.0, 1.0, 1.0, 1.0],
        "normal_col": [1.0, 2.0, 3.0, 4.0],
        "Class": [0, 0, 1, 1],
    })

    selector = FeatureSelector(target_column="Class")
    dropped = selector.compute_variance_threshold(df, threshold=0.0)
    assert "constant_col" in dropped
    assert "normal_col" not in dropped


def test_imbalance_handler_oversampler():
    """ImbalanceHandler should successfully equalize minority and majority classes."""
    X = pd.DataFrame({"feat": [1, 2, 3, 4, 5]})
    y = pd.Series([0, 0, 0, 0, 1], name="Class")  # 4 genuine, 1 fraud

    handler = ImbalanceHandler(random_state=42)
    X_res, y_res = handler.resample_ros(X, y)

    assert len(y_res) == 8  # 4 + 4
    assert y_res.value_counts().to_dict() == {0: 4, 1: 4}


def test_preprocessor_pipeline_fit_transform():
    """FraudPreprocessor should impute, cap, scale, and align columns on batch data."""
    X = pd.DataFrame({
        "amount": [10.0, 20.0, np.nan, 40.0],  # Nan should be imputed with median
        "V1": [0.5, 0.6, 0.7, 100.0],          # Outlier should be capped
    })

    preprocessor = FraudPreprocessor(scaler_type="standard", outlier_method="iqr")
    preprocessor.fit(X)

    assert preprocessor.feature_cols_ == ["amount", "V1"]

    X_trans = preprocessor.transform(X)
    assert X_trans.shape == (4, 2)
    # Check that NaN has been filled (no NaNs left)
    assert X_trans["amount"].isnull().sum() == 0
    # Check that outlier is capped and scaled (standard scaler mean ~ 0, std ~ 1)
    assert abs(X_trans["V1"].mean()) < 1e-9
