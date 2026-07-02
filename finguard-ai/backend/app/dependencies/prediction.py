"""
backend/app/dependencies/prediction.py
────────────────────────────────────────
FastAPI dependency providers for the prediction service.

Provides:
  - get_prediction_service()  →  PredictionService

Model loading is triggered once at first call (lazy singleton).
Subsequent requests reuse the already-loaded registry without I/O.
"""
from app.services.prediction import PredictionService, get_registry


def get_prediction_service() -> PredictionService:
    """
    FastAPI dependency that returns a PredictionService wired to the
    globally loaded model registry.

    Usage::

        @router.post("/predict")
        async def predict(
            payload: PredictionRequest,
            service: PredictionService = Depends(get_prediction_service),
        ) -> PredictionResponse:
            return await service.predict(payload)
    """
    registry = get_registry()
    return PredictionService(registry=registry)
