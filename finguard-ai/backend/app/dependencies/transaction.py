from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.dependencies.database import get_mongo_db
from app.repositories.transaction import TransactionRepository
from app.services.transaction import TransactionService


async def get_transaction_repository(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> TransactionRepository:
    """Provides a TransactionRepository scoped to the active database session."""
    return TransactionRepository(db)


async def get_transaction_service(
    repo: TransactionRepository = Depends(get_transaction_repository),
) -> TransactionService:
    """Provides a TransactionService wired to the TransactionRepository."""
    return TransactionService(repo)
