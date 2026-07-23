from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    ProfileUpdateRequest,
    PasswordChangeRequest,
    RoleChangeRequest,
)
from app.services.auth import AuthService
from app.dependencies.auth import get_auth_service, get_current_user, RoleChecker, oauth2_scheme
from app.dependencies.notification import get_notification_service
from app.services.notification import NotificationService
from app.core.security.crypto import decode_jwt_token
from app.db.connection import db_manager
from app.db.collections import collections

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _serialize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Converts raw MongoDB user document fields to UserResponse-compatible format."""
    return {
        "_id": str(user.get("_id", "")),
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


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    summary="Register a new user",
    description="Creates a new investigator or admin account. Email must be unique and password must be strong.",
    responses={
        201: {"description": "User registered successfully"},
        409: {"description": "Email already in use"},
        422: {"description": "Validation error on input fields"},
    },
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
    notif_svc: NotificationService = Depends(get_notification_service),
) -> UserResponse:
    """Registers a new FinGuard AI user account."""
    try:
        user = await auth_service.register_user(request)
        import asyncio
        asyncio.create_task(
            notif_svc.notify_user_registered(
                user_id=str(user["_id"]),
                full_name=user["full_name"],
                email=user["email"],
            )
        )
    except ValueError as e:
        # Duplicate email or rule violation
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return UserResponse(**_serialize_user(user))


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    summary="Authenticate and receive JWT tokens",
    description="Validates email and password, then issues an access token and a refresh token.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    request_payload: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    notif_svc: NotificationService = Depends(get_notification_service),
) -> TokenResponse:
    """Authenticates the user and returns signed JWT access/refresh tokens with active session registration."""
    try:
        ip = request.client.host if request.client else "127.0.0.1"
        user_agent = request.headers.get("user-agent", "Unknown Device")
        user, access_token, refresh_token = await auth_service.login_user(
            request_payload, ip_address=ip, user_agent=user_agent
        )
        import asyncio
        asyncio.create_task(
            notif_svc.notify_auth_login(
                user_id=str(user["_id"]),
                email=user["email"],
                ip_address=ip,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(**_serialize_user(user)),
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Issues a fresh access token by validating a valid refresh token.",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Refresh token invalid or expired"},
    },
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Validates the provided refresh token and generates a fresh token pair."""
    try:
        user, access_token, new_refresh_token = await auth_service.refresh_access_token(
            request.refresh_token
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=UserResponse(**_serialize_user(user)),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout current session",
    description="Invalidates the current session. Stateless JWT logout is acknowledged at the client layer.",
    responses={
        200: {"description": "Logged out successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    notif_svc: NotificationService = Depends(get_notification_service),
) -> JSONResponse:
    """Acknowledges logout and clears the user's current session identifier in database."""
    # Try parsing session ID from token and clean it up
    try:
        payload = decode_jwt_token(token)
        sid = payload.get("sid")
        if sid:
            sessions = [s for s in current_user.get("sessions", []) if s.get("session_id") != sid]
            await auth_service.user_repo.update_one(
                {"_id": str(current_user["_id"])},
                {"$set": {"sessions": sessions}}
            )
    except Exception:
        pass

    import asyncio
    asyncio.create_task(notif_svc.notify_auth_logout(str(current_user["_id"])))
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Logged out successfully. Session invalidated.",
        },
    )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="Get current authenticated user",
    description="Returns the full profile of the currently authenticated investigator or admin.",
    responses={
        200: {"description": "User profile returned"},
        401: {"description": "Token missing or invalid"},
        403: {"description": "Inactive account"},
    },
)
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Returns the authenticated user's profile using the JWT bearer token."""
    return UserResponse(**_serialize_user(current_user))


