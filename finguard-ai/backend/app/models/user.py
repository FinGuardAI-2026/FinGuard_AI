from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, EmailStr, Field

class UserDB(BaseModel):
    """Internal user model corresponding to a document in MongoDB."""
    id: Optional[str] = Field(default=None, alias="_id")
    full_name: str
    email: EmailStr
    hashed_password: str
    role: str = "Fraud Analyst"  # "Admin" or "Fraud Analyst"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    avatar_color: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=lambda: {
        "email_notifications": True,
        "system_alerts": True,
        "theme": "dark",
        "language": "en"
    })
    sessions: List[Dict[str, Any]] = Field(default_factory=list)
    login_history: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
