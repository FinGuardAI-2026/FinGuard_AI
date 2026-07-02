"""
backend/tests/conftest.py
──────────────────────────
pytest configuration for the backend test suite.

Ensures ml_pipeline is importable from backend/tests/ by adding the
monorepo root to sys.path at session start.
"""
import sys
from pathlib import Path

# Root of the monorepo: …/finguard-ai
_REPO_ROOT = Path(__file__).resolve().parents[2]  # backend/tests → backend → finguard-ai

# Make ml_pipeline importable
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
