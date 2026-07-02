"""
ml_pipeline/tests/test_dataset_inspector.py
───────────────────────────────────────────
Unit tests validating DatasetInspector's profiling metrics.
"""
import pytest
import pandas as pd

from ml_pipeline.preprocessing.dataset_inspector import DatasetInspector


def test_inspector_reports_correct_shapes_and_duplicates():
    """DatasetInspector should correctly count rows, columns, duplicate rows, and missing values."""
    df = pd.DataFrame({
        "transaction_id": ["tx-1", "tx-2", "tx-2"],  # 1 duplicate row
        "amount": [10.0, 20.0, 20.0],
        "merchant_category": ["SHOPPING", "FOOD", "FOOD"],
        "payment_method": ["CARD", "CARD", "CARD"],
        "transaction_type": ["PURCHASE", "PURCHASE", "PURCHASE"],
        "country": ["USA", "CAN", "CAN"],
        "is_fraud": [0, 0, 1], # 1 fraud out of 3 total records (33.33%)
    })

    inspector = DatasetInspector(target_column="is_fraud")
    report = inspector.inspect(df)

    assert report["dataset_shape"]["rows"] == 3
    assert report["dataset_shape"]["columns"] == 7
    assert report["duplicate_rows"] == 1
    assert report["columns"]["transaction_id"]["null_count"] == 0
    assert report["columns"]["transaction_id"]["unique_count"] == 2


def test_inspector_calculates_correct_fraud_percentage():
    """DatasetInspector should compute the correct ratio of positive to negative classes."""
    df = pd.DataFrame({
        "transaction_id": ["tx-1", "tx-2", "tx-3", "tx-4"],
        "amount": [10.0, 20.0, 30.0, 40.0],
        "merchant_category": ["FOOD"] * 4,
        "payment_method": ["CARD"] * 4,
        "transaction_type": ["PURCHASE"] * 4,
        "country": ["USA"] * 4,
        "is_fraud": [0, 1, 0, 0],  # 1 fraud out of 4 = 25.0%
    })

    inspector = DatasetInspector(target_column="is_fraud")
    report = inspector.inspect(df)

    assert report["fraud_percentage"] == 25.0
    assert report["class_distribution"]["1"]["count"] == 1
    assert report["class_distribution"]["0"]["count"] == 3


def test_inspector_summary_stats_for_numeric_columns():
    """DatasetInspector should capture summary statistics (mean, min, max) for numeric columns."""
    df = pd.DataFrame({
        "transaction_id": ["tx-1", "tx-2"],
        "amount": [10.0, 50.0],  # Mean = 30.0, Min = 10.0, Max = 50.0
        "merchant_category": ["FOOD", "FOOD"],
        "payment_method": ["CARD", "CARD"],
        "transaction_type": ["PURCHASE", "PURCHASE"],
        "country": ["USA", "USA"],
        "is_fraud": [0, 0],
    })

    inspector = DatasetInspector(target_column="is_fraud")
    report = inspector.inspect(df)

    assert "amount" in report["numeric_summary"]
    assert report["numeric_summary"]["amount"]["mean"] == 30.0
    assert report["numeric_summary"]["amount"]["min"] == 10.0
    assert report["numeric_summary"]["amount"]["max"] == 50.0
