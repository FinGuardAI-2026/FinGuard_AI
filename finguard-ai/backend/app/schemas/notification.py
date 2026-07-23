"""
backend/app/schemas/notification.py
─────────────────────────────────────
Pydantic v2 schemas for the /api/v1/notifications endpoints.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Notification Type Constants ───────────────────────────────────────────────

NOTIFICATION_TYPES = [
    "fraud_alert",
    "report",
    "system",
    "admin",
    "user_registered",
    "auth_login",
    "auth_logout",
    "auth_password_change",
    "profile_update",
    "role_change",
]

SEVERITY_LEVELS = ["critical", "high", "medium", "low", "info"]


# ── Create / Internal ─────────────────────────────────────────────────────────

class NotificationCreate(BaseModel):
    """Internal service-layer payload for creating a new notification."""

    user_id: str
    type: str
    title: str
    message: str
    severity: str = "info"
    action_required: bool = False
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ── Response ──────────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    """Single notification DTO returned by the API."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="MongoDB ObjectId as string.")
    user_id: str
    type: str
    title: str
    message: str
    severity: str
    action_required: bool
    action_url: Optional[str] = None
    is_read: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated list of notifications with aggregate counters."""

    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    limit: int


class UnreadCountResponse(BaseModel):
    """Fast unread-count poll response."""

    count: int


# ── Action Schemas ────────────────────────────────────────────────────────────

class MarkReadRequest(BaseModel):
    """Body for batch mark-read."""

    notification_ids: List[str] = Field(
        ...,
        min_length=1,
        description="List of notification ObjectId strings to mark as read.",
    )


# ── Preferences ───────────────────────────────────────────────────────────────

class NotificationTypePreference(BaseModel):
    """Per-type subscription toggle."""

    type: str
    enabled: bool = True
    label: str = ""


class NotificationPreferences(BaseModel):
    """
    User notification preferences.
    Stored in a separate 'notification_preferences' collection.
    Designed for future integration with email/push channels.
    """

    user_id: str

    # Which notification types to receive
    subscribed_types: List[NotificationTypePreference] = Field(
        default_factory=lambda: [
            NotificationTypePreference(type=t, enabled=True, label=t.replace("_", " ").title())
            for t in NOTIFICATION_TYPES
        ]
    )

    # In-app settings
    show_read_notifications: bool = True
    group_by_date: bool = True

    # Future: email / push channel settings (stored but not yet wired)
    email_enabled: bool = False
    push_enabled: bool = False
    quiet_hours_start: Optional[str] = None   # "22:00"
    quiet_hours_end: Optional[str] = None     # "08:00"

    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationPreferencesResponse(NotificationPreferences):
    """API response for preferences (mirrors the model)."""
    pass
