import re
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional, Dict

class AdminUserCreateRequest(BaseModel):
    """Payload schema validating administrative user creation requests."""
    full_name: str = Field(..., min_length=2, max_length=100, example="Jane Doe")
    email: EmailStr = Field(..., example="jane.doe@finguard.ai")
    password: str = Field(..., min_length=8, max_length=64, example="StrongP@ss1")
    role: str = Field(default="Fraud Analyst", example="Fraud Analyst")

    @model_validator(mode="after")
    def verify_strong_password(self) -> 'AdminUserCreateRequest':
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

class AdminUserEditRequest(BaseModel):
    """Payload schema for editing user profiles."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class AdminPasswordResetRequest(BaseModel):
    """Payload schema validating password overwrite requests from Admins."""
    password: str = Field(..., min_length=8, max_length=64)

    @model_validator(mode="after")
    def verify_strong_password(self) -> 'AdminPasswordResetRequest':
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

class BulkStatusUpdateRequest(BaseModel):
    """Payload schema for bulk toggling user active status."""
    user_ids: List[str]
    is_active: bool

class BulkDeleteRequest(BaseModel):
    """Payload schema for bulk soft-deleting users."""
    user_ids: List[str]

class PermissionMatrixUpdateRequest(BaseModel):
    """Payload schema validating updates to the RBAC Permission Matrix."""
    matrix: Dict[str, List[str]]
