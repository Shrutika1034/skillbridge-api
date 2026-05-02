"""
Configuration and environment variables
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/skillbridge"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    MONITORING_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Monitoring Officer API Key
    MONITORING_API_KEY: str = "skillbridge-monitoring-key-12345"
    
    # Environment
    DEBUG: bool = False
    
    class Config:
        env_file = BASE_DIR / ".env"
        case_sensitive = True

settings = Settings()
