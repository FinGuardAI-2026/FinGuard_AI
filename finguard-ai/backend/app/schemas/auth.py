import re
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class RegisterRequest(BaseModel):
    """Payload schema validating user registrations."""
    full_name: str = Field(..., min_length=2, max_length=100, example="Jane Doe")
    email: EmailStr = Field(..., example="jane.doe@finguard.ai")
    password: str = Field(..., min_length=8, max_length=64, example="StrongP@ss1")
    confirm_password: str = Field(..., example="StrongP@ss1")
    role: Optional[str] = Field(default="Fraud Analyst", example="Fraud Analyst")

    @model_validator(mode="after")
    def verify_passwords_match(self) -> 'RegisterRequest':
        """Asserts that password entries are identical."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    @model_validator(mode="after")
    def verify_strong_password(self) -> 'RegisterRequest':
        """Enforces complexity requirements for user passwords."""
        pw = self.password
        if not re.search(r"[A-Z]", pw):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", pw):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", pw):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pw):
            raise ValueError("Password must contain at least one special character")
        return self

class LoginRequest(BaseModel):
    """Payload schema validating authentication checks."""
    email: EmailStr = Field(..., example="jane.doe@finguard.ai")
    password: str = Field(..., example="StrongP@ss1")

class UserResponse(BaseModel):
    """Return model representing active user profile data."""
    id: str = Field(..., alias="_id")
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    avatar_color: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    sessions: Optional[List[Dict[str, Any]]] = None
    login_history: Optional[List[Dict[str, Any]]] = None

    class Config:
        populate_by_name = True

class TokenResponse(BaseModel):
    """Return schema packing access tokens and expiration lifespans."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    """Payload verification requesting refreshed access tokens."""
    refresh_token: str

class ErrorDetail(BaseModel):
    """Indicates field validation error issues."""
    field: str
    issue: str
    type: str

class ErrorBody(BaseModel):
    """Indicates internal system error information structures."""
    code: str
    message: str
    details: List[ErrorDetail] = []
    timestamp: str

class ErrorResponse(BaseModel):
    """Generic system wrapper response indicating operation issues."""
    success: bool = False
    error: ErrorBody


class ProfileUpdateRequest(BaseModel):
    """Payload schema validating profile updates."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    avatar_color: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class PasswordChangeRequest(BaseModel):
    """Payload schema validating password changes."""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=64)

    @model_validator(mode="after")
    def verify_strong_password(self) -> 'PasswordChangeRequest':
        """Enforces complexity requirements for user passwords."""
        pw = self.new_password
        if not re.search(r"[A-Z]", pw):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", pw):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", pw):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pw):
            raise ValueError("Password must contain at least one special character")
        return self


class RoleChangeRequest(BaseModel):
    """Payload schema validating admin role modifications."""
    user_id: str
    new_role: str = Field(..., description="Admin or Fraud Analyst")
