"""
ml_pipeline/gemini/__init__.py
──────────────────────────────
Public API for the FinGuard AI Gemini integration module.
"""
from ml_pipeline.gemini.client import GeminiClient
from ml_pipeline.gemini.report_generator import FraudContext, FraudReportGenerator, ReportResult
from ml_pipeline.gemini.prompts import PROMPT_TEMPLATES

__all__ = [
    "GeminiClient",
    "FraudContext",
    "FraudReportGenerator",
    "ReportResult",
    "PROMPT_TEMPLATES",
]