@router.patch(
    "/profile",
    response_model=UserResponse,
    summary="Update profile details",
)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    notif_svc: NotificationService = Depends(get_notification_service),
) -> UserResponse:
    user_id = str(current_user["_id"])
    updates = {}
    changed_fields = []
    
    if request.full_name is not None:
        updates["full_name"] = request.full_name
        changed_fields.append("full_name")
    if request.email is not None:
        updates["email"] = request.email.strip().lower()
        changed_fields.append("email")
    if request.avatar_color is not None:
        updates["avatar_color"] = request.avatar_color
        changed_fields.append("avatar_color")
    if request.avatar_url is not None:
        updates["avatar_url"] = request.avatar_url
        changed_fields.append("avatar_url")
    if request.preferences is not None:
        # Merge preferences
        existing_prefs = current_user.get("preferences") or {}
        merged_prefs = {**existing_prefs, **request.preferences}
        updates["preferences"] = merged_prefs
        changed_fields.append("preferences")
        
    if not updates:
        return UserResponse(**_serialize_user(current_user))
        
    updates["updated_at"] = datetime.utcnow()
    
    success = await auth_service.user_repo.update_one({"_id": user_id}, {"$set": updates})
    if not success:
        raise HTTPException(status_code=500, detail="Database update failed")
        
    updated_user = await auth_service.user_repo.find_one({"_id": user_id})
    
    import asyncio
    asyncio.create_task(
        notif_svc.notify_profile_update(user_id=user_id, changed_fields=changed_fields)
    )
    
    return UserResponse(**_serialize_user(updated_user))


@router.post(
    "/change-password",
    summary="Change user password",
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    notif_svc: NotificationService = Depends(get_notification_service),
) -> JSONResponse:
    user_id = str(current_user["_id"])
    from app.core.security.crypto import verify_password, hash_password
    
    if not verify_password(request.old_password, current_user.get("hashed_password", "")):
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    new_hashed = hash_password(request.new_password)
    success = await auth_service.user_repo.update_one(
        {"_id": user_id},
        {"$set": {"hashed_password": new_hashed, "updated_at": datetime.utcnow()}}
    )
    if not success:
        raise HTTPException(status_code=500, detail="Database update failed")
        
    import asyncio
    asyncio.create_task(
        notif_svc.notify_password_change(user_id=user_id, email=current_user["email"])
    )
    
    return JSONResponse(content={"success": True, "message": "Password changed successfully"})


