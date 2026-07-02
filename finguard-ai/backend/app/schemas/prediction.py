"""
backend/app/schemas/prediction.py
──────────────────────────────────
Pydantic v2 compatible schemas for the fraud-prediction endpoint.
All Field examples use the v2 `examples=[...]` parameter.
Class-based Config replaced with model_config = ConfigDict(...).

Request  → PredictionRequest   (transaction data to score)
Response → PredictionResponse  (full AI pipeline output)
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Request ───────────────────────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    """
    Payload submitted to POST /api/v1/predict.

    The payload mirrors the numeric feature columns expected by the trained
    FraudPreprocessor / ML model.  Optional metadata fields are forwarded to
    the Risk Engine and Gemini report generator but are NOT used as model
    input features.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 1250.75,
                "time": 86400.0,
                "V1": -1.359,
                "V2": -0.072,
                "V14": -0.311,
                "transaction_id": "TXN-20260628-001",
                "merchant_name": "Amazon Prime",
                "merchant_category": "E-COMMERCE",
                "payment_method": "CREDIT_CARD",
                "country": "USA",
                "city": "New York",
                "ip_address": "203.0.113.42",
                "device_id": "DEV-a1b2c3d4e5f6",
                "generate_reports": False,
            }
        }
    )

    # ── Numeric model features (required) ────────────────────────────────
    amount: float = Field(
        ...,
        gt=0,
        examples=[1250.75],
        description="Transaction amount in the requested currency.",
    )
    time: Optional[float] = Field(
        default=None,
        examples=[86400.0],
        description=(
            "Seconds elapsed since the start of the observation window "
            "(matches the 'Time' feature used during model training). "
            "Defaults to current epoch seconds when omitted."
        ),
    )

    # Anonymous PCA-derived features (V1-V28) — all optional with default 0.0
    V1: float  = Field(default=0.0, examples=[-1.359])
    V2: float  = Field(default=0.0, examples=[-0.072])
    V3: float  = Field(default=0.0, examples=[2.536])
    V4: float  = Field(default=0.0, examples=[1.378])
    V5: float  = Field(default=0.0, examples=[-0.338])
    V6: float  = Field(default=0.0, examples=[0.462])
    V7: float  = Field(default=0.0, examples=[0.239])
    V8: float  = Field(default=0.0, examples=[0.098])
    V9: float  = Field(default=0.0, examples=[0.363])
    V10: float = Field(default=0.0, examples=[0.090])
    V11: float = Field(default=0.0, examples=[-0.551])
    V12: float = Field(default=0.0, examples=[-0.617])
    V13: float = Field(default=0.0, examples=[-0.991])
    V14: float = Field(default=0.0, examples=[-0.311])
    V15: float = Field(default=0.0, examples=[1.468])
    V16: float = Field(default=0.0, examples=[-0.470])
    V17: float = Field(default=0.0, examples=[0.207])
    V18: float = Field(default=0.0, examples=[0.025])
    V19: float = Field(default=0.0, examples=[0.403])
    V20: float = Field(default=0.0, examples=[0.251])
    V21: float = Field(default=0.0, examples=[-0.018])
    V22: float = Field(default=0.0, examples=[0.277])
    V23: float = Field(default=0.0, examples=[-0.110])
    V24: float = Field(default=0.0, examples=[0.066])
    V25: float = Field(default=0.0, examples=[0.128])
    V26: float = Field(default=0.0, examples=[-0.189])
    V27: float = Field(default=0.0, examples=[0.133])
    V28: float = Field(default=0.0, examples=[-0.021])

    # ── Transaction metadata (forwarded to Risk Engine + Gemini) ──────────
    transaction_id: Optional[str] = Field(
        default=None,
        examples=["TXN-20260628-001"],
        description="Optional client-supplied transaction identifier.",
    )
    merchant_name: Optional[str]     = Field(default=None, examples=["Amazon Prime"])
    merchant_category: Optional[str] = Field(default=None, examples=["E-COMMERCE"])
    payment_method: Optional[str]    = Field(default=None, examples=["CREDIT_CARD"])
    transaction_type: Optional[str]  = Field(default=None, examples=["PURCHASE"])
    country: Optional[str]           = Field(default=None, examples=["USA"])
    city: Optional[str]              = Field(default=None, examples=["New York"])
    ip_address: Optional[str]        = Field(default=None, examples=["203.0.113.42"])
    device_id: Optional[str]         = Field(default=None, examples=["DEV-a1b2c3d4e5f6"])
    browser: Optional[str]           = Field(default=None, examples=["Chrome/124.0"])
    operating_system: Optional[str]  = Field(default=None, examples=["Windows 11"])
    transaction_time: Optional[datetime] = Field(
        default=None,
        examples=["2026-06-28T00:00:00Z"],
        description="UTC timestamp of the transaction.",
    )

    # ── Report generation flag ────────────────────────────────────────────
    generate_reports: bool = Field(
        default=False,
        description=(
            "When true, triggers Gemini AI report generation "
            "(investigation, analyst summary, executive, customer notification). "
            "Adds latency; use selectively."
        ),
    )


