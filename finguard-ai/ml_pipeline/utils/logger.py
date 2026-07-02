"""
ml_pipeline/utils/logger.py
───────────────────────────
Configures the logger for the ML Pipeline, handling console and file logging.
"""
import logging
import sys
from pathlib import Path
from ml_pipeline.config.paths import paths
from ml_pipeline.config.config import config


def get_logger(name: str) -> logging.Logger:
    """
    Initializes and returns a configured Logger instance.

    Sets up:
    - A FileHandler targeting 'ml_pipeline/logs/ml_pipeline.log'.
    - A StreamHandler writing to stdout.
    - Formatting with timestamps, levels, and logger origin.
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers if already configured
    if logger.hasHandlers():
        return logger

    logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))

    # Standard formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s [%(name)s:%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (ml_pipeline/logs/ml_pipeline.log)
    log_file = paths.log_file_path
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        # Fallback if log directory/file cannot be written
        print(f"Warning: Failed to initialize file logging at '{log_file}': {e}", file=sys.stderr)

    return logger
