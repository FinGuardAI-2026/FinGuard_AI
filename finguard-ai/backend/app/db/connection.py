import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.logging.logger import logger
from app.core.config import settings

class DatabaseManager:
    """Singleton Database Manager orchestrating MongoDB client and connections."""
    
    _instance = None
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    async def connect_to_database(self) -> None:
        """Establishes an asynchronous client session pool with MongoDB Atlas."""
        if self.client is not None:
            logger.warning("MongoDB client is already initialized.")
            return

        logger.info("Initializing asynchronous connection pool with MongoDB...")
        try:
            # Configure motor async client with client options (timeout 5s)
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000
            )
            # Select database context
            self.db = self.client[settings.DATABASE_NAME]
            
            # Verify connectivity via a ping command
            await self.client.admin.command("ping")
            logger.info(
                f"Connected to database successfully: {settings.DATABASE_NAME}"
            )
        except Exception as e:
            logger.error(
                f"Database connection initialization failed: {str(e)}",
                exc_info=e
            )
            self.client = None
            self.db = None
            # Allow startup to continue in a degraded status rather than crashing hard
            raise e

    async def close_database_connection(self) -> None:
        """Gracefully closes all MongoDB client session pools."""
        if self.client is None:
            logger.warning("No active database client session found to close.")
            return

        logger.info("Closing MongoDB client sessions...")
        try:
            self.client.close()
            logger.info("MongoDB client connections closed cleanly.")
        except Exception as e:
            logger.error(f"Error while closing database connections: {str(e)}", exc_info=e)
        finally:
            self.client = None
            self.db = None

    def get_db(self) -> AsyncIOMotorDatabase:
        """Returns the active MongoDB database instance."""
        if self.db is None:
            raise RuntimeError("Database not initialized. Ensure connect_to_database was run.")
        return self.db

    def get_client(self) -> AsyncIOMotorClient:
        """Returns the active MongoDB client instance."""
        if self.client is None:
            raise RuntimeError("Database client not initialized.")
        return self.client

# Singleton reference
db_manager = DatabaseManager()