# ── SHAP nested model ─────────────────────────────────────────────────────────

class SHAPDriver(BaseModel):
    """A single SHAP attribution driver for a feature."""
    feature: str
    value: float
    impact: float


class SHAPExplanation(BaseModel):
    """Structured SHAP output included in each prediction response."""
    base_value: float
    positive_drivers: List[SHAPDriver] = Field(default_factory=list)
    negative_drivers: List[SHAPDriver] = Field(default_factory=list)
    narrative_risk_drivers: List[str] = Field(default_factory=list)
    narrative_mitigating_factors: List[str] = Field(default_factory=list)


# ── Risk Engine nested model ──────────────────────────────────────────────────

class RiskBreakdown(BaseModel):
    """Score component breakdown from the Risk Engine."""
    ml_contribution: float
    shap_contribution: float
    rule_contribution: float
    total: float


class RiskEngineOutput(BaseModel):
    """Structured risk assessment included in each prediction response."""
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: str           # Low | Medium | High | Critical
    triggered_rules: List[str] = Field(default_factory=list)
    score_breakdown: RiskBreakdown
    investigation_recommendation: str


# ── Response ──────────────────────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    """
    Full AI pipeline output returned from POST /api/v1/predict.

    Contains the ML prediction, fraud probability, confidence score,
    SHAP explanation, risk assessment, and optional Gemini reports.
    """

    model_config = ConfigDict(protected_namespaces=())

    # ── Core prediction ───────────────────────────────────────────────────
    transaction_id: str   = Field(..., description="Echo of the supplied or auto-generated transaction ID.")
    prediction: str       = Field(..., description="'FRAUD' or 'GENUINE'.")
    fraud_probability: float = Field(..., ge=0.0, le=100.0, description="Fraud probability as a percentage (0–100).")
    confidence_score: float  = Field(..., ge=0.0, le=100.0, description="Model confidence as a percentage (0–100).")

    # ── SHAP explanation ──────────────────────────────────────────────────
    shap_explanation: SHAPExplanation

    # ── Risk engine output ────────────────────────────────────────────────
    risk_assessment: RiskEngineOutput

    # ── Gemini reports (populated when generate_reports=True) ─────────────
    gemini_reports: Optional[Dict[str, str]] = Field(
        default=None,
        description=(
            "Gemini AI-generated reports keyed by type: "
            "'fraud_investigation', 'analyst_summary', 'executive_summary', 'customer_notification'."
        ),
    )

    # ── Meta ──────────────────────────────────────────────────────────────
    top_features: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top 5 most influential features by absolute SHAP magnitude.",
    )
    model_version: str  = Field(default="champion", description="Identifier of the model artifact used.")
    processing_time_ms: float = Field(..., description="Total pipeline latency in milliseconds.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC time of prediction.")
