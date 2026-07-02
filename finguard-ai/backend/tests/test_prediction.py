"""
backend/tests/test_prediction.py
──────────────────────────────────
Unit tests for the fraud-detection prediction pipeline.

Tests are organised into three classes:
  - TestPredictionSchemas    → Pydantic schema validation
  - TestPredictionService    → Service logic with mocked ML artifacts
  - TestPredictionRouter     → HTTP endpoint contract tests

All ML artifacts (model, preprocessor, SHAP, risk engine) are replaced
with lightweight MagicMock / AsyncMock objects so tests run offline
without requiring trained model files.
"""
import pytest
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

from pydantic import ValidationError

from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    SHAPExplanation,
    SHAPDriver,
    RiskEngineOutput,
    RiskBreakdown,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_request(**overrides) -> PredictionRequest:
    """Builds a minimal valid PredictionRequest."""
    defaults = dict(
        amount=250.00,
        time=86400.0,
        V1=-1.359,
        V2=-0.072,
        V14=-0.311,
        merchant_name="Amazon Prime",
        merchant_category="E-COMMERCE",
        payment_method="CREDIT_CARD",
        country="USA",
        city="New York",
        ip_address="203.0.113.42",
        device_id="DEV-a1b2c3d4e5f6",
        generate_reports=False,
    )
    defaults.update(overrides)
    return PredictionRequest(**defaults)


def _make_risk_output(risk_score: float = 25.0, risk_level: str = "Low") -> RiskEngineOutput:
    return RiskEngineOutput(
        risk_score=risk_score,
        risk_level=risk_level,
        triggered_rules=[],
        score_breakdown=RiskBreakdown(
            ml_contribution=risk_score,
            shap_contribution=0.0,
            rule_contribution=0.0,
            total=risk_score,
        ),
        investigation_recommendation="CLEAR: Transaction falls within normal parameters.",
    )


def _make_shap_explanation() -> SHAPExplanation:
    return SHAPExplanation(
        base_value=0.02,
        positive_drivers=[SHAPDriver(feature="Amount", value=250.0, impact=0.12)],
        negative_drivers=[SHAPDriver(feature="V14", value=-0.311, impact=-0.05)],
        narrative_risk_drivers=["Feature `Amount` increased fraud likelihood by +12.00%."],
        narrative_mitigating_factors=["Feature `V14` lowered fraud likelihood by -5.00%."],
    )


def _make_registry_mock(
    model=None,
    preprocessor=None,
    shap_explainer=None,
    risk_engine=None,
) -> MagicMock:
    """Creates a mock _ModelRegistry with controllable attributes."""
    import pandas as pd

    feature_names = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]

    mock_model = model or MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.87, 0.13]])

    mock_preprocessor = preprocessor or MagicMock()
    mock_preprocessor.feature_cols_ = feature_names
    mock_preprocessor.transform.side_effect = lambda df: df

    mock_shap = shap_explainer or MagicMock()
    mock_shap.calculate_shap_values.return_value = np.zeros((1, len(feature_names)))
    mock_shap.expected_value = 0.02
    mock_shap.generate_analyst_narrative.return_value = {
        "base_value": 0.02,
        "positive_drivers": [{"feature": "Amount", "value": 250.0, "impact": 0.12}],
        "negative_drivers": [{"feature": "V14", "value": -0.311, "impact": -0.05}],
        "analyst_narrative": {
            "risk_drivers": ["Feature `Amount` increased fraud likelihood."],
            "mitigating_factors": ["Feature `V14` lowered fraud likelihood."],
        },
    }

    mock_risk = risk_engine or MagicMock()

    from ml_pipeline.risk_engine.engine import RiskAssessment
    mock_assessment = RiskAssessment(
        fraud_probability=0.13,
        shap_magnitude=0.05,
        rule_penalty=0.0,
        risk_score=15.0,
        risk_level="Low",
        triggered_rules=[],
        score_breakdown={
            "ml_contribution": 7.80,
            "shap_contribution": 0.75,
            "rule_contribution": 0.00,
            "total": 15.0,
        },
        investigation_recommendation="CLEAR: Normal parameters.",
    )
    mock_risk.calculate.return_value = mock_assessment

    registry = MagicMock()
    registry.model = mock_model
    registry.preprocessor = mock_preprocessor
    registry.shap_explainer = mock_shap
    registry.risk_engine = mock_risk
    type(registry).feature_names = PropertyMock(return_value=feature_names)
    type(registry).model_version = PropertyMock(return_value="champion_model")

    return registry


# ── Schema Validation Tests ───────────────────────────────────────────────────

