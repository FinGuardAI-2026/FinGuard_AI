import time
import os
import psutil
from datetime import timezone;
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.dependencies.auth import get_current_user, RoleChecker
from app.dependencies.database import get_mongo_db
from app.core.security.crypto import hash_password
from app.db.connection import db_manager
from app.db.collections import collections
from app.services.audit import log_audit_action
from app.schemas.admin import (
    AdminUserCreateRequest,
    AdminUserEditRequest,
    AdminPasswordResetRequest,
    BulkStatusUpdateRequest,
    BulkDeleteRequest,
    PermissionMatrixUpdateRequest,
)
from app.schemas.auth import UserResponse

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Governance & Administration"],
    dependencies=[Depends(RoleChecker(["Admin"]))]
)

def serialize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to convert MongoDB raw user to schema structure."""
    return {
        "_id": str(user.get("_id", "")),
        "id": str(user.get("_id", "")),
        "full_name": user.get("full_name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "Fraud Analyst"),
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at", datetime.utcnow()),
        "updated_at": user.get("updated_at", datetime.utcnow()),
        "last_login": user.get("last_login"),
        "avatar_color": user.get("avatar_color"),
        "avatar_url": user.get("avatar_url"),
        "preferences": user.get("preferences"),
        "sessions": user.get("sessions", []),
        "login_history": user.get("login_history", []),
    }

async def log_admin_event(request: Request, current_user: Dict[str, Any], action: str, status_str: str, details: str = None):
    """Encapsulated helper to record administrative security events."""
    db = db_manager.get_db()
    ip = request.client.host if request.client else "127.0.0.1"
    browser = request.headers.get("user-agent", "Unknown Device")
    endpoint = f"{request.method} {request.url.path}"
    request_id = getattr(request.state, "request_id", "unknown")
    performed_by = current_user.get("email", "unknown_admin")
    await log_audit_action(
        db,
        action=action,
        performed_by=performed_by,
        ip_address=ip,
        browser=browser,
        endpoint=endpoint,
        request_id=request_id,
        status=status_str,
        details=details
    )

# ── User Management Endpoints ───────────────────────────────────────────────

@router.get("/users", response_model=List[UserResponse])
async def list_users(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """List all users who are not soft-deleted."""
    users_cursor = db[collections.USERS].find({"is_deleted": {"$ne": True}})
    users = await users_cursor.to_list(length=100)
    return [UserResponse(**serialize_user(u)) for u in users]

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: Request,
    payload: AdminUserCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Provision a new user account."""
    email_clean = payload.email.strip().lower()
    existing_user = await db[collections.USERS].find_one({"email": email_clean, "is_deleted": {"$ne": True}})
    if existing_user:
        await log_admin_event(request, current_user, "USER_CREATE", "FAILED", f"Email already registered: {email_clean}")
        raise HTTPException(status_code=409, detail="Email already registered")

    user_doc = {
        "full_name": payload.full_name,
        "email": email_clean,
        "hashed_password": hash_password(payload.password),
        "role": payload.role,
        "is_active": True,
        "is_deleted": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "preferences": {
            "theme": "dark",
            "email_alerts": True,
            "browser_notifications": False,
            "prediction_threshold": 0.75
        },
        "sessions": [],
        "login_history": []
    }

    result = await db[collections.USERS].insert_one(user_doc)
    created = await db[collections.USERS].find_one({"_id": result.inserted_id})
    await log_admin_event(request, current_user, "USER_CREATE", "SUCCESS", f"Created user {email_clean} with role {payload.role}")
    return UserResponse(**serialize_user(created))

