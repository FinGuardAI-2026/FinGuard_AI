"""
ml_pipeline/preprocessing/data_loader.py
────────────────────────────────────────
Validating and loading raw CSV datasets into Pandas DataFrames.
"""
from pathlib import Path
from typing import Union
import pandas as pd

from ml_pipeline.config.config import config
from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class DataLoader:
    """
    Handles CSV loading, format validation, and verification of columns.
    """

    def __init__(self, raw_data_path: Union[str, Path] = None) -> None:
        from ml_pipeline.config.paths import paths
        self.data_path = Path(raw_data_path) if raw_data_path else paths.raw_data_path

    def load_dataset(self) -> pd.DataFrame:
        """
        Loads the CSV file from disk and validates it.

        Raises:
            FileNotFoundError: If the CSV file is missing.
            ValueError: If the dataset fails validation (e.g. missing columns).
        """
        logger.info(f"Attempting to load raw dataset from '{self.data_path}'...")

        if not self.data_path.is_file():
            err_msg = f"Dataset file '{self.data_path}' not found on disk. Please place it there."
            logger.error(err_msg)
            raise FileNotFoundError(err_msg)

        try:
            df = pd.read_csv(self.data_path)
            logger.info(f"Successfully read CSV file. Dimensions: {df.shape[0]} rows x {df.shape[1]} columns.")
        except Exception as e:
            err_msg = f"Error reading CSV file at '{self.data_path}': {e}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        self.validate_dataset(df)
        return df

    def validate_dataset(self, df: pd.DataFrame) -> None:
        """
        Validates the schema of the loaded dataset.

        Asserts that:
        - The DataFrame is not empty.
        - All required columns defined in MLConfig are present.
        """
        if df.empty:
            err_msg = "Validation failed: Loaded dataset is empty."
            logger.error(err_msg)
            raise ValueError(err_msg)

        # Check required columns
        missing_cols = [col for col in config.required_columns if col not in df.columns]
        if missing_cols:
            err_msg = (
                f"Validation failed: The dataset is missing required columns: {missing_cols}. "
                f"Available columns are: {list(df.columns)}"
            )
            logger.error(err_msg)
            raise ValueError(err_msg)

        logger.info("Dataset schema validation passed successfully.")