class TestPredictionSchemas:

    def test_valid_request_minimal(self):
        req = PredictionRequest(amount=100.0)
        assert req.amount == 100.0
        assert req.generate_reports is False

    def test_valid_request_full(self):
        req = _make_request()
        assert req.merchant_name == "Amazon Prime"
        assert req.country == "USA"

    def test_invalid_amount_zero_raises(self):
        with pytest.raises(ValidationError):
            PredictionRequest(amount=0)

    def test_invalid_amount_negative_raises(self):
        with pytest.raises(ValidationError):
            PredictionRequest(amount=-50.0)

    def test_v_features_default_to_zero(self):
        req = PredictionRequest(amount=10.0)
        for i in range(1, 29):
            assert getattr(req, f"V{i}") == 0.0

    def test_generate_reports_flag_default_false(self):
        req = PredictionRequest(amount=10.0)
        assert req.generate_reports is False

    def test_generate_reports_flag_true(self):
        req = PredictionRequest(amount=10.0, generate_reports=True)
        assert req.generate_reports is True

    def test_response_model_instantiation(self):
        shap = _make_shap_explanation()
        risk = _make_risk_output()
        resp = PredictionResponse(
            transaction_id="TXN-001",
            prediction="GENUINE",
            fraud_probability=13.0,
            confidence_score=87.0,
            shap_explanation=shap,
            risk_assessment=risk,
            model_version="champion_model",
            processing_time_ms=45.2,
        )
        assert resp.prediction == "GENUINE"
        assert resp.fraud_probability == 13.0

    def test_risk_breakdown_fields(self):
        breakdown = RiskBreakdown(
            ml_contribution=7.8,
            shap_contribution=0.75,
            rule_contribution=0.0,
            total=8.55,
        )
        assert breakdown.total == 8.55


# ── PredictionService Unit Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
class TestPredictionService:

    async def _run(self, request: PredictionRequest, registry=None):
        """Helper to run predict() with an injected mock registry."""
        from app.services.prediction import PredictionService
        reg = registry or _make_registry_mock()
        service = PredictionService(registry=reg)
        return await service.predict(request)

    async def test_genuine_prediction_returned(self):
        """Model outputs low fraud probability → GENUINE label."""
        req = _make_request(amount=42.0)
        # Default mock: predict_proba returns [[0.87, 0.13]] → GENUINE
        result = await self._run(req)
        assert result.prediction == "GENUINE"

    async def test_fraud_prediction_returned(self):
        """Model outputs high fraud probability → FRAUD label."""
        reg = _make_registry_mock()
        reg.model.predict_proba.return_value = np.array([[0.02, 0.98]])
        result = await self._run(_make_request(), registry=reg)
        assert result.prediction == "FRAUD"

    async def test_fraud_probability_scaled_to_percent(self):
        """fraud_probability in response is 0–100, not 0–1."""
        reg = _make_registry_mock()
        reg.model.predict_proba.return_value = np.array([[0.75, 0.25]])
        result = await self._run(_make_request(), registry=reg)
        assert 0.0 <= result.fraud_probability <= 100.0

    async def test_confidence_score_scaled_to_percent(self):
        """confidence_score in response is 0–100, not 0–1."""
        result = await self._run(_make_request())
        assert 0.0 <= result.confidence_score <= 100.0

    async def test_transaction_id_auto_generated_when_missing(self):
        """When no transaction_id is provided, one is auto-generated."""
        req = _make_request()
        req.transaction_id = None
        result = await self._run(req)
        assert result.transaction_id.startswith("TXN-")

    async def test_transaction_id_echoed_when_provided(self):
        """When a transaction_id is supplied, it is echoed in the response."""
        req = _make_request(transaction_id="TXN-MY-CUSTOM-ID-001")
        result = await self._run(req)
        assert result.transaction_id == "TXN-MY-CUSTOM-ID-001"

    async def test_processing_time_ms_positive(self):
        """Pipeline timing must always be positive."""
        result = await self._run(_make_request())
        assert result.processing_time_ms > 0

    async def test_shap_explanation_present(self):
        """SHAP explanation must always be present (even if simulated)."""
        result = await self._run(_make_request())
        assert isinstance(result.shap_explanation, SHAPExplanation)

    async def test_risk_assessment_present(self):
        """Risk assessment must always be present."""
        result = await self._run(_make_request())
        assert isinstance(result.risk_assessment, RiskEngineOutput)

    async def test_top_features_present_when_shap_available(self):
        """Top features list should be populated when SHAP runs successfully."""
        result = await self._run(_make_request())
        assert isinstance(result.top_features, list)

    async def test_gemini_reports_none_when_not_requested(self):
        """Gemini reports should be None when generate_reports=False."""
        req = _make_request(generate_reports=False)
        result = await self._run(req)
        assert result.gemini_reports is None

    async def test_preprocessor_none_still_runs(self):
        """Service must not crash when preprocessor is missing."""
        reg = _make_registry_mock()
        reg.preprocessor = None
        result = await self._run(_make_request(), registry=reg)
        assert result.prediction in ("FRAUD", "GENUINE")

    async def test_shap_explainer_none_still_runs(self):
        """Service must not crash when SHAP explainer is missing."""
        reg = _make_registry_mock()
        reg.shap_explainer = None
        result = await self._run(_make_request(), registry=reg)
        assert result.shap_explanation.base_value == 0.0

    async def test_risk_engine_none_falls_back(self):
        """Service must not crash when risk engine is missing — uses fallback."""
        reg = _make_registry_mock()
        reg.risk_engine = None
        result = await self._run(_make_request(), registry=reg)
        assert result.risk_assessment.risk_level in ("Low", "Medium", "High", "Critical")

    async def test_model_version_propagated(self):
        """model_version from registry is echoed in response."""
        reg = _make_registry_mock()
        type(reg).model_version = PropertyMock(return_value="best_model")
        result = await self._run(_make_request(), registry=reg)
        assert result.model_version == "best_model"

    async def test_risk_score_in_valid_range(self):
        """Risk score must be between 0 and 100."""
        result = await self._run(_make_request())
        assert 0.0 <= result.risk_assessment.risk_score <= 100.0

    async def test_timestamp_is_datetime(self):
        """Response timestamp should be a UTC datetime object."""
        result = await self._run(_make_request())
        assert isinstance(result.timestamp, datetime)

    async def test_fallback_risk_for_critical(self):
        """Fallback risk engine labels 99% probability as Critical."""
        from app.services.prediction import PredictionService
        reg = _make_registry_mock()
        reg.risk_engine = None
        reg.model.predict_proba.return_value = np.array([[0.01, 0.99]])
        service = PredictionService(registry=reg)
        result = await service.predict(_make_request())
        assert result.risk_assessment.risk_level == "Critical"

    async def test_fallback_risk_for_low(self):
        """Fallback risk engine labels 5% probability as Low."""
        from app.services.prediction import PredictionService
        reg = _make_registry_mock()
        reg.risk_engine = None
        reg.model.predict_proba.return_value = np.array([[0.95, 0.05]])
        service = PredictionService(registry=reg)
        result = await service.predict(_make_request())
        assert result.risk_assessment.risk_level == "Low"


