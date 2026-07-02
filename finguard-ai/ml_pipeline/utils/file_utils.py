"""
ml_pipeline/utils/file_utils.py
───────────────────────────────
Generic file system operations for serialization and deserialization
of configurations, models, reports, and execution statistics.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Union
import joblib

from ml_pipeline.utils.logger import get_logger

logger = get_logger(__name__)


def save_json(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 4) -> None:
    """Serializes a dictionary to a JSON file, creating parent folders if necessary."""
    path = Path(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, default=str)
        logger.info(f"Successfully saved JSON to '{path}'")
    except Exception as e:
        logger.error(f"Error saving JSON to '{path}': {e}")
        raise


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Deserializes a JSON file into a dictionary."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file '{path}' does not exist.")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from '{path}': {e}")
        raise


def save_joblib(obj: Any, file_path: Union[str, Path]) -> None:
    """Saves a Python object (model, pipeline, etc.) using joblib."""
    path = Path(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(obj, path)
        logger.info(f"Successfully saved joblib artifact to '{path}'")
    except Exception as e:
        logger.error(f"Error saving joblib artifact to '{path}': {e}")
        raise


def load_joblib(file_path: Union[str, Path]) -> Any:
    """Loads a serialized Python object using joblib."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Joblib artifact '{path}' does not exist.")
    try:
        return joblib.load(path)
    except Exception as e:
        logger.error(f"Error loading joblib artifact from '{path}': {e}")
        raise