@router.post(
    "/change-role",
    summary="Change user role (Admin only)",
)
async def change_role(
    request: RoleChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    notif_svc: NotificationService = Depends(get_notification_service),
) -> JSONResponse:
    # Verify the calling user is Admin (RBAC check inline to handle exceptions cleanly)
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Access denied: Insufficient privileges")

    target_user = await auth_service.user_repo.find_one({"_id": request.user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    old_role = target_user.get("role", "Fraud Analyst")
    if old_role == request.new_role:
        return JSONResponse(content={"success": True, "message": "Role is already set to target role"})
        
    success = await auth_service.user_repo.update_one(
        {"_id": request.user_id},
        {"$set": {"role": request.new_role, "updated_at": datetime.utcnow()}}
    )
    if not success:
        raise HTTPException(status_code=500, detail="Database update failed")
        
    import asyncio
    asyncio.create_task(
        notif_svc.notify_role_change(
            user_id=request.user_id,
            old_role=old_role,
            new_role=request.new_role,
            changed_by=current_user.get("full_name", "Admin")
        )
    )
    
    return JSONResponse(content={"success": True, "message": f"User role updated to {request.new_role}"})


# ── Enterprise Account Center & Session Management Endpoints ──────────────────

@router.get(
    "/profile/center",
    summary="Fetch aggregated account center data",
)
async def get_profile_center(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Dict[str, Any]:
    user_id = str(current_user["_id"])
    db = db_manager.get_db()
    
    # 1. Compute Security Score
    # Baseline 40% (has account + active).
    # +20% if email is registered under enterprise domain finguard.ai
    # +20% if password changed recently (or we check updated_at)
    # +20% if no failed logins or session count is low (<= 2)
    security_score = 60
    if len(current_user.get("sessions", [])) <= 2:
        security_score += 20
    if "@finguard.ai" in current_user.get("email", "").lower():
        security_score += 20

    # 2. Compute Profile Completion
    # baseline 50% for standard fields (name, email)
    # +25% if avatar color or URL set
    # +25% if preferences configured
    completion = 50
    if current_user.get("avatar_color") or current_user.get("avatar_url"):
        completion += 25
    if current_user.get("preferences"):
        completion += 25

    # 3. Aggregate Statistics from Transactions & Reports
    txn_collection = db[collections.TRANSACTIONS]
    
    # Analysts see only their own, Admins see all for statistics
    is_admin = current_user.get("role") == "Admin"
    query_filter = {} if is_admin else {"user_id": user_id}
    
    total_txns = await txn_collection.count_documents(query_filter)
    
    # Avg Risk Score
    pipeline = [
        {"$match": {**query_filter, "risk_score": {"$exists": True}}},
        {"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}
    ]
    avg_risk_cursor = txn_collection.aggregate(pipeline)
    avg_risk_list = await avg_risk_cursor.to_list(length=1)
    avg_risk_score = round(avg_risk_list[0]["avg_risk"], 1) if avg_risk_list else 0.0

    # Total Reports
    total_reports = await txn_collection.count_documents({
        **query_filter,
        "llm_report": {"$exists": True, "$ne": None}
    })

    # Total alerts handled (notifications count)
    total_alerts = await db[collections.NOTIFICATIONS].count_documents({"user_id": user_id})

    # 4. Fetch Recent Reports
    reports_cursor = txn_collection.find({
        **query_filter,
        "llm_report": {"$exists": True, "$ne": None}
    }).sort("created_at", -1).limit(5)
    
    def serialize_report_txn(doc):
        out = dict(doc)
        if "_id" in out:
            out["id"] = str(out.pop("_id"))
        return out
        
    recent_reports = [serialize_report_txn(d) for d in await reports_cursor.to_list(length=5)]

    # 5. Fetch Recent Notifications
    notif_cursor = db[collections.NOTIFICATIONS].find({
        "user_id": user_id
    }).sort("created_at", -1).limit(5)
    
    def serialize_notif(doc):
        out = dict(doc)
        if "_id" in out:
            out["id"] = str(out.pop("_id"))
        return out
        
    recent_notifs = [serialize_notif(d) for d in await notif_cursor.to_list(length=5)]

    return {
        "security_score": security_score,
        "profile_completion": completion,
        "statistics": {
            "total_transactions_investigated": total_txns,
            "total_reports_generated": total_reports,
            "avg_risk_score": avg_risk_score,
            "total_alerts_handled": total_alerts,
        },
        "recent_reports": recent_reports,
        "recent_notifications": recent_notifs,
    }


@router.post(
    "/sessions/{session_id}/revoke",
    summary="Revoke a specific device session",
)
async def revoke_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> JSONResponse:
    sessions = current_user.get("sessions", [])
    updated_sessions = [s for s in sessions if s.get("session_id") != session_id]
    
    if len(sessions) == len(updated_sessions):
        raise HTTPException(status_code=404, detail="Session not found")
        
    success = await auth_service.user_repo.update_one(
        {"_id": str(current_user["_id"])},
        {"$set": {"sessions": updated_sessions}}
    )
    if not success:
        raise HTTPException(status_code=500, detail="Database revocation update failed")
        
    return JSONResponse(content={"success": True, "message": "Session successfully revoked"})


@router.post(
    "/sessions/revoke-all",
    summary="Revoke all other device sessions",
)
async def revoke_all_sessions(
    token: str = Depends(oauth2_scheme),
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> JSONResponse:
    current_sid = None
    try:
        payload = decode_jwt_token(token)
        current_sid = payload.get("sid")
    except Exception:
        pass
        
    sessions = current_user.get("sessions", [])
    # Keep only the current session, discard the others
    updated_sessions = [s for s in sessions if s.get("session_id") == current_sid] if current_sid else []
    
    await auth_service.user_repo.update_one(
        {"_id": str(current_user["_id"])},
        {
            "$set": {
                "sessions": updated_sessions,
                "token_valid_after": datetime.utcnow()
            }
        }
    )
    return JSONResponse(content={"success": True, "message": "All other sessions successfully revoked"})

