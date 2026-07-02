from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
)
from app.services.auth import AuthService
from app.dependencies.auth import get_auth_service, get_current_user

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
) -> UserResponse:
    """Registers a new FinGuard AI user account."""
    try:
        user = await auth_service.register_user(request)
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
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticates the user and returns signed JWT access/refresh tokens."""
    try:
        user, access_token, refresh_token = await auth_service.login_user(request)
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    """Acknowledges logout. Clients must discard stored tokens upon receipt."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Logged out successfully. Please discard your access and refresh tokens.",
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
