"""
backend/app/routers/notifications.py
──────────────────────────────────────
REST API for the enterprise notification system.

All endpoints require JWT authentication.
Users can only access their own notifications.
Admin-broadcast notifications (user_id='ADMIN') are visible to Admin-role users.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.dependencies.auth import get_current_user, RoleChecker
from app.dependencies.notification import get_notification_service
from app.schemas.notification import (
    MarkReadRequest,
    NotificationListResponse,
    NotificationPreferences,
    NotificationPreferencesResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification import NotificationService

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
)

# ── RBAC helpers ──────────────────────────────────────────────────────────────

_any_authenticated = get_current_user
_admin_only = RoleChecker(["Admin"])


def _serialize_notification(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures _id is present for alias mapping in NotificationResponse."""
    out = dict(doc)
    if "_id" not in out and "id" in out:
        out["_id"] = out.pop("id")
    return out


# ── List / Read ───────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List notifications",
    description="Returns paginated notifications for the authenticated user. Admins also receive ADMIN-broadcast notifications.",
    responses={
        200: {"description": "Notification list returned"},
        401: {"description": "Not authenticated"},
    },
)
async def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    type_filter: Optional[str] = Query(default=None, alias="type"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    """Returns the notification feed for the current user."""
    user_id = str(current_user["_id"])
    is_admin = current_user.get("role") == "Admin"

    repo = svc._repo

    # Fetch user-specific notifications
    user_notifications = await repo.get_by_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
        type_filter=type_filter,
    )

    # Admins additionally receive ADMIN-broadcast notifications
    if is_admin:
        admin_notifications = await repo.get_by_user(
            user_id="ADMIN",
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            type_filter=type_filter,
        )
        # Merge + sort by created_at descending
        combined = user_notifications + admin_notifications
        combined.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        notifications = combined[:limit]
    else:
        notifications = user_notifications

    # Counts
    user_total = await repo.get_total_count(user_id, unread_only, type_filter)
    user_unread = await repo.get_unread_count(user_id)
    admin_unread = 0
    admin_total = 0
    if is_admin:
        admin_unread = await repo.get_unread_count("ADMIN")
        admin_total = await repo.get_total_count("ADMIN", unread_only, type_filter)

    serialized = [
        NotificationResponse(**_serialize_notification(n)) for n in notifications
    ]

    return NotificationListResponse(
        notifications=serialized,
        total=user_total + admin_total,
        unread_count=user_unread + admin_unread,
        page=(offset // limit) + 1,
        limit=limit,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get unread notification count",
    description="Lightweight endpoint polled every 30s by the frontend bell badge.",
    responses={
        200: {"description": "Unread count returned"},
        401: {"description": "Not authenticated"},
    },
)
async def get_unread_count(
    current_user: Dict[str, Any] = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> UnreadCountResponse:
    """Returns the total unread notification count for the current user."""
    user_id = str(current_user["_id"])
    is_admin = current_user.get("role") == "Admin"

    repo = svc._repo
    count = await repo.get_unread_count(user_id)
    if is_admin:
        count += await repo.get_unread_count("ADMIN")

    return UnreadCountResponse(count=count)


# ── Preferences ───────────────────────────────────────────────────────────────

@router.get(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Get notification preferences",
    description="Returns the user's notification preferences. Defaults are returned if not yet configured.",
)
async def get_preferences(
    current_user: Dict[str, Any] = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationPreferencesResponse:
    """Returns notification preferences for the current user."""
    user_id = str(current_user["_id"])
    prefs = await svc.get_preferences(user_id)
    return NotificationPreferencesResponse(**prefs.model_dump())


@router.put(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Update notification preferences",
    description="Persists notification preferences for the current user.",
)
async def update_preferences(
    preferences: NotificationPreferences,
    current_user: Dict[str, Any] = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> NotificationPreferencesResponse:
    """Saves notification preferences for the current user."""
    user_id = str(current_user["_id"])
    preferences.user_id = user_id
    await svc.update_preferences(user_id, preferences)
    return NotificationPreferencesResponse(**preferences.model_dump())


# ── Mark Read ─────────────────────────────────────────────────────────────────

@router.patch(
    "/{notification_id}/read",
    summary="Mark a notification as read",
    responses={
        200: {"description": "Notification marked as read"},
        404: {"description": "Notification not found"},
    },
)
async def mark_notification_read(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> JSONResponse:
    """Marks a single notification as read."""
    user_id = str(current_user["_id"])
    is_admin = current_user.get("role") == "Admin"

    repo = svc._repo
    # Try user's own notifications first
    success = await repo.mark_read(notification_id, user_id)
    # Admins can also mark ADMIN-broadcast notifications
    if not success and is_admin:
        success = await repo.mark_read(notification_id, "ADMIN")

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or already read.",
        )
    return JSONResponse(content={"success": True, "message": "Notification marked as read."})


@router.patch(
    "/mark-all-read",
    summary="Mark all notifications as read",
    responses={200: {"description": "All notifications marked as read"}},
)
async def mark_all_read(
    current_user: Dict[str, Any] = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> JSONResponse:
    """Marks all unread notifications as read for the current user."""
    user_id = str(current_user["_id"])
    is_admin = current_user.get("role") == "Admin"

    repo = svc._repo
    count = await repo.mark_all_read(user_id)
    if is_admin:
        count += await repo.mark_all_read("ADMIN")

    return JSONResponse(
        content={"success": True, "marked_count": count, "message": f"{count} notifications marked as read."}
    )


@router.patch(
    "/bulk-read",
    summary="Mark a list of notifications as read",
    responses={200: {"description": "Bulk mark-read completed"}},
)
async def bulk_mark_read(
    body: MarkReadRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> JSONResponse:
    """Marks a specific set of notification IDs as read."""
    user_id = str(current_user["_id"])
    is_admin = current_user.get("role") == "Admin"

    repo = svc._repo
    count = await repo.bulk_mark_read(body.notification_ids, user_id)
    if is_admin:
        count += await repo.bulk_mark_read(body.notification_ids, "ADMIN")

    return JSONResponse(
        content={"success": True, "marked_count": count}
    )


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete(
    "/clear-read",
    summary="Delete all read notifications",
    responses={200: {"description": "Read notifications cleared"}},
)
async def clear_read_notifications(
    current_user: Dict[str, Any] = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> JSONResponse:
    """Deletes all read notifications for the current user."""
    user_id = str(current_user["_id"])
    count = await svc._repo.delete_all_read(user_id)
    return JSONResponse(
        content={"success": True, "deleted_count": count, "message": f"{count} read notifications cleared."}
    )


@router.delete(
    "/{notification_id}",
    summary="Delete a notification",
    responses={
        200: {"description": "Notification deleted"},
        404: {"description": "Notification not found"},
    },
)
async def delete_notification(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
) -> JSONResponse:
    """Deletes a single notification (scoped to the authenticated user)."""
    user_id = str(current_user["_id"])
    is_admin = current_user.get("role") == "Admin"

    repo = svc._repo
    success = await repo.delete_notification(notification_id, user_id)
    if not success and is_admin:
        success = await repo.delete_notification(notification_id, "ADMIN")

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return JSONResponse(content={"success": True, "message": "Notification deleted."})
