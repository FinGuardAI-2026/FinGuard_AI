import math
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionFilterParams,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdateRequest,
)
from app.models.transaction import TransactionDB


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures all datetime values are kept as datetime objects for Pydantic."""
    return doc


class TransactionService:
    """
    Business logic layer for the transaction domain.

    Responsibilities:
    - Enforce business rules before touching the repository.
    - Translate raw MongoDB dicts into Pydantic response objects.
    - Compute pagination metadata.

    Does NOT know about HTTP or FastAPI — pure Python callable logic.
    """

    def __init__(self, repo: TransactionRepository) -> None:
        self.repo = repo

    # ── Create ────────────────────────────────────────────────────────────

    async def create_transaction(
        self,
        payload: TransactionCreateRequest,
        user_id: str,
    ) -> TransactionResponse:
        """Persists a new transaction document and returns the created record."""
        transaction_in = TransactionDB(
            user_id=user_id,
            amount=payload.amount,
            currency=payload.currency.upper(),
            merchant_name=payload.merchant_name,
            merchant_category=payload.merchant_category,
            payment_method=payload.payment_method.value,
            transaction_type=payload.transaction_type.value,
            country=payload.country.upper(),
            city=payload.city,
            latitude=payload.latitude,
            longitude=payload.longitude,
            ip_address=payload.ip_address,
            device_id=payload.device_id,
            browser=payload.browser,
            operating_system=payload.operating_system,
            transaction_time=payload.transaction_time or datetime.utcnow(),
            status="PENDING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        doc = transaction_in.model_dump(by_alias=True, exclude_none=True)
        # Remove None _id so MongoDB auto-generates ObjectId
        doc.pop("_id", None)
        doc.pop("id", None)

        inserted_id = await self.repo.insert_one(doc)
        created = await self.repo.find_one({"_id": inserted_id})
        if not created:
            raise RuntimeError("Database error: failed to retrieve created transaction.")
        return TransactionResponse(**created)

    # ── Read One ──────────────────────────────────────────────────────────

    async def get_transaction(self, transaction_db_id: str) -> TransactionResponse:
        """Retrieves a single transaction by its MongoDB _id."""
        doc = await self.repo.find_one({"_id": transaction_db_id})
        if not doc:
            raise ValueError(f"Transaction '{transaction_db_id}' not found.")
        return TransactionResponse(**doc)

    # ── List with Filters ─────────────────────────────────────────────────

    async def list_transactions(
        self,
        filters: TransactionFilterParams,
        requesting_user_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> TransactionListResponse:
        """
        Returns a paginated list of transactions.
        Admins see all records; Fraud Analysts see only their own.
        """
        user_id_filter = None if is_admin else requesting_user_id

        docs, total = await self.repo.find_filtered(
            user_id=user_id_filter,
            transaction_id=filters.transaction_id,
            merchant=filters.merchant,
            country=filters.country,
            payment_method=filters.payment_method.value if filters.payment_method else None,
            min_amount=filters.min_amount,
            max_amount=filters.max_amount,
            date_from=filters.date_from,
            date_to=filters.date_to,
            merchant_category=filters.merchant_category,
            status=filters.status.value if filters.status else None,
            sort_by=filters.sort_by.value,
            sort_order=filters.sort_order.value,
            page=filters.page,
            page_size=filters.page_size,
        )

        total_pages = math.ceil(total / filters.page_size) if total > 0 else 0

        return TransactionListResponse(
            transactions=[TransactionResponse(**d) for d in docs],
            total_records=total,
            total_pages=total_pages,
            page=filters.page,
            page_size=filters.page_size,
        )

    # ── Update ────────────────────────────────────────────────────────────

    async def update_transaction(
        self,
        transaction_db_id: str,
        payload: TransactionUpdateRequest,
    ) -> TransactionResponse:
        """Applies partial updates to a transaction and returns the refreshed document."""
        existing = await self.repo.find_one({"_id": transaction_db_id})
        if not existing:
            raise ValueError(f"Transaction '{transaction_db_id}' not found.")

        updates = payload.model_dump(exclude_none=True)
        # Enums arrive as enum members; extract their .value for storage
        for key, val in updates.items():
            if hasattr(val, "value"):
                updates[key] = val.value

        updates["updated_at"] = datetime.utcnow()
        await self.repo.update_one({"_id": transaction_db_id}, updates)

        refreshed = await self.repo.find_one({"_id": transaction_db_id})
        return TransactionResponse(**refreshed)

    # ── Delete ────────────────────────────────────────────────────────────

    async def delete_transaction(self, transaction_db_id: str) -> bool:
        """Hard-deletes a transaction document. Returns True if deleted."""
        existing = await self.repo.find_one({"_id": transaction_db_id})
        if not existing:
            raise ValueError(f"Transaction '{transaction_db_id}' not found.")
        return await self.repo.delete_one({"_id": transaction_db_id})
