"""
backend/app/services/prediction.py
────────────────────────────────────
PredictionService — the core AI inference orchestrator.

Pipeline stages (in order):
  1. Validation & Normalisation    → enforce feature presence / defaults
  2. Preprocessing                 → FraudPreprocessor.transform()
  3. ML Prediction                 → champion_model.predict_proba()
  4. Confidence Score              → probability of the winning class
  5. SHAP Explanation              → FinGuardSHAPExplainer
  6. Risk Assessment               → RiskEngine.calculate()
  7. Gemini Reports (optional)     → FraudReportGenerator.generate_all()
  8. Response Assembly             → PredictionResponse

Design notes:
  - Model + preprocessor are loaded ONCE at application startup
    via a module-level singleton to avoid per-request cold-starts.
  - All heavy imports (joblib, shap, pandas) are deferred inside the
    module so that FastAPI workers that don't use prediction pay no cost.
  - SHAP background data is approximated from a zero-row placeholder
    when no training data is available at serve time; a real deployment
    should ship a small representative background dataset.
"""
import time
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    SHAPExplanation,
    SHAPDriver,
    RiskEngineOutput,
    RiskBreakdown,
)

from app.repositories.transaction import TransactionRepository
from app.db.connection import db_manager

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
# Resolve paths relative to this file so the service is location-agnostic.
_BACKEND_DIR = Path(__file__).resolve().parents[3]          # …/finguard-ai/backend
_ML_PIPELINE  = _BACKEND_DIR / "ml_pipeline"        # …/finguard-ai/ml_pipeline
_MODELS_DIR   = _ML_PIPELINE / "models"

# Canonical model artifact names (training saves both formats)
_PREPROCESSOR_PATHS = [
    _MODELS_DIR / "preprocessor.joblib",
    _MODELS_DIR / "preprocessor.pkl",
]
_MODEL_PATHS = [
    _MODELS_DIR / "champion_model.joblib",
    _MODELS_DIR / "best_model.pkl",
    _MODELS_DIR / "best_model.joblib",
]

# print("BACKEND_DIR :", _BACKEND_DIR)
# print("ML_PIPELINE :", _ML_PIPELINE)
# print("MODELS_DIR  :", _MODELS_DIR)

# for p in _MODEL_PATHS:
#     print(p, "=>", p.exists())

# PCA feature columns in dataset-training order
_FEATURE_COLUMNS = (
    ["Time"]
    + [f"V{i}" for i in range(1, 29)]
    + ["Amount"]
)


# ── Lazy Singleton State ───────────────────────────────────────────────────────

