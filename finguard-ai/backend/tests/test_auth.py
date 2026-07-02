import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, HTTPException

# ── Crypto utilities ────────────────────────────────────────────────────────
from app.core.security.crypto import (
    hash_password,
    verify_password,
    create_jwt_token,
    decode_jwt_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from datetime import timedelta


# ── 1. Password Hashing Tests ────────────────────────────────────────────────
class TestCrypto:
    def test_hash_and_verify_password(self):
        """Correct password should verify against its hash."""
        pw = "StrongP@ss1"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True

    def test_wrong_password_fails_verification(self):
        """Incorrect password must not verify successfully."""
        hashed = hash_password("StrongP@ss1")
        assert verify_password("WrongP@ss99", hashed) is False

    def test_create_and_decode_access_token(self):
        """Encoded JWT payload should round-trip decode with the same claims."""
        claims = {"sub": "user_id_abc", "email": "jane@finguard.ai", "role": "Fraud Analyst"}
        token = create_jwt_token(claims, timedelta(minutes=30))
        decoded = decode_jwt_token(token)
        assert decoded["sub"] == "user_id_abc"
        assert decoded["email"] == "jane@finguard.ai"

    def test_decode_invalid_token_raises(self):
        """Tampering with a token should raise ValueError."""
        token = create_jwt_token({"sub": "x"}, timedelta(minutes=1))
        tampered = token + "INVALID"
        with pytest.raises(ValueError):
            decode_jwt_token(tampered)


# ── 2. Schema Validation Tests ───────────────────────────────────────────────
class TestSchemas:
    def test_register_request_passwords_mismatch(self):
        """RegisterRequest should reject mismatched confirm_password."""
        from pydantic import ValidationError
        from app.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError):
            RegisterRequest(
                full_name="Jane Doe",
                email="jane@finguard.ai",
                password="StrongP@ss1",
                confirm_password="DifferentPass1!",
            )

    def test_register_request_weak_password(self):
        """RegisterRequest should reject passwords missing special characters."""
        from pydantic import ValidationError
        from app.schemas.auth import RegisterRequest

        with pytest.raises(ValidationError):
            RegisterRequest(
                full_name="Jane Doe",
                email="jane@finguard.ai",
                password="onlylowercase1",
                confirm_password="onlylowercase1",
            )

    def test_register_request_valid(self):
        """RegisterRequest should accept a fully valid payload."""
        from app.schemas.auth import RegisterRequest

        req = RegisterRequest(
            full_name="Jane Doe",
            email="jane@finguard.ai",
            password="StrongP@ss1",
            confirm_password="StrongP@ss1",
        )
        assert req.email == "jane@finguard.ai"


# ── 3. AuthService Unit Tests ────────────────────────────────────────────────
@pytest.mark.asyncio
class TestAuthService:
    def _make_user_doc(self):
        return {
            "_id": "507f1f77bcf86cd799439011",
            "full_name": "Jane Doe",
            "email": "jane@finguard.ai",
            "hashed_password": hash_password("StrongP@ss1"),
            "role": "Fraud Analyst",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
        }

    async def test_register_duplicate_email_raises(self):
        """AuthService.register_user should raise ValueError on existing email."""
        from app.services.auth import AuthService
        from app.schemas.auth import RegisterRequest

        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = self._make_user_doc()

        service = AuthService(mock_repo)
        req = RegisterRequest(
            full_name="Jane Doe",
            email="jane@finguard.ai",
            password="StrongP@ss1",
            confirm_password="StrongP@ss1",
        )
        with pytest.raises(ValueError, match="already registered"):
            await service.register_user(req)

    async def test_register_new_user_success(self):
        """AuthService.register_user should insert and return the new user document."""
        from app.services.auth import AuthService
        from app.schemas.auth import RegisterRequest

        new_user = self._make_user_doc()
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None            # No existing user
        mock_repo.insert_one.return_value = new_user["_id"]
        mock_repo.find_one.return_value = new_user

        service = AuthService(mock_repo)
        req = RegisterRequest(
            full_name="Jane Doe",
            email="jane@finguard.ai",
            password="StrongP@ss1",
            confirm_password="StrongP@ss1",
        )
        result = await service.register_user(req)
        assert result["email"] == "jane@finguard.ai"

    async def test_login_invalid_password_raises(self):
        """AuthService.login_user should raise ValueError on wrong password."""
        from app.services.auth import AuthService
        from app.schemas.auth import LoginRequest

        user = self._make_user_doc()
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = user

        service = AuthService(mock_repo)
        req = LoginRequest(email="jane@finguard.ai", password="WrongP@ss1!")
        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login_user(req)

    async def test_login_success_returns_tokens(self):
        """AuthService.login_user should return user dict plus access and refresh tokens."""
        from app.services.auth import AuthService
        from app.schemas.auth import LoginRequest

        user = self._make_user_doc()
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = user
        mock_repo.update_one.return_value = True

        service = AuthService(mock_repo)
        req = LoginRequest(email="jane@finguard.ai", password="StrongP@ss1")
        result_user, access_token, refresh_token = await service.login_user(req)

        assert result_user["email"] == "jane@finguard.ai"
        assert isinstance(access_token, str) and len(access_token) > 0
        assert isinstance(refresh_token, str) and len(refresh_token) > 0

    async def test_refresh_token_wrong_type_raises(self):
        """AuthService.refresh_access_token should reject access tokens used as refresh tokens."""
        from app.services.auth import AuthService

        # Create a plain access token (no "type": "refresh" claim)
        access_token = create_jwt_token(
            {"sub": "uid", "email": "x@x.com", "role": "Fraud Analyst"},
            timedelta(minutes=30),
        )
        mock_repo = AsyncMock()
        service = AuthService(mock_repo)

        with pytest.raises(ValueError, match="Invalid token type"):
            await service.refresh_access_token(access_token)
