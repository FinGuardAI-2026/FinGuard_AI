import pytest
from app.routers.search import rank_string_match

def test_rank_string_match():
    """Verify exact match gets weight 0, starts-with gets 1, contains gets 2, others get 3."""
    assert rank_string_match("Amazon", "Amazon") == 0
    assert rank_string_match("Amazon Inc", "Amazon") == 1
    assert rank_string_match("The Amazon Store", "Amazon") == 2
    assert rank_string_match("Google", "Amazon") == 3
    assert rank_string_match("", "Amazon") == 3
    assert rank_string_match("Amazon", "") == 3

class TestSearchRouter:
    @pytest.fixture
    def app_with_overrides(self):
        from app.main import create_app
        from app.dependencies.auth import get_current_user
        from fastapi.testclient import TestClient
        from unittest.mock import AsyncMock, MagicMock, patch

        app = create_app()

        self.mock_user = {
            "_id": "507f1f77bcf86cd799439011",
            "full_name": "Test User",
            "email": "test@finguard.ai",
            "role": "Fraud Analyst",
            "is_active": True,
        }

        # Build a mock DB that returns empty cursors for all collection queries
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_collection.find = MagicMock(return_value=mock_cursor)
        mock_collection.aggregate = MagicMock(return_value=mock_cursor)
        mock_collection.count_documents = AsyncMock(return_value=0)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        app.dependency_overrides[get_current_user] = lambda: self.mock_user

        with patch("app.routers.search.db_manager") as mock_dm:
            mock_dm.get_db.return_value = mock_db
            yield TestClient(app)

        app.dependency_overrides.clear()

    def test_search_empty_query(self, app_with_overrides):
        """GET /api/v1/search/?q= with empty query should return all empty lists."""
        response = app_with_overrides.get("/api/v1/search/?q=")
        assert response.status_code == 200
        body = response.json()
        assert body["users"] == []
        assert body["transactions"] == []
        assert body["predictions"] == []
        assert body["reports"] == []
        assert body["merchants"] == []
        assert body["countries"] == []
