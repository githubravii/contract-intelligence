from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_KEY: str = "dev-secret-key"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/contract_intel"
    
    # AI Services
    ANTHROPIC_API_KEY: str
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # Security
    LOG_PII_REDACTION: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()