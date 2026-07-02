from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Any, Dict, Optional

from app.dependencies.auth import get_current_user, RoleChecker
from app.dependencies.transaction import get_transaction_service
from app.services.transaction import TransactionService
from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionFilterParams,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdateRequest,
    PaymentMethod,
    TransactionStatus,
    SortField,
    SortOrder,
)

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])

# ── Role guards ──────────────────────────────────────────────────────────────
_admin_only = RoleChecker(["Admin"])
_any_role    = RoleChecker(["Admin", "Fraud Analyst"])


# ── POST /api/v1/transactions ────────────────────────────────────────────────

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TransactionResponse,
    summary="Create a new transaction",
    description="Persists a financial transaction record. Available to Admin and Fraud Analyst roles.",
    responses={
        201: {"description": "Transaction created"},
        400: {"description": "Invalid request payload"},
        401: {"description": "Unauthenticated"},
        422: {"description": "Validation error"},
    },
)
async def create_transaction(
    payload: TransactionCreateRequest,
    current_user: Dict[str, Any] = Depends(_any_role),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Creates a new transaction record owned by the authenticated user."""
    try:
        return await service.create_transaction(payload, user_id=current_user["_id"])
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ── GET /api/v1/transactions ─────────────────────────────────────────────────

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=TransactionListResponse,
    summary="List transactions with filters, search, sorting, and pagination",
    description=(
        "Returns a paginated list of transactions. "
        "Admins see all records. Fraud Analysts see only their own transactions."
    ),
)
async def list_transactions(
    # Search params
    transaction_id: Optional[str] = Query(default=None, description="Exact UUID match."),
    merchant: Optional[str] = Query(default=None, description="Partial merchant name search."),
    country: Optional[str] = Query(default=None, description="ISO country code filter."),
    payment_method: Optional[PaymentMethod] = Query(default=None),
    # Filters
    min_amount: Optional[float] = Query(default=None, ge=0, description="Minimum transaction amount."),
    max_amount: Optional[float] = Query(default=None, ge=0, description="Maximum transaction amount."),
    date_from: Optional[str] = Query(default=None, description="ISO 8601 UTC start date, e.g. 2026-01-01T00:00:00Z"),
    date_to: Optional[str] = Query(default=None, description="ISO 8601 UTC end date."),
    merchant_category: Optional[str] = Query(default=None),
    tx_status: Optional[TransactionStatus] = Query(default=None, alias="status"),
    # Sorting
    sort_by: SortField = Query(default=SortField.DATE),
    sort_order: SortOrder = Query(default=SortOrder.DESC),
    # Pagination
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    # Auth
    current_user: Dict[str, Any] = Depends(_any_role),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionListResponse:
    """Lists transactions with optional search, filtering, sorting, and pagination."""
    from datetime import datetime

    def _parse_dt(v: Optional[str]) -> Optional[datetime]:
        if not v:
            return None
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid datetime format: '{v}'. Use ISO 8601, e.g. '2026-01-01T00:00:00Z'.",
            )

    filters = TransactionFilterParams(
        transaction_id=transaction_id,
        merchant=merchant,
        country=country,
        payment_method=payment_method,
        min_amount=min_amount,
        max_amount=max_amount,
        date_from=_parse_dt(date_from),
        date_to=_parse_dt(date_to),
        merchant_category=merchant_category,
        status=tx_status,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    is_admin = current_user.get("role") == "Admin"
    return await service.list_transactions(
        filters=filters,
        requesting_user_id=current_user["_id"],
        is_admin=is_admin,
    )


# ── GET /api/v1/transactions/{id} ────────────────────────────────────────────

@router.get(
    "/{transaction_db_id}",
    status_code=status.HTTP_200_OK,
    response_model=TransactionResponse,
    summary="Retrieve a single transaction by MongoDB document ID",
    responses={
        200: {"description": "Transaction found"},
        404: {"description": "Transaction not found"},
    },
)
async def get_transaction(
    transaction_db_id: str,
    current_user: Dict[str, Any] = Depends(_any_role),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Returns a single transaction by its MongoDB ObjectId string."""
    try:
        return await service.get_transaction(transaction_db_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── PUT /api/v1/transactions/{id} ────────────────────────────────────────────

@router.put(
    "/{transaction_db_id}",
    status_code=status.HTTP_200_OK,
    response_model=TransactionResponse,
    summary="Update a transaction (Admin only)",
    description="Partially updates a transaction record. Restricted to Admin role.",
    responses={
        200: {"description": "Transaction updated"},
        403: {"description": "Forbidden"},
        404: {"description": "Transaction not found"},
    },
)
async def update_transaction(
    transaction_db_id: str,
    payload: TransactionUpdateRequest,
    current_user: Dict[str, Any] = Depends(_admin_only),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Updates allowed fields of an existing transaction. Admin access only."""
    try:
        return await service.update_transaction(transaction_db_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── DELETE /api/v1/transactions/{id} ─────────────────────────────────────────

@router.delete(
    "/{transaction_db_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a transaction (Admin only)",
    description="Hard-deletes a transaction record from the database. Restricted to Admin role.",
    responses={
        200: {"description": "Transaction deleted"},
        403: {"description": "Forbidden"},
        404: {"description": "Transaction not found"},
    },
)
async def delete_transaction(
    transaction_db_id: str,
    current_user: Dict[str, Any] = Depends(_admin_only),
    service: TransactionService = Depends(get_transaction_service),
) -> Dict[str, Any]:
    """Permanently removes a transaction document. Admin access only."""
    try:
        await service.delete_transaction(transaction_db_id)
        return {"success": True, "message": f"Transaction '{transaction_db_id}' deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
