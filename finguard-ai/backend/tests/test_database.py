import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories.base import BaseRepository

@pytest.mark.asyncio
async def test_repository_insert_one():
    """Verifies BaseRepository insert_one triggers motor's internal insert call."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    # Configure mock return value for collection insert
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = "507f1f77bcf86cd799439011"
    mock_collection.insert_one = AsyncMock(return_value=mock_insert_result)
    mock_db.__getitem__.return_value = mock_collection

    repo = BaseRepository(mock_db, "test_collection")
    document = {"name": "test_record"}
    
    doc_id = await repo.insert_one(document)
    
    assert doc_id == "507f1f77bcf86cd799439011"
    mock_collection.insert_one.assert_called_once_with(document)

@pytest.mark.asyncio
async def test_repository_find_one():
    """Verifies BaseRepository find_one triggers motor's find_one call and formats result id."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    from bson import ObjectId
    mock_id = ObjectId("507f1f77bcf86cd799439011")
    mock_doc = {"_id": mock_id, "name": "test_record"}
    
    mock_collection.find_one = AsyncMock(return_value=mock_doc)
    mock_db.__getitem__.return_value = mock_collection

    repo = BaseRepository(mock_db, "test_collection")
    result = await repo.find_one({"_id": "507f1f77bcf86cd799439011"})
    
    assert result is not None
    assert result["_id"] == "507f1f77bcf86cd799439011"
    mock_collection.find_one.assert_called_once()
