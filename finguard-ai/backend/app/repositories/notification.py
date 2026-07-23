"""
backend/app/repositories/notification.py
──────────────────────────────────────────
Repository for the 'notifications' and 'notification_preferences' collections.
Extends BaseRepository with notification-specific query helpers.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import pymongo
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    """CRUD operations for the notifications collection."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, "notifications")

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
        type_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns paginated notifications for a user, newest first.
        Admin-broadcast notifications (user_id='ADMIN') are returned
        for all users who have the Admin role — the router handles that.
        """
        query: Dict[str, Any] = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        if type_filter:
            query["type"] = type_filter

        cursor = (
            self.collection.find(self._format_query(query))
            .sort("created_at", pymongo.DESCENDING)
            .skip(offset)
            .limit(limit)
        )
        results = await cursor.to_list(length=limit)
        return [self._format_result(r) for r in results]

    async def get_unread_count(self, user_id: str) -> int:
        """Fast unread count — used by the 30-second polling endpoint."""
        return await self.collection.count_documents(
            {"user_id": user_id, "is_read": False}
        )

    async def get_total_count(
        self,
        user_id: str,
        unread_only: bool = False,
        type_filter: Optional[str] = None,
    ) -> int:
        """Total documents count for pagination metadata."""
        query: Dict[str, Any] = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        if type_filter:
            query["type"] = type_filter
        return await self.collection.count_documents(query)

    # ── Update ────────────────────────────────────────────────────────────

    async def mark_read(self, notification_id: str, user_id: str) -> bool:
        """Marks a single notification as read (scoped to owning user)."""
        now = datetime.utcnow()
        return await self.update_one(
            {"_id": notification_id, "user_id": user_id},
            {"$set": {"is_read": True, "updated_at": now}},
        )

    async def mark_all_read(self, user_id: str) -> int:
        """Marks all unread notifications as read. Returns modified count."""
        now = datetime.utcnow()
        result = await self.collection.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True, "updated_at": now}},
        )
        return result.modified_count

    async def bulk_mark_read(self, notification_ids: List[str], user_id: str) -> int:
        """Marks a specific list of notification IDs as read."""
        from bson import ObjectId

        object_ids = []
        for nid in notification_ids:
            try:
                object_ids.append(ObjectId(nid))
            except Exception:
                pass

        if not object_ids:
            return 0

        now = datetime.utcnow()
        result = await self.collection.update_many(
            {"_id": {"$in": object_ids}, "user_id": user_id},
            {"$set": {"is_read": True, "updated_at": now}},
        )
        return result.modified_count

    # ── Delete ────────────────────────────────────────────────────────────

    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Deletes a single notification (scoped to owning user)."""
        return await self.delete_one({"_id": notification_id, "user_id": user_id})

    async def delete_all_read(self, user_id: str) -> int:
        """Deletes all read notifications for a user. Returns deleted count."""
        result = await self.collection.delete_many(
            {"user_id": user_id, "is_read": True}
        )
        return result.deleted_count


class NotificationPreferencesRepository(BaseRepository):
    """CRUD for the notification_preferences collection (one doc per user)."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, "notification_preferences")

    async def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"user_id": user_id})

    async def upsert(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Creates or replaces the preferences document for a user."""
        preferences["user_id"] = user_id
        preferences["updated_at"] = datetime.utcnow()
        result = await self.collection.replace_one(
            {"user_id": user_id},
            preferences,
            upsert=True,
        )
        return result.matched_count > 0 or result.upserted_id is not None
