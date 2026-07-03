from typing import Any, Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base import BaseRepository
from app.db.collections import collections


class TransactionRepository(BaseRepository):
    """
    Transaction-specific database repository.

    Inherits generic CRUD from BaseRepository.
    Adds query-building logic for filters, search, sorting, and pagination.
    Contains NO business logic — only database I/O.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, collections.TRANSACTIONS)

    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Queries a transaction by its UUID transaction_id field."""
        return await self.find_one({"transaction_id": transaction_id})

    def _build_filter(
        self,
        user_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        merchant: Optional[str] = None,
        country: Optional[str] = None,
        payment_method: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        date_from: Optional[Any] = None,
        date_to: Optional[Any] = None,
        merchant_category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Constructs a MongoDB query filter dict from optional parameters."""
        query: Dict[str, Any] = {}

        if user_id:
            query["user_id"] = user_id
        if transaction_id:
            query["transaction_id"] = transaction_id
        if merchant:
            # Partial case-insensitive search on merchant_name
            query["merchant_name"] = {"$regex": merchant, "$options": "i"}
        if country:
            query["country"] = country.upper()
        if payment_method:
            query["payment_method"] = payment_method
        if merchant_category:
            query["merchant_category"] = {"$regex": merchant_category, "$options": "i"}
        if status:
            query["status"] = status

        # Amount range
        amount_filter: Dict[str, float] = {}
        if min_amount is not None:
            amount_filter["$gte"] = min_amount
        if max_amount is not None:
            amount_filter["$lte"] = max_amount
        if amount_filter:
            query["amount"] = amount_filter

        # Date range on transaction_time
        date_filter: Dict[str, Any] = {}
        if date_from:
            date_filter["$gte"] = date_from
        if date_to:
            date_filter["$lte"] = date_to
        if date_filter:
            query["transaction_time"] = date_filter

        return query

    async def find_filtered(
        self,
        user_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        merchant: Optional[str] = None,
        country: Optional[str] = None,
        payment_method: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        date_from: Optional[Any] = None,
        date_to: Optional[Any] = None,
        merchant_category: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "transaction_time",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 25,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Returns (list_of_documents, total_matching_count) for the given filters.
        Handles sorting and pagination internally.
        """
        query = self._build_filter(
            user_id=user_id,
            transaction_id=transaction_id,
            merchant=merchant,
            country=country,
            payment_method=payment_method,
            min_amount=min_amount,
            max_amount=max_amount,
            date_from=date_from,
            date_to=date_to,
            merchant_category=merchant_category,
            status=status,
        )

        total = await self.collection.count_documents(query)

        mongo_sort_dir = -1 if sort_order == "desc" else 1
        offset = (page - 1) * page_size

        cursor = (
            self.collection.find(query)
            .sort(sort_by, mongo_sort_dir)
            .skip(offset)
            .limit(page_size)
        )
        results = await cursor.to_list(length=page_size)
        # print("Mongo Query:", query)
        # print("Total Found:", total)
        # print("Results:", results)
        return [self._format_result(r) for r in results], total