class _ModelRegistry:
    """Holds lazily-loaded ML artifacts shared across requests."""

    def __init__(self) -> None:
        self._preprocessor = None
        self._model = None
        self._shap_explainer = None
        self._risk_engine = None
        self._feature_names: List[str] = []
        self._model_version: str = "champion"
        self._loaded: bool = False

    # ── Loaders ───────────────────────────────────────────────────────────

    def _load_artifact(self, candidates: List[Path]) -> Any:
        """Tries each candidate path, returns the first successfully loaded object."""
        import joblib

        for path in candidates:
            if path.exists():
                logger.info(f"Loading artifact from '{path}'")
                return joblib.load(path)
        raise FileNotFoundError(
            f"No artifact found. Searched: {[str(p) for p in candidates]}"
        )

    def load(self) -> None:
        """Load all ML artifacts. Idempotent — safe to call multiple times."""
        if self._loaded:
            return

        logger.info("Initialising ML model registry...")

        # 1. Load preprocessor
        try:
            self._preprocessor = self._load_artifact(_PREPROCESSOR_PATHS)
            if hasattr(self._preprocessor, "feature_cols_"):
                self._feature_names = list(self._preprocessor.feature_cols_)
            logger.info("FraudPreprocessor loaded successfully.")
        except FileNotFoundError as e:
            logger.warning(f"Preprocessor not found — will use raw features: {e}")
            self._preprocessor = None
            self._feature_names = _FEATURE_COLUMNS[:]

        # 2. Load champion model
        try:
            self._model = self._load_artifact(_MODEL_PATHS)
            # Determine model version from filename
            for p in _MODEL_PATHS:
                if p.exists():
                    self._model_version = p.stem
                    break
            logger.info(f"Champion model '{self._model_version}' loaded.")
        except FileNotFoundError as e:
            logger.error(f"CRITICAL: Champion model not found: {e}")
            raise RuntimeError(
                "Prediction service unavailable — model artifact missing."
            ) from e

        # 3. Build SHAP explainer
        try:
            from ml_pipeline.explainability.shap_explainer import FinGuardSHAPExplainer
            import joblib

            bg_path = _MODELS_DIR / "background_data.joblib"
            if bg_path.exists():
                try:
                    bg_data = joblib.load(bg_path)
                    logger.info(f"Loaded SHAP background dataset from '{bg_path}'")
                except Exception as ex:
                    logger.warning(f"Failed to load background dataset: {ex}. Using zero-row fallback.")
                    bg_data = pd.DataFrame(
                        np.zeros((1, len(self._feature_names))),
                        columns=self._feature_names,
                    )
            else:
                logger.warning(f"SHAP background dataset '{bg_path}' not found. Using zero-row fallback.")
                bg_data = pd.DataFrame(
                    np.zeros((1, len(self._feature_names))),
                    columns=self._feature_names,
                )

            self._shap_explainer = FinGuardSHAPExplainer(
                model=self._model,
                background_data=bg_data,
            )
            logger.info("SHAP explainer initialised successfully.")
        except Exception as e:
            logger.warning(f"SHAP explainer unavailable: {e}")
            self._shap_explainer = None

        # 4. Instantiate Risk Engine (stateless, no artifacts required)
        try:
            from ml_pipeline.risk_engine.engine import RiskEngine

            self._risk_engine = RiskEngine()
            logger.info("Risk engine initialised.")
        except Exception as e:
            logger.warning(f"Risk engine unavailable: {e}")
            self._risk_engine = None

        self._loaded = True
        logger.info("ML model registry initialisation complete.")

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def preprocessor(self):
        return self._preprocessor

    @property
    def model(self):
        return self._model

    @property
    def shap_explainer(self):
        return self._shap_explainer

    @property
    def risk_engine(self):
        return self._risk_engine

    @property
    def feature_names(self) -> List[str]:
        return self._feature_names

    @property
    def model_version(self) -> str:
        return self._model_version


# Module-level singleton
_registry = _ModelRegistry()


def get_registry() -> _ModelRegistry:
    """Returns the loaded model registry (loads lazily on first call)."""
    _registry.load()
    return _registry


# ── Prediction Service ────────────────────────────────────────────────────────

