import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, HTTPException

from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferences,
)
from app.services.notification import NotificationService
from app.repositories.notification import (
    NotificationRepository,
    NotificationPreferencesRepository,
)


# ── 1. Schema Validation Tests ───────────────────────────────────────────────
class TestNotificationSchemas:
    def test_notification_create_defaults(self):
        """NotificationCreate should populate defaults correctly."""
        req = NotificationCreate(
            user_id="user_123",
            type="fraud_alert",
            title="Suspicious Activity",
            message="Check txn 9921",
        )
        assert req.severity == "info"
        assert req.action_required is False
        assert req.action_url is None
        assert req.metadata == {}

    def test_notification_response_serialization(self):
        """NotificationResponse should successfully initialize from dict with ObjectId."""
        data = {
            "_id": "507f1f77bcf86cd799439011",
            "user_id": "user_123",
            "type": "fraud_alert",
            "title": "Alert",
            "message": "Flagged",
            "severity": "critical",
            "action_required": True,
            "action_url": "/tx",
            "is_read": False,
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        res = NotificationResponse(**data)
        assert res.id == "507f1f77bcf86cd799439011"
        assert res.severity == "critical"
        assert res.action_required is True


# ── 2. NotificationService Unit Tests ───────────────────────────────────────────
@pytest.mark.asyncio
class TestNotificationService:
    async def test_notify_fraud_prediction_critical(self):
        """notify_fraud_prediction should create a critical action-required notification for high risk."""
        mock_notif_repo = AsyncMock()
        mock_prefs_repo = AsyncMock()
        service = NotificationService(mock_notif_repo, mock_prefs_repo)

        mock_notif_repo.insert_one.return_value = "new_notif_id"

        await service.notify_fraud_prediction(
            user_id="user_123",
            transaction_id="TXN-9921",
            fraud_probability=0.85,
            risk_level="Critical",
            amount=5000.0,
        )

        mock_notif_repo.insert_one.assert_called_once()
        inserted_doc = mock_notif_repo.insert_one.call_args[0][0]
        assert inserted_doc["user_id"] == "user_123"
        assert inserted_doc["type"] == "fraud_alert"
        assert inserted_doc["severity"] == "critical"
        assert inserted_doc["action_required"] is True
        assert inserted_doc["action_url"] == "/transactions"

    async def test_notify_fraud_prediction_low_ignored(self):
        """notify_fraud_prediction should not fire notification if risk is low/info."""
        mock_notif_repo = AsyncMock()
        mock_prefs_repo = AsyncMock()
        service = NotificationService(mock_notif_repo, mock_prefs_repo)

        await service.notify_fraud_prediction(
            user_id="user_123",
            transaction_id="TXN-9921",
            fraud_probability=0.10,
            risk_level="Low",
            amount=10.0,
        )

        mock_notif_repo.insert_one.assert_not_called()

    async def test_notify_user_registered(self):
        """notify_user_registered should fire welcome alert and admin broadcast alert."""
        mock_notif_repo = AsyncMock()
        mock_prefs_repo = AsyncMock()
        service = NotificationService(mock_notif_repo, mock_prefs_repo)

        await service.notify_user_registered(
            user_id="user_123",
            full_name="Jane Analyst",
            email="jane@finguard.ai",
        )

        assert mock_notif_repo.insert_one.call_count == 2
        calls = [args[0][0] for args in mock_notif_repo.insert_one.call_args_list]
        
        # User welcome notification
        assert any(c["user_id"] == "user_123" and c["type"] == "user_registered" for c in calls)
        # Admin broadcast notification
        assert any(c["user_id"] == "ADMIN" and c["type"] == "admin" for c in calls)

    async def test_notify_role_change(self):
        """notify_role_change should fire user and admin-broadcast alerts."""
        mock_notif_repo = AsyncMock()
        mock_prefs_repo = AsyncMock()
        service = NotificationService(mock_notif_repo, mock_prefs_repo)

        await service.notify_role_change(
            user_id="user_123",
            old_role="Fraud Analyst",
            new_role="Admin",
            changed_by="Head Admin",
        )

        assert mock_notif_repo.insert_one.call_count == 2


# ── 3. Notification Router Integration Tests ──────────────────────────────────
class TestNotificationRouter:
    @pytest.fixture
    def app_with_overrides(self):
        from app.main import create_app
        from app.dependencies.auth import get_current_user
        from app.dependencies.notification import get_notification_service

        app = create_app()

        # Mock dependencies
        self.mock_user = {
            "_id": "507f1f77bcf86cd799439011",
            "full_name": "Test User",
            "email": "test@finguard.ai",
            "role": "Fraud Analyst",
            "is_active": True,
        }

        self.mock_notif_repo = AsyncMock()
        self.mock_prefs_repo = AsyncMock()
        self.mock_service = NotificationService(self.mock_notif_repo, self.mock_prefs_repo)

        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_notification_service] = lambda: self.mock_service

        yield app

        app.dependency_overrides.clear()

    def test_list_notifications_endpoint(self, app_with_overrides):
        """GET /api/v1/notifications/ should return list of serialized notifications."""
        client = TestClient(app_with_overrides)
        
        fake_docs = [{
            "_id": "507f1f77bcf86cd799439011",
            "user_id": "507f1f77bcf86cd799439011",
            "type": "system",
            "title": "Welcome Alert",
            "message": "Welcome onboard!",
            "severity": "info",
            "action_required": False,
            "is_read": False,
            "metadata": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }]
        
        self.mock_notif_repo.get_by_user.return_value = fake_docs
        self.mock_notif_repo.get_total_count.return_value = 1
        self.mock_notif_repo.get_unread_count.return_value = 1

        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert len(body["notifications"]) == 1
        assert body["notifications"][0]["title"] == "Welcome Alert"

    def test_get_unread_count_endpoint(self, app_with_overrides):
        """GET /api/v1/notifications/unread-count should return count of unread alerts."""
        client = TestClient(app_with_overrides)
        self.mock_notif_repo.get_unread_count.return_value = 5

        response = client.get("/api/v1/notifications/unread-count")
        assert response.status_code == 200
        assert response.json()["count"] == 5

    def test_mark_read_endpoint(self, app_with_overrides):
        """PATCH /api/v1/notifications/{id}/read should mark the notification read."""
        client = TestClient(app_with_overrides)
        self.mock_notif_repo.mark_read.return_value = True

        response = client.patch("/api/v1/notifications/507f1f77bcf86cd799439011/read")
        assert response.status_code == 200
        assert response.json()["success"] is True
        self.mock_notif_repo.mark_read.assert_called_once_with(
            "507f1f77bcf86cd799439011", "507f1f77bcf86cd799439011"
        )
