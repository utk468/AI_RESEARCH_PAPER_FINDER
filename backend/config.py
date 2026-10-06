from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "AI Research Paper Finder"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    ALLOWED_ORIGINS: List[str] = ["*"]

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_URI: Optional[str] = None
    MONGODB_DB_NAME: str = "research_paper_finder"
    DATABASE_NAME: Optional[str] = None
    SECRET_KEY: Optional[str] = None

    def model_post_init(self, __context):
        if self.MONGODB_URI and (self.MONGODB_URL == "mongodb://localhost:27017" or not self.MONGODB_URL):
            self.MONGODB_URL = self.MONGODB_URI
        if self.DATABASE_NAME and (self.MONGODB_DB_NAME == "research_paper_finder" or not self.MONGODB_DB_NAME):
            self.MONGODB_DB_NAME = self.DATABASE_NAME

    PDF_STORAGE_PATH: str = "storage/pdfs"

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    SEARCH_PROVIDER: str = "tavily"
    TAVILY_API_KEY: Optional[str] = None

    EMBEDDING_MODEL: str = "google/embeddinggemma-300m"
    HF_TOKEN: Optional[str] = None
    RAG_TOP_K: int = 5
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 80
    MAX_PAPERS_PER_SEARCH: int = 20

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    CACHE_TTL: int = 3600
    ENABLE_CACHE: bool = True

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
