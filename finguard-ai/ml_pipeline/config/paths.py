"""
ml_pipeline/config/paths.py
───────────────────────────
Dynamic path resolution manager for the ML Pipeline workspace.
Translates logical names into absolute local paths, ensuring all folders
exist automatically when imported.
"""
import os
from pathlib import Path


class PathManager:
    """
    Manages all directory and file paths within the ML workspace.

    Automatically creates missing directories upon instantiation.
    """

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

        # ── Directory Scopes ───────────────────────────────────────────────
        self.data_dir = self.workspace_root / "data"
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"

        self.models_dir = self.workspace_root / "models"
        self.experiments_dir = self.workspace_root / "experiments"
        self.figures_dir = self.workspace_root / "figures"
        self.reports_dir = self.workspace_root / "reports"
        self.logs_dir = self.workspace_root / "logs"

        # Auto-create all required directory nodes
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Helper to create all path nodes if they do not exist."""
        directories = [
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.models_dir,
            self.experiments_dir,
            self.figures_dir,
            self.reports_dir,
            self.logs_dir,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    # ── Derived File Paths ────────────────────────────────────────────────
    @property
    def raw_data_path(self) -> Path:
        """Returns path to the raw input CSV dataset."""
        from ml_pipeline.config.config import config
        return self.raw_data_dir / config.raw_data_filename

    @property
    def log_file_path(self) -> Path:
        """Returns path to the central execution log file."""
        return self.logs_dir / "ml_pipeline.log"


# Instantiated singleton referencing the local folder of this file
CURRENT_FILE_DIR = Path(__file__).resolve().parent
ML_PIPELINE_ROOT = CURRENT_FILE_DIR.parent
paths = PathManager(ML_PIPELINE_ROOT)
