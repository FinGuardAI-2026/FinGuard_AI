from datetime import datetime
from typing import Optional
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

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
