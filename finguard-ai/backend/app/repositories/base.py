from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId

class BaseRepository:
    """Base repository class wrapping generic database operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str) -> None:
        self.db = db
        self.collection_name = collection_name
        self.collection: AsyncIOMotorCollection = db[collection_name]

    async def insert_one(self, document: Dict[str, Any]) -> str:
        """Inserts a single document and returns the stringified ObjectId."""
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Queries a single document matching the filter criteria."""
        # Convert _id string to ObjectId if present in query
        cls_query = self._format_query(filter_query)
        result = await self.collection.find_one(cls_query)
        return self._format_result(result) if result else None

    async def find_many(
        self,
        filter_query: Dict[str, Any],
        limit: int = 50,
        offset: int = 0,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """Queries multiple documents with pagination and sorting."""
        cls_query = self._format_query(filter_query)
        cursor = self.collection.find(cls_query)
        
        if sort:
            cursor = cursor.sort(sort)
            
        cursor = cursor.skip(offset).limit(limit)
        results = await cursor.to_list(length=limit)
        return [self._format_result(res) for res in results]

    async def update_one(
        self,
        filter_query: Dict[str, Any],
        update_data: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """Updates a single document matching the filter criteria."""
        cls_query = self._format_query(filter_query)
        # Ensure update directives are properly formatted (e.g. $set)
        if not any(key.startswith('$') for key in update_data.keys()):
            update_body = {"$set": update_data}
        else:
            update_body = update_data

        result = await self.collection.update_one(cls_query, update_body, upsert=upsert)
        return result.modified_count > 0 or (upsert and result.upserted_id is not None)

    async def delete_one(self, filter_query: Dict[str, Any]) -> bool:
        """Deletes a single document matching the filter criteria."""
        cls_query = self._format_query(filter_query)
        result = await self.collection.delete_one(cls_query)
        return result.deleted_count > 0

    async def count_documents(self, filter_query: Dict[str, Any]) -> int:
        """Counts the total documents matching the filter criteria."""
        cls_query = self._format_query(filter_query)
        return await self.collection.count_documents(cls_query)

    def _format_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Utility to convert hex string ids into BSON ObjectIds."""
        formatted = query.copy()
        if "_id" in formatted and isinstance(formatted["_id"], str):
            try:
                formatted["_id"] = ObjectId(formatted["_id"])
            except Exception:
                pass
        return formatted

    def _format_result(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Utility converting BSON ObjectId elements back to hexadecimal string ids."""
        formatted = document.copy()
        if "_id" in formatted:
            formatted["_id"] = str(formatted["_id"])
        return formatted
