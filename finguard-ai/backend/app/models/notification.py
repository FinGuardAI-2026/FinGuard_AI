"""
backend/app/models/notification.py
────────────────────────────────────
MongoDB document model for the notifications collection.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class NotificationDB(BaseModel):
    """Represents a single notification document stored in MongoDB."""

    user_id: str = Field(
        ...,
        description=(
            "Target user's ObjectId string. "
            "Use 'ADMIN' for admin-broadcast notifications."
        ),
    )
    type: str = Field(
        ...,
        description=(
            "Notification type discriminator. One of: fraud_alert, report, "
            "system, admin, user_registered, auth_login, auth_logout, "
            "auth_password_change, profile_update, role_change."
        ),
    )
    title: str = Field(..., description="Short human-readable title.")
    message: str = Field(..., description="Full notification body text.")
    severity: str = Field(
        default="info",
        description="One of: critical, high, medium, low, info.",
    )

    # ── Action-required flag ──────────────────────────────────────────────
    action_required: bool = Field(
        default=False,
        description="When True, the notification requires explicit user action.",
    )
    action_url: Optional[str] = Field(
        default=None,
        description="Optional relative frontend path the action button links to.",
    )

    # ── Read state ────────────────────────────────────────────────────────
    is_read: bool = Field(default=False)

    # ── Extra context ─────────────────────────────────────────────────────
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form key/value context (transaction_id, amount, etc.).",
    )

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
