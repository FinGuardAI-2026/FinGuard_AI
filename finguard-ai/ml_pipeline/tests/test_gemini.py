"""
ml_pipeline/tests/test_gemini.py
─────────────────────────────────
Unit tests validating the Gemini API Client, Prompt Templates, and Report Generator.
"""
import pytest
from pathlib import Path
import json

from ml_pipeline.gemini.prompts import PROMPT_TEMPLATES
from ml_pipeline.gemini.client import GeminiClient
from ml_pipeline.gemini.report_generator import FraudContext, FraudReportGenerator, _render_prompt


def test_prompt_rendering():
    """Verify that the prompts render placeholder values correctly."""
    context = FraudContext(
        transaction_id="TX-123",
        amount=100.50,
        currency="USD",
        merchant_name="Test Merchant",
        merchant_category="RETAIL",
        prediction="FRAUD",
        fraud_probability=95.5,
        risk_score=90.0,
        risk_level="Critical",
        triggered_rules=["Rule A", "Rule B"],
        shap_risk_drivers=["Driver A", "Driver B"],
        shap_mitigating_factors=["Mitigator A"],
    )

    for report_type in PROMPT_TEMPLATES:
        rendered = _render_prompt(report_type, context)
        # Check that placeholders are resolved and not present in raw format
        assert "$transaction_id" not in rendered
        assert "$amount" not in rendered
        # Check that values actually exist in rendered text if they are in the template
        if report_type != "customer_notification":
            assert "TX-123" in rendered
        assert "100.50" in rendered
        assert "Test Merchant" in rendered


def test_gemini_client_fallback():
    """Verify that GeminiClient falls back to deterministic simulated reports when offline."""
    client = GeminiClient(api_key=None)  # Forces offline/simulation mode
    assert not client.active

    for report_type in ["fraud_investigation", "analyst_summary", "executive_summary", "customer_notification"]:
        response = client.generate("Some prompt", report_type=report_type)
        assert response is not None
        assert len(response) > 0
        assert "Offline Mode" not in response  # Should return structured fallback, not error string


def test_report_generator(tmp_path):
    """Verify that FraudReportGenerator generates all 4 files and updates the index correctly."""
    context = FraudContext(
        transaction_id="TX-TEST-GEN",
        amount=500.00,
        merchant_name="Electronics Shop",
        prediction="FRAUD",
        fraud_probability=80.0,
        risk_score=75.0,
        risk_level="High",
        triggered_rules=["High Amount", "New Device"],
    )

    # Use tmp_path fixture to avoid polluting the workspace
    generator = FraudReportGenerator(output_dir=tmp_path)
    results = generator.generate_all(context)

    assert len(results) == 4

    # Verify files exist and contain content
    expected_filenames = [
        "fraud_investigation_report.md",
        "analyst_summary.md",
        "executive_summary.md",
        "customer_notification.md",
    ]

    for filename in expected_filenames:
        file_path = tmp_path / filename
        assert file_path.exists()
        content = file_path.read_text(encoding="utf-8")
        assert "TX-TEST-GEN" in content
        assert "High" in content

    # Verify report index JSON
    index_path = tmp_path / "report_index.json"
    assert index_path.exists()
    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(index_data) == 1
    assert index_data[0]["transaction_id"] == "TX-TEST-GEN"
    assert len(index_data[0]["reports"]) == 4
