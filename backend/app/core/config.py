"""
Application configuration.
Loads settings from environment variables (12-factor style), with sane
local-dev defaults so the app can boot without a .env file.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "AI Enterprise Knowledge Assistant"
    ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Security / Auth ---
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@db:5432/knowledge_assistant"

    # --- Vector store ---
    VECTOR_DB_PROVIDER: str = "chroma"  # "chroma" | "faiss"
    CHROMA_PERSIST_DIR: str = "/app/vector_store"

    # --- LLM / Embeddings ---
    # LLM_PROVIDER supports: "watsonx", "huggingface", "openai", "mock"
    LLM_PROVIDER: str = "mock"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # IBM watsonx.ai
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    WATSONX_MODEL_ID: str = "ibm/granite-13b-instruct-v2"

    HUGGINGFACEHUB_API_TOKEN: str = ""

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # --- File uploads ---
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_MB: int = 25

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
