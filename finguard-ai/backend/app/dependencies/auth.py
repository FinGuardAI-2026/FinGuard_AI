from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any

from app.dependencies.database import get_mongo_db
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.core.security.crypto import decode_jwt_token

# Set oauth flow token URL matching login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_mongo_db)) -> UserRepository:
    """FastAPI Dependency providing the UserRepository instantiated with active db session."""
    return UserRepository(db)

async def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    """FastAPI Dependency providing the AuthService instantiated with User repository."""
    return AuthService(user_repo)

# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     user_repo: UserRepository = Depends(get_user_repository)
# ) -> Dict[str, Any]:

#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     print("=" * 60)
#     print("TOKEN:", token)

#     try:
#         payload = decode_jwt_token(token)
#         print("PAYLOAD:", payload)

#         user_id = payload.get("sub")
#         print("USER_ID:", user_id)

#         if user_id is None:
#             print("SUB IS NONE")
#             raise credentials_exception

#     except Exception as e:
#         print("JWT ERROR:", repr(e))
#         raise credentials_exception

#     user = await user_repo.find_one({"_id": user_id})
#     print("USER:", user)

#     if user is None:
#         print("USER NOT FOUND")
#         raise credentials_exception

#     if not user.get("is_active"):
#         print("USER INACTIVE")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Inactive user profile"
#         )

#     print("AUTH SUCCESS")
#     return user

async def get_current_user(
    user_repo: UserRepository = Depends(get_user_repository)
) -> Dict[str, Any]:

    # Testing only
    user = await user_repo.get_by_email("satyam.test@finguard.ai")

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Test user not found"
        )

    return user

class RoleChecker:
    """RBAC dynamic dependency class verifying that the user matches required roles."""

    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Insufficient privileges"
            )
        return current_user
