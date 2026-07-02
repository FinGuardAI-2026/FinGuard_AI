import math
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionUpdateRequest,
    TransactionFilterParams,
    PaymentMethod,
    TransactionType,
    TransactionStatus,
    SortField,
    SortOrder,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_tx_doc(overrides: dict = None) -> dict:
    doc = {
        "_id": "64f1a2b3c4d5e6f7a8b9c0d1",
        "transaction_id": "00000000-0000-0000-0000-000000000001",
        "user_id": "user_abc",
        "amount": 500.00,
        "currency": "USD",
        "merchant_name": "Amazon",
        "merchant_category": "E-COMMERCE",
        "payment_method": "CREDIT_CARD",
        "transaction_type": "PURCHASE",
        "status": "PENDING",
        "country": "USA",
        "city": "New York",
        "latitude": 40.71,
        "longitude": -74.00,
        "ip_address": "203.0.113.1",
        "device_id": "DEV-abc123",
        "browser": "Chrome",
        "operating_system": "Windows 11",
        "transaction_time": datetime.utcnow(),
        "prediction": None,
        "fraud_probability": None,
        "confidence_score": None,
        "risk_score": None,
        "shap_summary": None,
        "llm_report": None,
        "investigation_status": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    if overrides:
        doc.update(overrides)
    return doc


def _make_create_request(**kwargs) -> TransactionCreateRequest:
    defaults = dict(
        amount=500.00,
        currency="USD",
        merchant_name="Amazon",
        merchant_category="E-COMMERCE",
        payment_method=PaymentMethod.CREDIT_CARD,
        transaction_type=TransactionType.PURCHASE,
        country="USA",
        ip_address="203.0.113.1",
        device_id="DEV-abc123",
    )
    defaults.update(kwargs)
    return TransactionCreateRequest(**defaults)


# ── Schema Validation Tests ──────────────────────────────────────────────────

class TestTransactionSchemas:
    def test_create_request_valid(self):
        req = _make_create_request()
        assert req.currency == "USD"
        assert req.amount == 500.00

    def test_create_request_negative_amount_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _make_create_request(amount=-10.0)

    def test_create_request_invalid_currency_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _make_create_request(currency="us")  # lowercase / wrong length

    def test_create_request_invalid_ip_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _make_create_request(ip_address="not-an-ip")

    def test_create_request_invalid_device_id_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            _make_create_request(device_id="DEV bad id!")

    def test_update_request_empty_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TransactionUpdateRequest()  # All fields None should fail


# ── TransactionService Unit Tests ────────────────────────────────────────────

@pytest.mark.asyncio
class TestTransactionService:
    async def test_create_transaction_success(self):
        from app.services.transaction import TransactionService

        doc = _make_tx_doc()
        mock_repo = AsyncMock()
        mock_repo.insert_one.return_value = doc["_id"]
        mock_repo.find_one.return_value = doc

        service = TransactionService(mock_repo)
        result = await service.create_transaction(_make_create_request(), user_id="user_abc")

        assert result.transaction_id == doc["transaction_id"]
        assert result.amount == 500.00
        mock_repo.insert_one.assert_called_once()

    async def test_get_transaction_not_found_raises(self):
        from app.services.transaction import TransactionService

        mock_repo = AsyncMock()
        mock_repo.find_one.return_value = None

        service = TransactionService(mock_repo)
        with pytest.raises(ValueError, match="not found"):
            await service.get_transaction("nonexistent_id")

    async def test_get_transaction_success(self):
        from app.services.transaction import TransactionService

        doc = _make_tx_doc()
        mock_repo = AsyncMock()
        mock_repo.find_one.return_value = doc

        service = TransactionService(mock_repo)
        result = await service.get_transaction(doc["_id"])
        assert result.amount == 500.00

    async def test_list_transactions_admin_sees_all(self):
        from app.services.transaction import TransactionService

        docs = [_make_tx_doc(), _make_tx_doc({"_id": "other_id", "user_id": "other_user"})]
        mock_repo = AsyncMock()
        mock_repo.find_filtered.return_value = (docs, 2)

        service = TransactionService(mock_repo)
        filters = TransactionFilterParams()
        result = await service.list_transactions(filters, requesting_user_id="user_abc", is_admin=True)

        assert result.total_records == 2
        assert result.total_pages == 1
        # Admin: user_id_filter should be None
        call_kwargs = mock_repo.find_filtered.call_args.kwargs
        assert call_kwargs.get("user_id") is None

    async def test_list_transactions_analyst_scoped(self):
        from app.services.transaction import TransactionService

        docs = [_make_tx_doc()]
        mock_repo = AsyncMock()
        mock_repo.find_filtered.return_value = (docs, 1)

        service = TransactionService(mock_repo)
        filters = TransactionFilterParams()
        result = await service.list_transactions(filters, requesting_user_id="user_abc", is_admin=False)

        call_kwargs = mock_repo.find_filtered.call_args.kwargs
        assert call_kwargs.get("user_id") == "user_abc"
        assert result.total_records == 1

    async def test_list_transactions_pagination_total_pages(self):
        from app.services.transaction import TransactionService

        mock_repo = AsyncMock()
        mock_repo.find_filtered.return_value = ([], 73)

        service = TransactionService(mock_repo)
        filters = TransactionFilterParams(page=1, page_size=25)
        result = await service.list_transactions(filters, requesting_user_id="u", is_admin=True)

        assert result.total_pages == math.ceil(73 / 25)  # 3

    async def test_update_transaction_not_found_raises(self):
        from app.services.transaction import TransactionService

        mock_repo = AsyncMock()
        mock_repo.find_one.return_value = None

        service = TransactionService(mock_repo)
        with pytest.raises(ValueError, match="not found"):
            await service.update_transaction("bad_id", TransactionUpdateRequest(amount=999.0))

    async def test_update_transaction_success(self):
        from app.services.transaction import TransactionService

        doc = _make_tx_doc()
        updated_doc = _make_tx_doc({"amount": 999.0})
        mock_repo = AsyncMock()
        mock_repo.find_one.side_effect = [doc, updated_doc]
        mock_repo.update_one.return_value = True

        service = TransactionService(mock_repo)
        result = await service.update_transaction(doc["_id"], TransactionUpdateRequest(amount=999.0))
        assert result.amount == 999.0

    async def test_delete_transaction_not_found_raises(self):
        from app.services.transaction import TransactionService

        mock_repo = AsyncMock()
        mock_repo.find_one.return_value = None

        service = TransactionService(mock_repo)
        with pytest.raises(ValueError, match="not found"):
            await service.delete_transaction("bad_id")

    async def test_delete_transaction_success(self):
        from app.services.transaction import TransactionService

        doc = _make_tx_doc()
        mock_repo = AsyncMock()
        mock_repo.find_one.return_value = doc
        mock_repo.delete_one.return_value = True

        service = TransactionService(mock_repo)
        result = await service.delete_transaction(doc["_id"])
        assert result is True
