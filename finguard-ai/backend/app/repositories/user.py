from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base import BaseRepository
from app.db.collections import collections

class UserRepository(BaseRepository):
    """User database repository implementing user-specific queries."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, collections.USERS)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Queries a user document matching the unique email address."""
        # Clean email to lower for query stability
        cleaned_email = email.strip().lower()
        return await self.find_one({"email": cleaned_email, "is_deleted": {"$ne": True}})
