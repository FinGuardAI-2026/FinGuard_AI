from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
import uuid


class TransactionDB(BaseModel):
    """
    Internal model representing a transaction document stored in MongoDB.

    Current fields hold ingested transaction telemetry.
    Future fields (prediction, risk_score, shap_summary, llm_report,
    investigation_status) are pre-declared as Optional so the ML, SHAP,
    Risk Engine, and Gemini modules can populate them without altering
    this schema.
    """

    id: Optional[str] = Field(default=None, alias="_id")

    # ── Core Identity ──────────────────────────────────────────────────────
    transaction_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Globally unique transaction identifier (UUID4)."
    )
    user_id: str = Field(..., description="Owning user ObjectId reference.")

    # ── Financial ──────────────────────────────────────────────────────────
    amount: float = Field(..., gt=0, description="Transaction amount in declared currency.")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code, e.g. 'USD'.")

    # ── Merchant ───────────────────────────────────────────────────────────
    merchant_name: str = Field(..., min_length=1, max_length=200)
    merchant_category: str = Field(..., description="Merchant Category Code (MCC) label.")

    # ── Transaction Meta ───────────────────────────────────────────────────
    payment_method: str = Field(..., description="e.g. 'CREDIT_CARD', 'ACH', 'WIRE', 'APPLE_PAY'.")
    transaction_type: str = Field(..., description="e.g. 'PURCHASE', 'TRANSFER', 'WITHDRAWAL'.")
    status: str = Field(default="PENDING", description="Processing status: PENDING, COMPLETED, FAILED, FLAGGED.")

    # ── Geographic ────────────────────────────────────────────────────────
    country: str = Field(..., min_length=2, max_length=3, description="ISO 3166-1 alpha-2/3 country code.")
    city: Optional[str] = Field(default=None)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)

    # ── Device & Network ──────────────────────────────────────────────────
    ip_address: str = Field(..., description="IPv4 or IPv6 originating address.")
    device_id: str = Field(..., description="Unique hashed device fingerprint.")
    browser: Optional[str] = Field(default=None)
    operating_system: Optional[str] = Field(default=None)

    # ── Timing ────────────────────────────────────────────────────────────
    transaction_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the transaction occurred."
    )

    # ── Future ML / AI Fields (nullable placeholders) ─────────────────────
    prediction: Optional[str] = Field(default=None, description="'Fraud' or 'Genuine'. Set by ML engine.")
    fraud_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Raw model sigmoid output.")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Model certainty score 0–100.")
    risk_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Hybrid risk engine score 0–100.")
    shap_summary: Optional[Dict[str, Any]] = Field(default=None, description="SHAP feature attribution vectors.")
    llm_report: Optional[Dict[str, str]] = Field(
        default=None,
        description="Gemini AI narrative reports keyed by audience type."
    )
    investigation_status: Optional[str] = Field(
        default=None,
        description="Lifecycle state: PENDING_REVIEW, UNDER_REVIEW, CONFIRMED_FRAUD, FALSE_POSITIVE, ESCALATED, RESOLVED."
    )

    # ── Audit ─────────────────────────────────────────────────────────────
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
