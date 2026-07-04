from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from app.repositories.user import UserRepository
from app.core.security.crypto import hash_password, verify_password, create_jwt_token, decode_jwt_token
from app.schemas.auth import RegisterRequest, LoginRequest
from app.models.user import UserDB
from app.core.config import settings

class AuthService:
    """Service layer orchestrating authentication, token generation, and profile creations."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register_user(self, request: RegisterRequest) -> Dict[str, Any]:
        """Validates duplicate entries and registers a new cryptographically hashed user profile."""
        email_clean = request.email.strip().lower()
        existing_user = await self.user_repo.get_by_email(email_clean)
        if existing_user:
            raise ValueError("Email already registered")

        # Select role constraints: only "Admin" or "Fraud Analyst" allowed
        role = request.role if request.role in ["Admin", "Fraud Analyst"] else "Fraud Analyst"

        user_in = UserDB(
            full_name=request.full_name,
            email=email_clean,
            hashed_password=hash_password(request.password),
            role=role,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        user_dict = user_in.model_dump(by_alias=True)
        # BSON conversions handled inside BaseRepository. Let's delete the unset _id field so MongoDB auto-creates it
        if "id" in user_dict and user_dict["id"] is None:
            del user_dict["id"]
        if "_id" in user_dict and user_dict["_id"] is None:
            del user_dict["_id"]

        user_id = await self.user_repo.insert_one(user_dict)
        
        # Query generated document to return full object details
        created_user = await self.user_repo.find_one({"_id": user_id})
        if not created_user:
            raise RuntimeError("Database error creating user profile")
            
        return created_user

    async def login_user(self, request: LoginRequest) -> Tuple[Dict[str, Any], str, str]:
        """Validates credentials, updates logins, and generates session JWT access/refresh tokens."""
        email_clean = request.email.strip().lower()
        user = await self.user_repo.get_by_email(email_clean)
        print("EMAIL:", email_clean)
        print("USER FOUND:", user is not None)

        if user:
            print("HASH:", user.get("hashed_password"))
        try:
            result = verify_password(request.password, user.get("hashed_password", ""))
            print("VERIFY RESULT:", result)
        except Exception as e:
            print("VERIFY ERROR:", repr(e))
            raise
        
        if not user or not user.get("is_active"):
            raise ValueError("Invalid email or password")
            
        if not verify_password(request.password, user.get("hashed_password", "")):
            raise ValueError("Invalid email or password")

        # Update last login time
        now = datetime.utcnow()
        await self.user_repo.update_one(
            {"_id": user["_id"]},
            {"last_login": now, "updated_at": now}
        )
        user["last_login"] = now

        # print("LOGIN SECRET:", settings.JWT_SECRET)

        # Generate tokens
        access_token, refresh_token = self.generate_auth_tokens(user)
        return user, access_token, refresh_token

    def generate_auth_tokens(self, user: Dict[str, Any]) -> Tuple[str, str]:
        """Creates short-term access tokens and long-term session refresh tokens."""
        claims = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"]
        }
        access_token = create_jwt_token(claims, expires_delta=timedelta(minutes=30))
        # Add refresh claim mapping
        claims_refresh = claims.copy()
        claims_refresh["type"] = "refresh"
        refresh_token = create_jwt_token(claims_refresh, expires_delta=timedelta(days=7))
        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> Tuple[Dict[str, Any], str, str]:
        """Validates refresh tokens, pulls user data, and issues fresh token credentials."""
        try:
            payload = decode_jwt_token(refresh_token)
        except ValueError as e:
            raise ValueError("Invalid token signature") from e

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token claims")

        user = await self.user_repo.find_one({"_id": user_id})
        if not user or not user.get("is_active"):
            raise ValueError("User account is inactive or missing")

        # Issue fresh pairs
        access_token, new_refresh_token = self.generate_auth_tokens(user)
        return user, access_token, new_refresh_token