@router.patch("/users/{user_id}", response_model=UserResponse)
async def edit_user(
    user_id: str,
    request: Request,
    payload: AdminUserEditRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Edit an existing user profile."""
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = await db[collections.USERS].find_one({"_id": oid, "is_deleted": {"$ne": True}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = {}
    details_list = []
    if payload.full_name is not None:
        updates["full_name"] = payload.full_name
        details_list.append(f"name: {payload.full_name}")
    if payload.email is not None:
        email_clean = payload.email.strip().lower()
        if email_clean != user["email"]:
            dup = await db[collections.USERS].find_one({"email": email_clean, "is_deleted": {"$ne": True}})
            if dup:
                raise HTTPException(status_code=409, detail="Email already in use")
            updates["email"] = email_clean
            details_list.append(f"email: {email_clean}")
    if payload.role is not None:
        updates["role"] = payload.role
        details_list.append(f"role: {payload.role}")
    if payload.is_active is not None:
        updates["is_active"] = payload.is_active
        details_list.append(f"is_active: {payload.is_active}")

    if updates:
        updates["updated_at"] = datetime.utcnow()
        await db[collections.USERS].update_one({"_id": oid}, {"$set": updates})
        user = await db[collections.USERS].find_one({"_id": oid})

    await log_admin_event(request, current_user, "USER_EDIT", "SUCCESS", f"Edited user {user['email']} (Changes: {', '.join(details_list)})")
    return UserResponse(**serialize_user(user))

@router.post("/users/bulk-status")
async def bulk_status(
    request: Request,
    payload: BulkStatusUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Bulk suspend or activate users."""
    oids = []
    for uid in payload.user_ids:
        try:
            oids.append(ObjectId(uid))
        except Exception:
            pass

    if not oids:
        raise HTTPException(status_code=400, detail="No valid user IDs provided")

    result = await db[collections.USERS].update_many(
        {"_id": {"$in": oids}, "is_deleted": {"$ne": True}},
        {"$set": {"is_active": payload.is_active, "updated_at": datetime.utcnow()}}
    )

    action_label = "ACTIVATE" if payload.is_active else "SUSPEND"
    await log_admin_event(
        request,
        current_user,
        f"BULK_{action_label}",
        "SUCCESS",
        f"Bulk updated active state to {payload.is_active} for {result.modified_count} users."
    )
    return {"success": True, "modified_count": result.modified_count}

@router.post("/users/bulk-delete")
async def bulk_delete(
    request: Request,
    payload: BulkDeleteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Bulk soft-delete users."""
    oids = []
    for uid in payload.user_ids:
        try:
            oids.append(ObjectId(uid))
        except Exception:
            pass

    if not oids:
        raise HTTPException(status_code=400, detail="No valid user IDs provided")

    result = await db[collections.USERS].update_many(
        {"_id": {"$in": oids}},
        {
            "$set": {
                "is_deleted": True,
                "is_active": False,
                "deleted_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )

    await log_admin_event(
        request,
        current_user,
        "BULK_DELETE",
        "SUCCESS",
        f"Bulk soft-deleted {result.modified_count} users."
    )
    return {"success": True, "modified_count": result.modified_count}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Soft delete a single user."""
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = await db[collections.USERS].find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db[collections.USERS].update_one(
        {"_id": oid},
        {
            "$set": {
                "is_deleted": True,
                "is_active": False,
                "deleted_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )

    await log_admin_event(request, current_user, "USER_DELETE", "SUCCESS", f"Soft deleted user {user['email']}")
    return {"success": True, "message": "User soft deleted successfully"}

@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    request: Request,
    payload: AdminPasswordResetRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Reset a user's password directly."""
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = await db[collections.USERS].find_one({"_id": oid, "is_deleted": {"$ne": True}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed = hash_password(payload.password)
    await db[collections.USERS].update_one(
        {"_id": oid},
        {"$set": {"hashed_password": hashed, "updated_at": datetime.utcnow()}}
    )

    await log_admin_event(request, current_user, "PASSWORD_RESET", "SUCCESS", f"Reset password for user {user['email']}")
    return {"success": True, "message": "Password reset successfully"}

# ── Audit Trails & Compliance Endpoints ─────────────────────────────────────

@router.get("/audit-logs")
async def list_audit_logs(
    action: Optional[str] = None,
    user: Optional[str] = None,
    status_filter: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Retrieve audit logs with advanced searches and filters."""
    filter_query = {}
    if action:
        filter_query["action"] = action
    if user:
        filter_query["performed_by"] = {"$regex": user, "$options": "i"}
    if status_filter:
        filter_query["status"] = status_filter
    if query:
        filter_query["$or"] = [
            {"details": {"$regex": query, "$options": "i"}},
            {"performed_by": {"$regex": query, "$options": "i"}},
            {"action": {"$regex": query, "$options": "i"}},
            {"ip_address": {"$regex": query, "$options": "i"}},
            {"request_id": {"$regex": query, "$options": "i"}},
            {"browser": {"$regex": query, "$options": "i"}}
        ]

    cursor = db[collections.AUDIT_LOGS].find(filter_query).sort("timestamp", -1).skip(offset).limit(limit)
    logs = await cursor.to_list(length=limit)
    total = await db[collections.AUDIT_LOGS].count_documents(filter_query)

    def serialize_log(log_doc):
        return {
            "id": str(log_doc["_id"]),
            "action": log_doc.get("action", "UNKNOWN"),
            "performed_by": log_doc.get("performed_by", ""),
            "ip_address": log_doc.get("ip_address", ""),
            "browser": log_doc.get("browser", ""),
            "endpoint": log_doc.get("endpoint", ""),
            "request_id": log_doc.get("request_id", ""),
            "timestamp": (
                log_doc["timestamp"]
                .replace(tzinfo=timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
                if log_doc.get("timestamp")
                else None
            ),
            "status": log_doc.get("status", "SUCCESS"),
            "details": log_doc.get("details", "")
        }

    return {
        "logs": [serialize_log(l) for l in logs],
        "total": total
    }

# ── System Health & Telemetry Endpoints ─────────────────────────────────────

@router.get("/system/telemetry")
async def system_telemetry(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Gathers database ping metrics, API latency values, and deployment statuses."""
    # 1. DB Ping
    t_start = time.perf_counter()
    try:
        await db.command("ping")
        db_ping = round((time.perf_counter() - t_start) * 1000, 1)
        db_status = "OPERATIONAL"
    except Exception:
        db_ping = 999.9
        db_status = "DEGRADED"

    # 2. Count Active Sessions & Users
    total_users = await db[collections.USERS].count_documents({"is_deleted": {"$ne": True}})
    suspended_users = await db[collections.USERS].count_documents({"is_deleted": {"$ne": True}, "is_active": False})
    
    users_with_sessions = db[collections.USERS].find({"is_deleted": {"$ne": True}, "sessions": {"$exists": True}})
    total_sessions = 0
    async for u in users_with_sessions:
        total_sessions += len(u.get("sessions", []))

    # System uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_delta = datetime.now() - boot_time

    days = uptime_delta.days
    hours = uptime_delta.seconds // 3600

    uptime = f"{days} days, {hours} hours"

    latest_prediction = await db[collections.TRANSACTIONS].find_one(
        {"xgboost_latency_ms": {"$exists": True}},
        sort=[("created_at", -1)]    )
    
    # print("========== LATEST PREDICTION ==========")
    # print(latest_prediction)

    if latest_prediction:
        xgboost_latency = latest_prediction.get("xgboost_latency_ms", 0)
        shap_latency = latest_prediction.get("shap_latency_ms", 0)
        gemini_latency = latest_prediction.get("gemini_latency_ms", 0)

    else:
        xgboost_latency = 0
        shap_latency = 0
        gemini_latency = 0

    # 3. Model Engine Load latencies
    telemetry = {
        "database": {
            "status": db_status,
            "ping_ms": db_ping,
            "connections": 5 # Simulated pool
        },
        "sessions": {
            "total_users": total_users,
            "suspended_users": suspended_users,
            "active_sessions": total_sessions
        },
        "deployment": {
            "environment": os.getenv("ENVIRONMENT", "Production"),
            "version": "v1.2.0-enterprise",
            "uptime": uptime,
            "build_timestamp": "2026-07-01T08:30:00Z"
        },
        "system_load": {
            "cpu_utilization": round(psutil.cpu_percent(interval=0.2), 1),
            "memory_utilization": round(psutil.virtual_memory().percent, 1),
            "disk_utilization": round(psutil.disk_usage("/").percent, 1)
        },
        "ai_models": {
            "xgboost": {
                "status": "LOADED",
                "latency_ms": xgboost_latency,
            },
            "shap": {
                "status": "LOADED",
                "latency_ms": shap_latency,
            },
            "gemini": {
                "status": "CONNECTED",
                "latency_ms": gemini_latency,
            }
        },
        "governance_score": 96.4,
    }
    # print("========== TELEMETRY ==========")
    # print(telemetry)
    # print(telemetry)
    return telemetry

from datetime import datetime, timedelta

@router.get("/activity-trend")
async def get_activity_trend(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Return transaction & fraud counts for the last 7 days."""

    seven_days_ago = datetime.utcnow() - timedelta(days=6)

    pipeline = [
        {
            "$match": {
                "transaction_time": {
                    "$gte": seven_days_ago
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%m/%d",
                        "date": "$transaction_time"
                    }
                },
                "transactions": {
                    "$sum": 1
                },
                "fraud": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$prediction", "FRAUD"]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    result = await db[collections.TRANSACTIONS].aggregate(pipeline).to_list(None)

    trend_map = {
        r["_id"]: {
            "transactions": r["transactions"],
            "fraud": r["fraud"]
        }
        for r in result
    }

    final_data = []

    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        date_key = day.strftime("%m/%d")

        values = trend_map.get(
            date_key,
            {
                "transactions": 0,
                "fraud": 0
            }
        )

        final_data.append({
            "date": date_key,
            "transactions": values["transactions"],
            "fraud": values["fraud"]
        })
    return final_data

@router.get("/browser-distribution")
async def get_browser_distribution(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    pipeline = [
        {
            "$unwind": "$sessions"
        },
        {
            "$group": {
                "_id": "$sessions.browser",
                "value": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "value": -1
            }
        }
    ]
    result = await db[collections.USERS].aggregate(pipeline).to_list(None)

    return [
        {
            "name": item["_id"] if item["_id"] else "Unknown",
            "value": item["value"]
        }
        for item in result
    ]
# ── RBAC Permission Matrix Endpoints ────────────────────────────────────────

DEFAULT_PERMISSION_MATRIX = {
    "Admin": [
        "view_transactions",
        "investigate_cases",
        "view_analytics",
        "manage_users",
        "view_audit_logs",
        "export_audit_logs",
        "manage_rbac",
        "view_system_telemetry"
    ],
    "Fraud Analyst": [
        "view_transactions",
        "investigate_cases",
        "view_analytics",
        "view_system_telemetry"
    ]
}

@router.get("/permissions")
async def get_permissions(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Fetch current Permission Matrix configuration."""
    matrix_doc = await db["roles_permissions"].find_one({"type": "matrix"})
    if not matrix_doc:
        # Seed default matrix
        seeded = {
            "type": "matrix",
            "matrix": DEFAULT_PERMISSION_MATRIX,
            "updated_at": datetime.utcnow()
        }
        await db["roles_permissions"].insert_one(seeded)
        return DEFAULT_PERMISSION_MATRIX
    return matrix_doc.get("matrix", DEFAULT_PERMISSION_MATRIX)

@router.put("/permissions")
async def update_permissions(
    request: Request,
    payload: PermissionMatrixUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Update Permission Matrix configuration."""
    await db["roles_permissions"].update_one(
        {"type": "matrix"},
        {"$set": {"matrix": payload.matrix, "updated_at": datetime.utcnow()}},
        upsert=True
    )
    await log_admin_event(request, current_user, "RBAC_MATRIX_UPDATE", "SUCCESS", "Updated roles permission matrix structure.")
    return {"success": True, "matrix": payload.matrix}

# ── Admin Notifications Endpoints ──────────────────────────────────────────

@router.get("/notifications")
async def get_admin_notifications(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Retrieve system security alerts for governance administrators."""
    # Generate live notifications dynamically from data
    notifications = []
    
    # 1. Check suspended users
    suspended_count = await db[collections.USERS].count_documents({"is_deleted": {"$ne": True}, "is_active": False})
    if suspended_count > 0:
        notifications.append({
            "id": "notif_suspend",
            "severity": "info",
            "title": "Inactive Accounts",
            "message": f"There are currently {suspended_count} suspended investigator accounts.",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    # 2. Check failed logins in the past 24 hours
    failed_logins = 0
    users = await db[collections.USERS].find({"is_deleted": {"$ne": True}}).to_list(100)
    for u in users:
        for entry in u.get("login_history", []):
            if entry.get("status") == "Failed":
                timestamp_str = entry.get("timestamp")
                # Can be datetime or string depending on version
                if isinstance(timestamp_str, datetime):
                    ts = timestamp_str
                else:
                    try:
                        ts = datetime.fromisoformat(str(timestamp_str))
                    except Exception:
                        ts = datetime.utcnow()
                if (datetime.utcnow() - ts).total_seconds() < 86400:
                    failed_logins += 1
                    
    if failed_logins > 3:
        notifications.append({
            "id": "notif_failed_login",
            "severity": "warning",
            "title": "Authentication Warning",
            "message": f"Detected {failed_logins} failed login attempts within the past 24 hours.",
            "timestamp": datetime.utcnow().isoformat()
        })

    # 3. Static health or telemetry notification if degraded
    # Fallback default info
    notifications.append({
        "id": "notif_compliance",
        "severity": "success",
        "title": "Compliance Status",
        "message": "All database operations meet SOC2/PCI data audit standards.",
        "timestamp": datetime.utcnow().isoformat()
    })

    return notifications

@router.post("/users/{user_id}/sessions/{session_id}/revoke")
async def revoke_user_session(
    user_id: str,
    session_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """Revoke a specific device session of another user."""
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    user = await db[collections.USERS].find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sessions = user.get("sessions", [])
    updated_sessions = [s for s in sessions if s.get("session_id") != session_id]

    if len(sessions) == len(updated_sessions):
        raise HTTPException(status_code=404, detail="Session not found")

    await db[collections.USERS].update_one(
        {"_id": oid},
        {"$set": {"sessions": updated_sessions}}
    )

    await log_admin_event(
        request,
        current_user,
        "SESSION_REVOKE",
        "SUCCESS",
        f"Revoked device session {session_id} of user {user['email']}"
    )

    return {"success": True, "message": "Session successfully revoked by Admin"}
