"""
ml_pipeline/tests/test_data_loader.py
─────────────────────────────────────
Unit tests validating DataLoader's file loading and schema checks.
"""
import pytest
import pandas as pd
from pathlib import Path

from ml_pipeline.preprocessing.data_loader import DataLoader
from ml_pipeline.config.config import config


def test_loader_raises_file_not_found(tmp_path):
    """DataLoader should raise FileNotFoundError if CSV file is not present."""
    nonexistent = tmp_path / "ghost.csv"
    loader = DataLoader(raw_data_path=nonexistent)
    with pytest.raises(FileNotFoundError, match="not found on disk"):
        loader.load_dataset()


def test_loader_raises_value_error_on_empty_csv(tmp_path):
    """DataLoader should raise ValueError if the loaded CSV is empty."""
    empty_csv = tmp_path / "empty.csv"
    # Create empty file
    empty_csv.write_text("")

    loader = DataLoader(raw_data_path=empty_csv)
    with pytest.raises(ValueError):
        loader.load_dataset()


def test_loader_raises_value_error_on_missing_columns(tmp_path):
    """DataLoader should raise ValueError if required columns are missing."""
    bad_csv = tmp_path / "bad.csv"
    # Write a DataFrame missing the target column 'is_fraud'
    df = pd.DataFrame({
        "transaction_id": ["tx-1"],
        "amount": [10.0],
        "merchant_category": ["SHOPPING"],
        "payment_method": ["CARD"],
        "transaction_type": ["PURCHASE"],
        "country": ["USA"],
    })
    df.to_csv(bad_csv, index=False)

    loader = DataLoader(raw_data_path=bad_csv)
    with pytest.raises(ValueError, match="missing required columns"):
        loader.load_dataset()


def test_loader_success_on_valid_csv(tmp_path):
    """DataLoader should successfully return a DataFrame when all required columns exist."""
    valid_csv = tmp_path / "valid.csv"
    # Construct complete minimal valid schema
    data = {col: ["test_val" if col != "amount" and col != "is_fraud" else 1.0 if col == "amount" else 0]
            for col in config.required_columns}
    df = pd.DataFrame(data)
    df.to_csv(valid_csv, index=False)

    loader = DataLoader(raw_data_path=valid_csv)
    loaded_df = loader.load_dataset()
    assert not loaded_df.empty
    assert loaded_df.shape[0] == 1
    assert "is_fraud" in loaded_df.columns
