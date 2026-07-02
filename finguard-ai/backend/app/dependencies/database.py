from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.db.connection import db_manager

async def get_mongo_client() -> AsyncIOMotorClient:
    """FastAPI Dependency providing the current active MongoDB client session."""
    return db_manager.get_client()

async def get_mongo_db() -> AsyncIOMotorDatabase:
    """FastAPI Dependency providing the current active MongoDB database context."""
    return db_manager.get_db()
