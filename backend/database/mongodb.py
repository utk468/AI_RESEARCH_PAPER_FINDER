from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from pymongo import ASCENDING, DESCENDING, IndexModel

from pymongo.errors import ConnectionFailure

from backend.config import settings
from backend.utils.logger import logger

class MongoDB:
    """
    Async MongoDB client wrapper using Motor.
    Provides lazy initialization and collection accessors.
    """

    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
            )
            self.database = self.client[settings.MONGODB_DB_NAME]

            await self.client.admin.command("ping")
            logger.info(f"Connected to MongoDB: {settings.MONGODB_URL}")
            await self._create_indexes()
        except ConnectionFailure as exc:
            logger.error(f"MongoDB connection failed: {exc}")
            raise

    async def disconnect(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    async def _create_indexes(self) -> None:
        """Create necessary indexes for performance."""

        await self.papers.create_indexes([
            IndexModel([("paper_id", ASCENDING)], unique=True),
            IndexModel([("url", ASCENDING)]),
            IndexModel([("year", DESCENDING)]),
            IndexModel([("$**", "text")]),
        ])

        await self.search_history.create_indexes([
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("query", ASCENDING)]),
        ])

        await self.bookmarks.create_indexes([
            IndexModel([("user_id", ASCENDING), ("paper_id", ASCENDING)], unique=True),
        ])
        logger.info("MongoDB indexes created.")

    @property
    def papers(self) -> AsyncIOMotorCollection:
        return self.database["papers"]

    @property
    def search_history(self) -> AsyncIOMotorCollection:
        return self.database["search_history"]

    @property
    def users(self) -> AsyncIOMotorCollection:
        return self.database["users"]

    @property
    def bookmarks(self) -> AsyncIOMotorCollection:
        return self.database["bookmarks"]

    @property
    def feedback(self) -> AsyncIOMotorCollection:
        return self.database["feedback"]

    @property
    def chat_history(self) -> AsyncIOMotorCollection:
        return self.database["chat_history"]

mongodb = MongoDB()

async def get_db() -> MongoDB:
    return mongodb
