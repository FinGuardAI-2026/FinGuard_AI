import re
from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from enum import Enum


# ── Enum Constraints ─────────────────────────────────────────────────────────

class TransactionStatus(str, Enum):
    PENDING   = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"
    FLAGGED   = "FLAGGED"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD  = "DEBIT_CARD"
    ACH         = "ACH"
    WIRE        = "WIRE"
    APPLE_PAY   = "APPLE_PAY"
    GOOGLE_PAY  = "GOOGLE_PAY"
    CRYPTO      = "CRYPTO"

class TransactionType(str, Enum):
    PURCHASE   = "PURCHASE"
    TRANSFER   = "TRANSFER"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT    = "DEPOSIT"
    REFUND     = "REFUND"

class SortField(str, Enum):
    AMOUNT   = "amount"
    DATE     = "transaction_time"
    MERCHANT = "merchant_name"

class SortOrder(str, Enum):
    ASC  = "asc"
    DESC = "desc"


# ── Request Schemas ───────────────────────────────────────────────────────────

class TransactionCreateRequest(BaseModel):
    """Payload for creating a new transaction record."""

    amount: float = Field(
        ..., gt=0,
        examples=[1250.75],
        description="Must be a positive number.",
    )
    currency: str = Field(
        ..., min_length=3, max_length=3,
        examples=["USD"],
        description="ISO 4217 3-letter currency code.",
    )
    merchant_name: str = Field(
        ..., min_length=1, max_length=200,
        examples=["Amazon Prime"],
    )
    merchant_category: str = Field(
        ...,
        examples=["E-COMMERCE"],
        description="MCC category label.",
    )
    payment_method: PaymentMethod  = Field(..., examples=["CREDIT_CARD"])
    transaction_type: TransactionType = Field(..., examples=["PURCHASE"])
    country: str = Field(
        ..., min_length=2, max_length=3,
        examples=["USA"],
        description="ISO 3166-1 country code.",
    )
    city: Optional[str]           = Field(default=None, examples=["New York"])
    latitude: Optional[float]     = Field(default=None, examples=[40.7128],  ge=-90.0,  le=90.0)
    longitude: Optional[float]    = Field(default=None, examples=[-74.0060], ge=-180.0, le=180.0)
    ip_address: str = Field(
        ...,
        examples=["203.0.113.42"],
        description="IPv4 or IPv6 address of originating device.",
    )
    device_id: str = Field(
        ...,
        examples=["DEV-a1b2c3d4e5f6"],
        min_length=4, max_length=100,
    )
    browser: Optional[str]           = Field(default=None, examples=["Chrome/124.0"])
    operating_system: Optional[str]  = Field(default=None, examples=["Windows 11"])
    transaction_time: Optional[datetime] = Field(
        default=None,
        examples=["2026-06-28T00:00:00Z"],
        description="UTC timestamp of the transaction. Defaults to now if not provided.",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Enforces uppercase ISO 4217 currency codes."""
        if not v.isalpha() or not v.isupper():
            raise ValueError("Currency must be a 3-letter uppercase ISO 4217 code, e.g. 'USD'.")
        return v

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        """Validates IPv4 or IPv6 address format."""
        ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        ipv6_pattern = r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$"
        if not (re.match(ipv4_pattern, v) or re.match(ipv6_pattern, v)):
            raise ValueError("ip_address must be a valid IPv4 or IPv6 address.")
        return v

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        """Rejects device IDs containing unsafe characters."""
        if not re.match(r"^[a-zA-Z0-9\-_\.]+$", v):
            raise ValueError("device_id may only contain alphanumeric characters, hyphens, underscores, and dots.")
        return v

    @field_validator("transaction_time", mode="before")
    @classmethod
    def validate_not_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Rejects timestamps set in the future."""
        if v and v > datetime.utcnow():
            raise ValueError("transaction_time cannot be in the future.")
        return v


class TransactionUpdateRequest(BaseModel):
    """Payload for partially updating a transaction record (all fields optional)."""

    amount: Optional[float]           = Field(default=None, gt=0, examples=[1500.00])
    currency: Optional[str]           = Field(default=None, min_length=3, max_length=3, examples=["GBP"])
    merchant_name: Optional[str]      = Field(default=None, max_length=200)
    merchant_category: Optional[str]  = Field(default=None)
    payment_method: Optional[PaymentMethod]   = Field(default=None)
    transaction_type: Optional[TransactionType] = Field(default=None)
    status: Optional[TransactionStatus]       = Field(default=None)
    country: Optional[str]            = Field(default=None, min_length=2, max_length=3)
    city: Optional[str]               = Field(default=None)
    latitude: Optional[float]         = Field(default=None, ge=-90.0,  le=90.0)
    longitude: Optional[float]        = Field(default=None, ge=-180.0, le=180.0)
    browser: Optional[str]            = Field(default=None)
    operating_system: Optional[str]   = Field(default=None)

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "TransactionUpdateRequest":
        """Ensures the update payload is not empty."""
        values = self.model_dump(exclude_none=True)
        if not values:
            raise ValueError("At least one field must be provided for an update.")
        return self


# ── Response Schemas ─────────────────────────────────────────────────────────

class TransactionResponse(BaseModel):
    """Full transaction document returned to the caller."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    merchant_name: str
    merchant_category: str
    payment_method: str
    transaction_type: str
    status: str
    country: str
    city: Optional[str]                    = None
    latitude: Optional[float]             = None
    longitude: Optional[float]            = None
    ip_address: str
    device_id: str
    browser: Optional[str]                = None
    operating_system: Optional[str]       = None
    transaction_time: datetime
    # Future ML/AI fields (nullable)
    prediction: Optional[str]             = None
    fraud_probability: Optional[float]    = None
    confidence_score: Optional[float]     = None
    risk_score: Optional[float]           = None
    shap_summary: Optional[Dict[str, Any]] = None
    llm_report: Optional[Dict[str, str]]  = None
    investigation_status: Optional[str]   = None
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """Paginated list of transaction records."""

    transactions: List[TransactionResponse]
    total_records: int
    total_pages: int
    page: int
    page_size: int


# ── Query Filter Schema ───────────────────────────────────────────────────────

class TransactionFilterParams(BaseModel):
    """URL query parameters for filtering, searching, sorting, and pagination."""

    # Search
    transaction_id: Optional[str]          = Field(default=None, description="Exact transaction UUID match.")
    merchant: Optional[str]                = Field(default=None, description="Partial merchant name search.")
    country: Optional[str]                 = Field(default=None)
    payment_method: Optional[PaymentMethod] = Field(default=None)

    # Filters
    min_amount: Optional[float]            = Field(default=None, ge=0)
    max_amount: Optional[float]            = Field(default=None, ge=0)
    date_from: Optional[datetime]          = Field(default=None)
    date_to: Optional[datetime]            = Field(default=None)
    merchant_category: Optional[str]       = Field(default=None)
    status: Optional[TransactionStatus]    = Field(default=None)

    # Sorting
    sort_by: SortField    = Field(default=SortField.DATE)
    sort_order: SortOrder = Field(default=SortOrder.DESC)

    # Pagination
    page: int      = Field(default=1,  ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