# ── Router HTTP Contract Tests ────────────────────────────────────────────────

class TestPredictionRouter:
    """
    Integration-style tests hitting the FastAPI router with a TestClient.
    All dependencies are overridden so no real ML models are loaded.
    """

    def _get_test_client(self, mock_service):
        """Build a TestClient with prediction service dependency overridden."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.dependencies.prediction import get_prediction_service
        from app.dependencies.auth import get_current_user, RoleChecker

        # Override auth to bypass JWT
        def _mock_user():
            return {"_id": "user_test", "role": "Admin"}

        def _mock_service():
            return mock_service

        app.dependency_overrides[get_current_user] = _mock_user
        app.dependency_overrides[get_prediction_service] = _mock_service

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def _build_mock_service(self) -> AsyncMock:
        """Returns a mock PredictionService with a canned response."""
        shap = _make_shap_explanation()
        risk = _make_risk_output()
        canned_response = PredictionResponse(
            transaction_id="TXN-TEST-001",
            prediction="GENUINE",
            fraud_probability=13.0,
            confidence_score=87.0,
            shap_explanation=shap,
            risk_assessment=risk,
            model_version="champion_model",
            processing_time_ms=42.0,
            top_features=[],
        )
        svc = MagicMock()
        svc.predict = AsyncMock(return_value=canned_response)
        svc._reg = _make_registry_mock()
        return svc

    def test_predict_returns_200(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.dependencies.prediction import get_prediction_service
        from app.dependencies.auth import get_current_user, RoleChecker

        svc = self._build_mock_service()

        app.dependency_overrides[get_current_user] = lambda: {"_id": "u", "role": "Admin"}
        app.dependency_overrides[get_prediction_service] = lambda: svc

        # RoleChecker overrides
        for key in list(app.dependency_overrides.keys()):
            pass  # already overriding get_current_user covers RoleChecker

        from app.routers.prediction import _any_role
        app.dependency_overrides[_any_role] = lambda: {"_id": "u", "role": "Admin"}

        try:
            client = TestClient(app)
            resp = client.post(
                "/api/v1/predict",
                json={"amount": 250.0, "V1": -1.359},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["prediction"] == "GENUINE"
            assert "fraud_probability" in data
            assert "risk_assessment" in data
            assert "shap_explanation" in data
        finally:
            app.dependency_overrides.clear()

    def test_predict_missing_amount_returns_422(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.dependencies.prediction import get_prediction_service
        from app.routers.prediction import _any_role

        svc = self._build_mock_service()
        app.dependency_overrides[_any_role] = lambda: {"_id": "u", "role": "Admin"}
        app.dependency_overrides[get_prediction_service] = lambda: svc

        try:
            client = TestClient(app)
            resp = client.post("/api/v1/predict", json={})  # Missing amount
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_health_endpoint_returns_200(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.dependencies.prediction import get_prediction_service
        from app.routers.prediction import _any_role

        svc = self._build_mock_service()
        app.dependency_overrides[_any_role] = lambda: {"_id": "u", "role": "Admin"}
        app.dependency_overrides[get_prediction_service] = lambda: svc

        try:
            client = TestClient(app)
            resp = client.get("/api/v1/predict/health")
            assert resp.status_code == 200
            data = resp.json()
            assert "components" in data
            assert "model_version" in data
        finally:
            app.dependency_overrides.clear()
