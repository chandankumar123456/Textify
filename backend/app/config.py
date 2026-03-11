from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Textify"
    DEBUG: bool = False

    # Database — defaults to local SQLite, set DATABASE_URL for PostgreSQL
    DATABASE_URL: str = "sqlite:///./data/textify.db"

    # Local filesystem storage root
    DATA_DIR: str = "data"

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # Upload settings
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = [".pdf"]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
