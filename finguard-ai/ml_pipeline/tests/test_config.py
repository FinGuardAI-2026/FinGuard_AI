"""
ml_pipeline/tests/test_config.py
────────────────────────────────
Verifies that configuration structures are frozen, split ratios are consistent,
and paths are resolved and initialized correctly.
"""
import pytest
from dataclasses import FrozenInstanceError
from pathlib import Path


def test_config_immutability():
    """Asserts that configuration parameters are frozen and cannot be mutated at runtime."""
    from ml_pipeline.config.config import config

    with pytest.raises(FrozenInstanceError):
        config.random_seed = 999  # type: ignore


def test_config_split_proportions():
    """Asserts that train, validation, and test split ratios sum exactly to 1.0."""
    from ml_pipeline.config.config import config

    total_split = config.train_size + config.val_size + config.test_size
    assert abs(total_split - 1.0) < 1e-9


def test_config_model_list():
    """Asserts that all five required ML models are registered in the config."""
    from ml_pipeline.config.config import config

    expected_models = {
        "logistic_regression",
        "decision_tree",
        "random_forest",
        "xgboost",
        "lightgbm",
    }
    assert set(config.model_names) == expected_models


def test_path_manager_structure():
    """Asserts that PathManager correctly initializes all required workspace directory nodes."""
    from ml_pipeline.config.paths import paths

    assert isinstance(paths.workspace_root, Path)
    assert paths.raw_data_dir.is_dir()
    assert paths.processed_data_dir.is_dir()
    assert paths.models_dir.is_dir()
    assert paths.experiments_dir.is_dir()
    assert paths.figures_dir.is_dir()
    assert paths.reports_dir.is_dir()
    assert paths.logs_dir.is_dir()
