import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

class TestProfileRouter:
    @pytest.fixture
    def app_with_overrides(self):
        from app.main import create_app
        from app.dependencies.auth import get_current_user
        
        app = create_app()

        self.mock_user = {
            "_id": "507f1f77bcf86cd799439011",
            "full_name": "Jane Doe",
            "email": "jane.doe@finguard.ai",
            "role": "Fraud Analyst",
            "is_active": True,
            "avatar_color": "from-cyan-500 to-blue-600",
            "avatar_url": None,
            "preferences": {
                "email_notifications": True,
                "system_alerts": True,
                "theme": "dark",
                "language": "en"
            },
            "sessions": [
                {
                    "session_id": "session-123",
                    "ip_address": "127.0.0.1",
                    "user_agent": "Mozilla/5.0",
                    "device_type": "Desktop",
                    "browser": "Chrome",
                    "os": "macOS",
                    "location": "Local Network",
                    "created_at": datetime.utcnow().isoformat(),
                    "last_active": datetime.utcnow().isoformat()
                }
            ],
            "login_history": []
        }

        # Mock database connection
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        
        mock_collection.find = MagicMock(return_value=mock_cursor)
        mock_collection.aggregate = MagicMock(return_value=mock_cursor)
        mock_collection.count_documents = AsyncMock(return_value=0)
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_collection.update_one = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        from app.dependencies.database import get_mongo_db
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_mongo_db] = lambda: mock_db

        with patch("app.routers.auth.db_manager") as mock_dm:
            mock_dm.get_db.return_value = mock_db
            yield TestClient(app)

        app.dependency_overrides.clear()

    def test_get_profile_center(self, app_with_overrides):
        """GET /api/v1/auth/profile/center returns security scores, statistics, and recent objects."""
        response = app_with_overrides.get("/api/v1/auth/profile/center")
        assert response.status_code == 200
        body = response.json()
        assert "security_score" in body
        assert "profile_completion" in body
        assert "statistics" in body
        assert "recent_reports" in body
        assert "recent_notifications" in body

    def test_revoke_session_success(self, app_with_overrides):
        """POST /api/v1/auth/sessions/session-123/revoke revokes that device session."""
        response = app_with_overrides.post("/api/v1/auth/sessions/session-123/revoke")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True

    def test_revoke_session_not_found(self, app_with_overrides):
        """POST /api/v1/auth/sessions/missing-123/revoke returns 404."""
        response = app_with_overrides.post("/api/v1/auth/sessions/missing-123/revoke")
        assert response.status_code == 404
