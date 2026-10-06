import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

    PROJECT_NAME: str = "Bulk Certificate Generator API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/certificates.db")
    
    # File Storage configuration
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage" / "certificates"))
    
    # Server base URL for generating verification QR codes and download links
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # Maximum recipients allowed in a single bulk request
    MAX_BATCH_SIZE: int = 1000

settings = Settings()

# Ensure storage directory exists
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