class PredictionService:
    """
    Orchestrates the full fraud-detection inference pipeline.

    Injected via FastAPI's dependency system; receives a loaded
    _ModelRegistry so models are only instantiated once per process.
    """

    def __init__(self, registry: _ModelRegistry) -> None:
        self._reg = registry

    @property
    def transaction_repo(self) -> Optional[TransactionRepository]:
        try:
            db = db_manager.get_db()
            return TransactionRepository(db)
        except RuntimeError:
            return None

    # ── Public Entry Point ────────────────────────────────────────────────

    async def predict(
        self,
        request: PredictionRequest,
        user_id: str = "",
    ) -> PredictionResponse:        
        """
        Executes the end-to-end fraud detection pipeline.

        Args:
            request: Validated PredictionRequest from the HTTP layer.

        Returns:
            PredictionResponse with all AI components populated.
        """
        t_start = time.perf_counter()

        # 1. Build feature DataFrame
        feature_df = self._build_feature_df(request)

        # 2. Preprocess
        processed_df = self._preprocess(feature_df)

        # 3. ML Inference
        fraud_probability, confidence_score, prediction_label, xgb_latency = self._infer(processed_df)

        # 4. SHAP Explanation
        shap_output, shap_vector, shap_latency = self._explain(processed_df, feature_df)

        # 5. Risk Assessment
        transaction_meta = self._build_transaction_meta(request)
        risk_output = self._assess_risk(
            fraud_probability=fraud_probability,
            transaction=transaction_meta,
            shap_vector=shap_vector,
        )

        # 6. Top Features (from SHAP magnitude)
        top_features = self._extract_top_features(shap_vector, processed_df)

        # 7. Optional Gemini Reports
        gemini_reports: Optional[Dict[str, str]] = None
        gemini_latency=0
        if request.generate_reports:
            gemini_reports, gemini_latency = await self._generate_reports(
                request=request,
                prediction=prediction_label,
                fraud_probability=fraud_probability,
                confidence_score=confidence_score,
                risk_output=risk_output,
                shap_output=shap_output,
            )

        # 8. Assemble response
        t_end = time.perf_counter()
        processing_ms = round((t_end - t_start) * 1000, 2)

        transaction_id = (
            request.transaction_id or f"TXN-{uuid.uuid4().hex[:12].upper()}"
        )

        repo = self.transaction_repo
        if repo is not None:
            try:
                # print(">>> Saving prediction to MongoDB...")
                await repo.insert_one({
                    "transaction_id": transaction_id,

                    "user_id": user_id,

                    "amount": request.amount,
                    "currency": "USD",

                    "merchant_name": request.merchant_name,
                    "merchant_category": request.merchant_category,

                    "payment_method": request.payment_method,
                    "transaction_type": request.transaction_type or "PURCHASE",

                    "status": "COMPLETED",

                    "country": request.country,
                    "city": request.city,

                    "ip_address": request.ip_address,
                    "device_id": request.device_id,
                    "browser": request.browser,
                    "operating_system": request.operating_system,

                    "transaction_time": request.transaction_time or datetime.utcnow(),

                    "prediction": prediction_label,
                    "fraud_probability": fraud_probability,
                    "confidence_score": confidence_score,
                    "xgboost_latency_ms": xgb_latency,
                    "shap_latency_ms": shap_latency,
                    "gemini_latency_ms": gemini_latency,

                    "risk_score": risk_output.risk_score,
                    "risk_level": risk_output.risk_level,

                    "shap_summary": shap_output.model_dump(),

                    "llm_report": gemini_reports,

                    "investigation_status": "PENDING_REVIEW",

                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                })
                # print(">>> Prediction saved successfully.")
                if user_id:
                    try:
                        db = db_manager.get_db()
                        from app.repositories.notification import NotificationRepository, NotificationPreferencesRepository
                        from app.services.notification import NotificationService
                        import asyncio
                        
                        notif_repo = NotificationRepository(db)
                        prefs_repo = NotificationPreferencesRepository(db)
                        notif_svc = NotificationService(notif_repo, prefs_repo)
                        
                        # Trigger fraud alert
                        asyncio.create_task(
                            notif_svc.notify_fraud_prediction(
                                user_id=user_id,
                                transaction_id=transaction_id,
                                fraud_probability=fraud_probability,
                                risk_level=risk_output.risk_level,
                                amount=request.amount,
                            )
                        )
                        
                        # Trigger report generated alert if requested
                        if request.generate_reports and gemini_reports:
                            asyncio.create_task(
                                notif_svc.notify_report_generated(
                                    user_id=user_id,
                                    transaction_id=transaction_id,
                                    report_type="fraud_investigation",
                                )
                            )
                    except Exception as ne:
                        logger.error(f"Failed to trigger notifications: {ne}")
            except Exception as e:
                logger.error(f"Failed to save prediction: {e}")

        return PredictionResponse(
            transaction_id=transaction_id,
            prediction=prediction_label,
            fraud_probability=round(fraud_probability * 100, 4),
            confidence_score=round(confidence_score * 100, 4),
            shap_explanation=shap_output,
            risk_assessment=risk_output,
            gemini_reports=gemini_reports,
            top_features=top_features,
            model_version=self._reg.model_version,
            processing_time_ms=processing_ms,
            xgboost_latency_ms=xgb_latency,
            shap_latency_ms=shap_latency,
            timestamp=datetime.utcnow(),
        )

    # ── Stage 1: Feature Frame Construction ───────────────────────────────

    # TODO: Legacy Kaggle Credit Card compatibility.
    # Remove after legacy Time/V1-V28 schema support is retired.
    def _build_feature_df(self, request: PredictionRequest) -> pd.DataFrame:
        """
        Builds the raw feature DataFrame from the request.
        Maps PredictionRequest fields to the exact column order expected
        by the trained preprocessor / model.
        """
        import time as _time

        row = {
            "Time": request.time if request.time is not None else _time.time(),
            "Amount": request.amount,
            "amount": request.amount,
            "merchant_category": request.merchant_category or "UNKNOWN",
            "payment_method": request.payment_method or "UNKNOWN",
            "transaction_type": request.transaction_type or "UNKNOWN",
            "country": request.country or "UNKNOWN",
        }
        for i in range(1, 29):
            row[f"V{i}"] = getattr(request, f"V{i}", 0.0)

        cols = self._reg.feature_names
        filtered_row = {}
        for col in cols:
            if col == "Amount" or col == "amount":
                filtered_row[col] = request.amount
            elif col == "Time" or col == "time":
                filtered_row[col] = request.time if request.time is not None else _time.time()
            elif col.startswith("V") and len(col) > 1 and col[1:].isdigit():
                filtered_row[col] = getattr(request, col, 0.0)
            else:
                filtered_row[col] = row.get(col, 0.0)

        return pd.DataFrame([filtered_row])

    # ── Stage 2: Preprocessing ────────────────────────────────────────────

    def _preprocess(self, feature_df: pd.DataFrame) -> pd.DataFrame:
        """Applies the FraudPreprocessor to a single-row feature DataFrame."""
        preprocessor = self._reg.preprocessor
        if preprocessor is not None:
            try:
                return preprocessor.transform(feature_df)
            except Exception as e:
                logger.warning(f"Preprocessor transform failed, using raw features: {e}")
        return feature_df

    # ── Stage 3: ML Inference ─────────────────────────────────────────────

    def _infer(self, processed_df: pd.DataFrame) -> Tuple[float, float, str, float]:
        """
        Runs the model and returns (fraud_prob, confidence, label).

        fraud_prob  – probability of class 1 (fraud) in [0, 1]
        confidence  – probability of the predicted class in [0, 1]
        label       – 'FRAUD' or 'GENUINE'
        """
        model = self._reg.model
        X = processed_df.values
        start=time.perf_counter()

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]          # [prob_legit, prob_fraud]
            fraud_prob = float(proba[1])
            predicted_class = int(np.argmax(proba))
            confidence = float(proba[predicted_class])
        else:
            # Fallback for models that only have predict()
            raw = model.predict(X)[0]
            fraud_prob = float(raw)
            predicted_class = 1 if fraud_prob >= 0.5 else 0
            confidence = fraud_prob if predicted_class == 1 else 1.0 - fraud_prob

        label = "FRAUD" if predicted_class == 1 else "GENUINE"
        latency_ms=round((time.perf_counter()-start)*1000,2)
        return fraud_prob, confidence, label, latency_ms

    # ── Stage 4: SHAP Explanation ─────────────────────────────────────────

    def _explain(
        self,
        processed_df: pd.DataFrame,
        raw_df: pd.DataFrame,
    ) -> Tuple[SHAPExplanation, Optional[np.ndarray], float]:
        """
        Computes SHAP values and returns a structured SHAPExplanation.

        Returns both the Pydantic model and the raw 1-D SHAP vector
        (the vector is forwarded to the Risk Engine).
        """
        explainer = self._reg.shap_explainer
        if explainer is None:
            return self._empty_shap_explanation(), None,0

        try:
            start = time.perf_counter()
            shap_matrix = explainer.calculate_shap_values(processed_df)
            shap_vector = shap_matrix[0]                # single sample

            sample_row = processed_df.iloc[0]
            narrative = explainer.generate_analyst_narrative(shap_vector, sample_row)

            pos_drivers = [
                SHAPDriver(**d) for d in narrative.get("positive_drivers", [])
            ]
            neg_drivers = [
                SHAPDriver(**d) for d in narrative.get("negative_drivers", [])
            ]
            analyst = narrative.get("analyst_narrative", {})

            explanation = SHAPExplanation(
                base_value=narrative.get("base_value", explainer.expected_value),
                positive_drivers=pos_drivers,
                negative_drivers=neg_drivers,
                narrative_risk_drivers=analyst.get("risk_drivers", []),
                narrative_mitigating_factors=analyst.get("mitigating_factors", []),
            )
            shap_latency = round(
                (time.perf_counter() - start) * 1000,
                2
            )
            return explanation, shap_vector, shap_latency

        except Exception as e:
            logger.warning(f"SHAP explanation failed: {e}")
            return self._empty_shap_explanation(), None, 0

    def _empty_shap_explanation(self) -> SHAPExplanation:
        return SHAPExplanation(
            base_value=0.0,
            positive_drivers=[],
            negative_drivers=[],
            narrative_risk_drivers=[],
            narrative_mitigating_factors=[],
        )

    # ── Stage 5: Risk Assessment ──────────────────────────────────────────

    def _assess_risk(
        self,
        fraud_probability: float,
        transaction: Dict[str, Any],
        shap_vector: Optional[np.ndarray],
    ) -> RiskEngineOutput:
        """Invokes the RiskEngine and wraps the result in a Pydantic model."""
        risk_engine = self._reg.risk_engine
        if risk_engine is None:
            return self._fallback_risk(fraud_probability)

        try:
            assessment = risk_engine.calculate(
                fraud_probability=fraud_probability,
                transaction=transaction,
                shap_values=shap_vector,
            )
            return RiskEngineOutput(
                risk_score=round(assessment.risk_score, 2),
                risk_level=assessment.risk_level,
                triggered_rules=assessment.triggered_rules,
                score_breakdown=RiskBreakdown(**assessment.score_breakdown),
                investigation_recommendation=assessment.investigation_recommendation,
            )
        except Exception as e:
            logger.warning(f"Risk engine calculation failed: {e}")
            return self._fallback_risk(fraud_probability)

    def _fallback_risk(self, fraud_probability: float) -> RiskEngineOutput:
        """Returns a minimal risk output when the engine is unavailable."""
        score = round(fraud_probability * 100, 2)
        if score <= 30:
            level = "Low"
        elif score <= 60:
            level = "Medium"
        elif score <= 85:
            level = "High"
        else:
            level = "Critical"

        return RiskEngineOutput(
            risk_score=score,
            risk_level=level,
            triggered_rules=[],
            score_breakdown=RiskBreakdown(
                ml_contribution=score,
                shap_contribution=0.0,
                rule_contribution=0.0,
                total=score,
            ),
            investigation_recommendation="Risk engine unavailable — score derived from ML probability only.",
        )

    # ── Stage 6: Top Features ─────────────────────────────────────────────

    def _extract_top_features(
        self,
        shap_vector: Optional[np.ndarray],
        processed_df: pd.DataFrame,
        n: int = 5,
    ) -> List[Dict[str, Any]]:
        """Returns the top-N features sorted by absolute SHAP impact."""
        if shap_vector is None:
            return []

        feature_names = (
            self._reg.feature_names
            if self._reg.feature_names
            else list(processed_df.columns)
        )
        if len(feature_names) != len(shap_vector):
            feature_names = list(processed_df.columns)

        indexed = sorted(
            enumerate(shap_vector),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:n]

        name_map = {
            "amount": "Transaction Amount",
            "merchant_category": "Merchant Category",
            "payment_method": "Payment Method",
            "transaction_type": "Transaction Type",
            "country": "Country",
        }

        def map_feature(feature_name: str, processed_val: float) -> Tuple[str, Union[float, str]]:
            for prefix in ["merchant_category_", "payment_method_", "transaction_type_", "country_"]:
                if feature_name.startswith(prefix):
                    raw_feat = prefix[:-1]
                    category = feature_name[len(prefix):]
                    readable_name = name_map.get(raw_feat, raw_feat.replace("_", " ").title())
                    if processed_val == 1.0:
                        return readable_name, category
                    return readable_name, None
            readable_name = name_map.get(feature_name, feature_name.replace("_", " ").title())
            return readable_name, processed_val

        results = []
        for rank, (idx, _) in enumerate(indexed):
            f_name = feature_names[idx]
            f_val_raw = processed_df.iloc[0, idx]
            
            if isinstance(f_val_raw, (int, float)):
                f_val = float(f_val_raw)
            elif f_val_raw is None:
                f_val = 0.0
            else:
                f_val = f_val_raw

                # Skip inactive one-hot encoded features
            if (
                f_name.startswith(("merchant_category_", "payment_method_", "transaction_type_", "country_"))
                and f_val != 1.0
            ):
                continue


            readable_name, readable_val = map_feature(f_name, f_val)
            
            results.append({
                "rank": rank + 1,
                "feature": readable_name,
                "shap_value": round(float(shap_vector[idx]), 6),
                "feature_value": round(readable_val, 6) if isinstance(readable_val, (int, float)) else readable_val,
            })

        return results

    # ── Stage 7: Gemini Reports ───────────────────────────────────────────

    async def _generate_reports(
        self,
        request: PredictionRequest,
        prediction: str,
        fraud_probability: float,
        confidence_score: float,
        risk_output: RiskEngineOutput,
        shap_output: SHAPExplanation,
    ) -> Optional[Dict[str, str]]:
        """
        Invokes FraudReportGenerator to produce all four Gemini AI reports.
        Returns a dict keyed by report type with the generated Markdown text.
        """
        try:
            from ml_pipeline.gemini.report_generator import FraudReportGenerator, FraudContext

            transaction_id = (
                request.transaction_id or f"TXN-{uuid.uuid4().hex[:12].upper()}"
            )
            reports_output_dir = _ML_PIPELINE / "reports" / transaction_id

            context = FraudContext(
                transaction_id=transaction_id,
                amount=request.amount,
                currency="USD",
                merchant_name=request.merchant_name or "Unknown",
                merchant_category=request.merchant_category or "UNKNOWN",
                payment_method=request.payment_method or "Unknown",
                transaction_type=request.transaction_type or "Unknown",
                country=request.country or "USA",
                city=request.city or "Unknown",
                ip_address=request.ip_address or "0.0.0.0",
                device_id=request.device_id or "Unknown",
                browser=request.browser or "Unknown",
                operating_system=request.operating_system or "Unknown",
                transaction_time=(
                    request.transaction_time.strftime("%Y-%m-%d %H:%M:%S UTC")
                    if request.transaction_time
                    else ""
                ),
                prediction=prediction,
                fraud_probability=round(fraud_probability * 100, 2),
                confidence_score=round(confidence_score * 100, 2),
                risk_score=risk_output.risk_score,
                risk_level=risk_output.risk_level,
                triggered_rules=risk_output.triggered_rules,
                investigation_recommendation=risk_output.investigation_recommendation,
                shap_risk_drivers=shap_output.narrative_risk_drivers,
                shap_mitigating_factors=shap_output.narrative_mitigating_factors,
            )

            generator = FraudReportGenerator(output_dir=reports_output_dir)
            start = time.perf_counter()
            results = generator.generate_all(context)
            gemini_latency = round(
                (time.perf_counter() - start) * 1000,
                2
            )

            return (
                {r.report_type: r.report_text for r in results},
                gemini_latency
            )
        
        except Exception as e:
            logger.error(f"Gemini report generation failed: {e}", exc_info=True)
            return None,0

    # ── Helpers ───────────────────────────────────────────────────────────

    def _build_transaction_meta(self, request: PredictionRequest) -> Dict[str, Any]:
        """
        Builds the transaction metadata dictionary forwarded to the Risk Engine.
        Mirrors the fields the BusinessRuleEvaluator inspects.
        """
        return {
            "amount": request.amount,
            "country": request.country or "USA",
            "merchant_category": request.merchant_category or "",
            "payment_method": request.payment_method or "",
            "transaction_type": request.transaction_type or "",
            "device_id": request.device_id or "",
            "ip_address": request.ip_address or "",
            "merchant_name": request.merchant_name or "",
        }
