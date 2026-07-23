from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
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

    async def login_user(
        self,
        request: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str, str]:
        """Validates credentials, updates logins, and generates session JWT access/refresh tokens."""
        import uuid
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
            # Log failed login attempt in login history
            ip = ip_address or "Unknown"
            ua = user_agent or "Unknown"
            failed_entry = {
                "id": uuid.uuid4().hex,
                "timestamp": datetime.utcnow(),
                "ip_address": ip,
                "device": ua,
                "location": "Local Network" if ip in ("127.0.0.1", "localhost", "::1") else "Remote Location",
                "status": "Failed"
            }
            # Add to history
            history = user.get("login_history", [])
            history.insert(0, failed_entry)
            await self.user_repo.update_one(
                {"_id": user["_id"]},
                {"$set": {"login_history": history[:20]}}
            )
            raise ValueError("Invalid email or password")

        # Create active session and log successful login
        session_id = uuid.uuid4().hex
        ip = ip_address or "127.0.0.1"
        ua = user_agent or "Unknown Browser"
        
        # Simple UA parsing
        ua_low = ua.lower()
        if "windows" in ua_low:
            os_name = "Windows"
        elif "macintosh" in ua_low or "mac os" in ua_low:
            os_name = "macOS"
        elif "iphone" in ua_low or "ipad" in ua_low:
            os_name = "iOS"
        elif "android" in ua_low:
            os_name = "Android"
        elif "linux" in ua_low:
            os_name = "Linux"
        else:
            os_name = "Unknown OS"

        if "chrome" in ua_low and "chrome" not in ua_low.split("chrome")[-1]:
            browser_name = "Chrome"
        elif "firefox" in ua_low:
            browser_name = "Firefox"
        elif "safari" in ua_low and "chrome" not in ua_low:
            browser_name = "Safari"
        elif "edge" in ua_low or "edg" in ua_low:
            browser_name = "Edge"
        else:
            browser_name = "Browser"

        if any(m in ua_low for m in ["mobi", "iphone", "android"]):
            device_type = "Mobile"
        elif "ipad" in ua_low:
            device_type = "Tablet"
        else:
            device_type = "Desktop"

        location = "Local Network" if ip in ("127.0.0.1", "localhost", "::1") else "Remote Location"

        new_session = {
            "session_id": session_id,
            "ip_address": ip,
            "user_agent": ua,
            "device_type": device_type,
            "browser": browser_name,
            "os": os_name,
            "location": location,
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow(),
        }

        success_entry = {
            "id": uuid.uuid4().hex,
            "timestamp": datetime.utcnow(),
            "ip_address": ip,
            "device": f"{browser_name} on {os_name}",
            "location": location,
            "status": "Success",
        }

        sessions = user.get("sessions", [])
        sessions.append(new_session)
        
        login_history = user.get("login_history", [])
        login_history.insert(0, success_entry)

        # Update user doc
        now = datetime.utcnow()
        await self.user_repo.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "last_login": now,
                    "updated_at": now,
                    "sessions": sessions,
                    "login_history": login_history[:20]
                }
            }
        )
        user["last_login"] = now
        user["sessions"] = sessions
        user["login_history"] = login_history[:20]

        # Generate tokens containing session ID (sid)
        access_token, refresh_token = self.generate_auth_tokens(user, session_id=session_id)
        return user, access_token, refresh_token

    def generate_auth_tokens(self, user: Dict[str, Any], session_id: Optional[str] = None) -> Tuple[str, str]:
        """Creates short-term access tokens and long-term session refresh tokens."""
        claims = {
            "sub": str(user["_id"]),
            "email": user["email"],
            "role": user["role"]
        }
        if session_id:
            claims["sid"] = session_id

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
        if not user or not user.get("is_active") or user.get("is_deleted"):
            raise ValueError("User account is inactive or missing")

        # Validate session ID if present in refresh token claims
        sid = payload.get("sid")
        if sid:
            active_sessions = user.get("sessions", [])
            session_exists = any(s.get("session_id") == sid for s in active_sessions)
            if not session_exists:
                raise ValueError("Session has been revoked or expired")

        # Issue fresh pairs preserving the session ID
        access_token, new_refresh_token = self.generate_auth_tokens(user, session_id=sid)
        return user, access_token, new_refresh_token
