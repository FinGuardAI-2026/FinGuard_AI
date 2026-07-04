from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

# Crypt context configuration for password salting and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def hash_password(password: str) -> str:
    """Computes a cryptographically secure hash of the password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    print("CREATE SECRET:", settings.JWT_SECRET)
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)

    # print("NOW UTC :", datetime.utcnow())
    # print("EXPIRE  :", expire)

    to_encode["exp"] = expire

    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=ALGORITHM,
    )

    return token

# def decode_jwt_token(token: str) -> Dict[str, Any]:
#     """Decodes and validates a JWT token, raising JWTError on validation failures."""
#     try:
#         payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
#         return payload
#     except JWTError as e:
#         raise ValueError("Invalid or expired token signature") from e

def decode_jwt_token(token: str):
    print("DECODE SECRET:", settings.JWT_SECRET)
    # print("=" * 60)

    # print("TOKEN =", token)

    # payload = jwt.get_unverified_claims(token)
    # print("UNVERIFIED =", payload)

    verified = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[ALGORITHM]
    )

    # print("VERIFIED =", verified)
    # print("=" * 60)

    return verified