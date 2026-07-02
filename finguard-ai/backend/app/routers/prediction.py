"""
backend/app/routers/prediction.py
───────────────────────────────────
Prediction router — exposes the fraud-detection inference API.

Endpoints
─────────
  POST /api/v1/predict           →  Run the full AI pipeline for a transaction
  GET  /api/v1/predict/health    →  Check model registry health
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user, RoleChecker
from app.dependencies.prediction import get_prediction_service
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction import PredictionService

router = APIRouter(prefix="/api/v1/predict", tags=["Prediction"])

# Fraud Analysts and Admins may submit transactions for scoring
_any_role = RoleChecker(["Admin", "Fraud Analyst"])


# ── GET /api/v1/predict/health ────────────────────────────────────────────────

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Model registry health check",
    description=(
        "Returns the load status of every ML artifact in the prediction pipeline. "
        "Use this endpoint to verify that the model, preprocessor, SHAP explainer, "
        "and risk engine were all loaded successfully at startup."
    ),
    responses={
        200: {"description": "All components status reported"},
        401: {"description": "Unauthenticated"},
    },
)
async def prediction_health(
    current_user: Dict[str, Any] = Depends(_any_role),
    service: PredictionService = Depends(get_prediction_service),
) -> Dict[str, Any]:
    """Returns a health snapshot of every AI component in the inference pipeline."""
    reg = service._reg
    return {
        "status": "operational" if reg.model is not None else "degraded",
        "components": {
            "preprocessor": "loaded" if reg.preprocessor is not None else "unavailable",
            "champion_model": "loaded" if reg.model is not None else "MISSING",
            "shap_explainer": "loaded" if reg.shap_explainer is not None else "unavailable",
            "risk_engine": "loaded" if reg.risk_engine is not None else "unavailable",
        },
        "model_version": reg.model_version,
    }


# ── POST /api/v1/predict ──────────────────────────────────────────────────────

@router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PredictionResponse,
    summary="Fraud detection — full AI pipeline",
    description=(
        "Submits a financial transaction for fraud detection. "
        "The request passes through the following stages:\n\n"
        "1. **Validation** — Pydantic schema enforcement\n"
        "2. **Preprocessing** — FraudPreprocessor (imputation + scaling)\n"
        "3. **ML Prediction** — Champion model `predict_proba()`\n"
        "4. **Confidence Score** — Probability of the winning class\n"
        "5. **SHAP Explanation** — Feature attribution (FinGuardSHAPExplainer)\n"
        "6. **Risk Assessment** — Risk Engine (ML + SHAP + Business Rules)\n"
        "7. **Gemini Reports** *(optional)* — AI-generated investigation, analyst, "
        "executive, and customer-notification reports\n\n"
        "Set `generate_reports: true` in the request body to include Gemini reports "
        "(adds ~2–10 s of latency depending on the Gemini API response time)."
    ),
    responses={
        200: {"description": "Prediction completed successfully"},
        400: {"description": "Invalid request payload"},
        401: {"description": "Unauthenticated"},
        422: {"description": "Validation error"},
        503: {"description": "Model registry unavailable"},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "legitimate_transaction": {
                            "summary": "Low-risk legitimate transaction",
                            "value": {
                                "amount": 42.50,
                                "time": 86400.0,
                                "V1": 1.191,
                                "V2": 0.266,
                                "V3": 0.166,
                                "V4": 0.448,
                                "V14": 0.207,
                                "merchant_name": "Starbucks",
                                "merchant_category": "FOOD_AND_BEVERAGE",
                                "payment_method": "CREDIT_CARD",
                                "country": "USA",
                                "city": "Seattle",
                                "ip_address": "192.168.1.1",
                                "device_id": "DEV-known-001",
                                "generate_reports": False,
                            },
                        },
                        "suspicious_transaction": {
                            "summary": "High-risk suspicious transaction",
                            "value": {
                                "amount": 9999.99,
                                "time": 3600.0,
                                "V1": -3.043,
                                "V2": -3.157,
                                "V3": 1.088,
                                "V4": 2.288,
                                "V10": -4.797,
                                "V11": 4.021,
                                "V12": -4.286,
                                "V14": -7.042,
                                "V16": -4.458,
                                "merchant_name": "Unknown Merchant",
                                "merchant_category": "CRYPTO",
                                "payment_method": "CRYPTO",
                                "country": "RU",
                                "city": "Moscow",
                                "ip_address": "185.220.101.1",
                                "device_id": "DEV-new-unknown-xyz",
                                "generate_reports": True,
                            },
                        },
                    }
                }
            }
        }
    },
)
async def predict(
    payload: PredictionRequest,
    current_user: Dict[str, Any] = Depends(_any_role),
    service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    """
    Runs the complete FinGuard AI fraud detection pipeline for a single transaction.

    Returns a structured response containing:
    - ML prediction label ('FRAUD' / 'GENUINE')
    - Fraud probability (0–100 %)
    - Confidence score (0–100 %)
    - SHAP feature attribution summary
    - Risk score (0–100) and risk level (Low / Medium / High / Critical)
    - Triggered business rules
    - Recommended investigation action
    - Optional Gemini AI-generated reports
    """
    try:
        return await service.predict(
        request=payload,
        user_id=current_user["_id"],
    )    
    except RuntimeError as exc:
        # Model not loaded or other infrastructure failure
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected prediction error: {exc}",
        )
