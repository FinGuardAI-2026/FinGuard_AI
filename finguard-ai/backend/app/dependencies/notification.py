"""
backend/app/dependencies/notification.py
──────────────────────────────────────────
FastAPI dependency factories for the notification layer.
Follows the same pattern as dependencies/transaction.py.
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends

from app.dependencies.database import get_mongo_db
from app.repositories.notification import (
    NotificationRepository,
    NotificationPreferencesRepository,
)
from app.services.notification import NotificationService


async def get_notification_repository(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> NotificationRepository:
    """FastAPI Dependency providing the NotificationRepository."""
    return NotificationRepository(db)


async def get_preferences_repository(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> NotificationPreferencesRepository:
    """FastAPI Dependency providing the NotificationPreferencesRepository."""
    return NotificationPreferencesRepository(db)


async def get_notification_service(
    notification_repo: NotificationRepository = Depends(get_notification_repository),
    preferences_repo: NotificationPreferencesRepository = Depends(get_preferences_repository),
) -> NotificationService:
    """FastAPI Dependency providing the NotificationService."""
    return NotificationService(
        notification_repo=notification_repo,
        preferences_repo=preferences_repo,
    )
