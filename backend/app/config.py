import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Textify"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://textify:textify@localhost:5432/textify"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # S3-compatible storage
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "textify"
    S3_REGION: str = "us-east-1"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Upload settings
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = [".pdf"]
    
    # Worker
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
