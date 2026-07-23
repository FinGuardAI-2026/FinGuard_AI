"""
backend/app/services/notification.py
──────────────────────────────────────
NotificationService — creates all notification types.

Design principles:
  - All public methods are fire-and-forget safe: they catch every exception
    internally and log it. Callers should wrap in asyncio.create_task().
  - Factory methods produce human-readable titles + messages.
  - Admin-broadcast notifications use user_id='ADMIN'.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.repositories.notification import (
    NotificationRepository,
    NotificationPreferencesRepository,
)
from app.schemas.notification import (
    NOTIFICATION_TYPES,
    NotificationCreate,
    NotificationPreferences,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Orchestrates notification creation across all business event types.
    Injected via FastAPI dependency; also callable directly from services.
    """

    def __init__(
        self,
        notification_repo: NotificationRepository,
        preferences_repo: NotificationPreferencesRepository,
    ) -> None:
        self._repo = notification_repo
        self._prefs_repo = preferences_repo

    # ── Core Factory ──────────────────────────────────────────────────────

    async def create_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        message: str,
        severity: str = "info",
        action_required: bool = False,
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Persists a single notification document.
        Returns the created document ID or None on failure.
        """
        try:
            doc = {
                "user_id": user_id,
                "type": type,
                "title": title,
                "message": message,
                "severity": severity,
                "action_required": action_required,
                "action_url": action_url,
                "is_read": False,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            return await self._repo.insert_one(doc)
        except Exception as exc:
            logger.warning(f"[NotificationService] Failed to create notification: {exc}")
            return None

    # ── Fraud Predictions ─────────────────────────────────────────────────

    async def notify_fraud_prediction(
        self,
        user_id: str,
        transaction_id: str,
        fraud_probability: float,
        risk_level: str,
        amount: float,
    ) -> None:
        """Fires a fraud alert notification after a prediction is saved."""
        prob_pct = round(fraud_probability * 100, 1)
        is_critical = risk_level in ("Critical", "High") or fraud_probability >= 0.6

        if not is_critical:
            # Only notify on significant risk
            return

        severity = "critical" if risk_level == "Critical" else "high"
        action_required = risk_level == "Critical"

        await self.create_notification(
            user_id=user_id,
            type="fraud_alert",
            title=f"🚨 {risk_level} Fraud Alert — {transaction_id}",
            message=(
                f"Transaction {transaction_id} for ${amount:,.2f} was flagged with "
                f"a fraud probability of {prob_pct}% (Risk Level: {risk_level}). "
                f"{'Immediate review required.' if action_required else 'Please investigate.'}"
            ),
            severity=severity,
            action_required=action_required,
            action_url="/transactions",
            metadata={
                "transaction_id": transaction_id,
                "fraud_probability": fraud_probability,
                "risk_level": risk_level,
                "amount": amount,
            },
        )

    # ── Reports ───────────────────────────────────────────────────────────

    async def notify_report_generated(
        self,
        user_id: str,
        transaction_id: str,
        report_type: str = "fraud_investigation",
    ) -> None:
        """Fires when a Gemini AI report is successfully generated."""
        label = report_type.replace("_", " ").title()
        await self.create_notification(
            user_id=user_id,
            type="report",
            title=f"📄 {label} Report Ready",
            message=(
                f"The {label} report for transaction {transaction_id} "
                f"has been generated and is ready for review."
            ),
            severity="info",
            action_url="/reports",
            metadata={"transaction_id": transaction_id, "report_type": report_type},
        )

    # ── User Registration ─────────────────────────────────────────────────

    async def notify_user_registered(
        self,
        user_id: str,
        full_name: str,
        email: str,
    ) -> None:
        """Fires a welcome notification for the new user + admin broadcast."""
        # Welcome message for the new user
        await self.create_notification(
            user_id=user_id,
            type="user_registered",
            title="🎉 Welcome to FinGuard AI",
            message=(
                f"Hello {full_name}, your account has been created successfully. "
                f"You are now registered as a Fraud Analyst. "
                f"Start by running your first AI prediction."
            ),
            severity="info",
            action_url="/prediction",
            metadata={"full_name": full_name, "email": email},
        )
        # Admin broadcast
        await self.create_notification(
            user_id="ADMIN",
            type="admin",
            title=f"👤 New User Registered: {full_name}",
            message=f"A new account was registered with email {email}.",
            severity="info",
            metadata={"full_name": full_name, "email": email, "new_user_id": user_id},
        )

    # ── Admin Actions ─────────────────────────────────────────────────────

    async def notify_admin_action(
        self,
        target_user_id: str,
        action: str,
        performed_by: str,
        details: str = "",
    ) -> None:
        """Fires when an admin performs an action affecting a user."""
        await self.create_notification(
            user_id="ADMIN",
            type="admin",
            title=f"🔧 Admin Action: {action}",
            message=details or f"Action '{action}' was performed on user {target_user_id} by {performed_by}.",
            severity="high",
            metadata={
                "action": action,
                "target_user_id": target_user_id,
                "performed_by": performed_by,
            },
        )

    # ── System Alerts ─────────────────────────────────────────────────────

    async def notify_system_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        action_required: bool = False,
    ) -> None:
        """Fires a system-wide alert visible to all Admin users."""
        await self.create_notification(
            user_id="ADMIN",
            type="system",
            title=f"⚙️ {title}",
            message=message,
            severity=severity,
            action_required=action_required,
        )

    # ── Auth Events ───────────────────────────────────────────────────────

    async def notify_auth_login(
        self,
        user_id: str,
        email: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Fires on successful login."""
        location_hint = f" from IP {ip_address}" if ip_address else ""
        await self.create_notification(
            user_id=user_id,
            type="auth_login",
            title="🔐 New Sign-In Detected",
            message=(
                f"Your account ({email}) was signed in{location_hint}. "
                f"If this wasn't you, change your password immediately."
            ),
            severity="info",
            metadata={"email": email, "ip_address": ip_address},
        )

    async def notify_auth_logout(self, user_id: str) -> None:
        """Fires on logout."""
        await self.create_notification(
            user_id=user_id,
            type="auth_logout",
            title="👋 Signed Out",
            message="You have been signed out of FinGuard AI. Your session has ended.",
            severity="low",
        )

    async def notify_password_change(self, user_id: str, email: str) -> None:
        """Fires when a user's password is changed."""
        await self.create_notification(
            user_id=user_id,
            type="auth_password_change",
            title="🔑 Password Changed",
            message=(
                f"The password for {email} was successfully changed. "
                f"If you did not make this change, contact an administrator immediately."
            ),
            severity="high",
            action_required=False,
            metadata={"email": email},
        )

    # ── Profile & Role ────────────────────────────────────────────────────

    async def notify_profile_update(
        self,
        user_id: str,
        changed_fields: List[str],
    ) -> None:
        """Fires when a user updates their profile."""
        fields_str = ", ".join(changed_fields) if changed_fields else "profile"
        await self.create_notification(
            user_id=user_id,
            type="profile_update",
            title="✏️ Profile Updated",
            message=f"Your profile information ({fields_str}) was updated successfully.",
            severity="info",
            metadata={"changed_fields": changed_fields},
        )

    async def notify_role_change(
        self,
        user_id: str,
        old_role: str,
        new_role: str,
        changed_by: str,
    ) -> None:
        """Fires when a user's role is changed by an admin."""
        await self.create_notification(
            user_id=user_id,
            type="role_change",
            title="🛡️ Role Changed",
            message=(
                f"Your account role has been changed from '{old_role}' to '{new_role}' "
                f"by {changed_by}. Your access permissions have been updated."
            ),
            severity="high",
            action_required=True,
            action_url="/profile",
            metadata={
                "old_role": old_role,
                "new_role": new_role,
                "changed_by": changed_by,
            },
        )
        # Also notify admins
        await self.create_notification(
            user_id="ADMIN",
            type="admin",
            title=f"🛡️ Role Change: {old_role} → {new_role}",
            message=f"User {user_id} role changed from '{old_role}' to '{new_role}' by {changed_by}.",
            severity="high",
            metadata={
                "target_user_id": user_id,
                "old_role": old_role,
                "new_role": new_role,
                "changed_by": changed_by,
            },
        )

    # ── Preferences ───────────────────────────────────────────────────────

    async def get_preferences(self, user_id: str) -> NotificationPreferences:
        """Returns user preferences, falling back to defaults if not set."""
        doc = await self._prefs_repo.get_by_user(user_id)
        if doc:
            doc.pop("_id", None)
            return NotificationPreferences(**doc)
        return NotificationPreferences(user_id=user_id)

    async def update_preferences(
        self,
        user_id: str,
        preferences: NotificationPreferences,
    ) -> bool:
        """Persists user notification preferences."""
        prefs_dict = preferences.model_dump()
        prefs_dict.pop("user_id", None)
        return await self._prefs_repo.upsert(user_id, prefs_dict)
