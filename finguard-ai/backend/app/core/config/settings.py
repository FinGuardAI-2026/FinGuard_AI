import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application configuration schema loaded from system environment or .env file."""
    
    # Metadata
    APP_NAME: str = Field(default="FinGuard AI", validation_alias="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", validation_alias="APP_VERSION")
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    
    # Networking
    HOST: str = Field(default="0.0.0.0", validation_alias="HOST")
    PORT: int = Field(default=8000, validation_alias="PORT")
    
    # Storage
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017/finguard",
        validation_alias="MONGODB_URI"
    )
    DATABASE_NAME: str = Field(default="finguard", validation_alias="DATABASE_NAME")
    
    # Security
    JWT_SECRET: str = Field(
        default="placeholder-jwt-secret-key-change-this-in-production",
        validation_alias="JWT_SECRET"
    )
    
    # GenAI Interface
    GEMINI_API_KEY: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")

    # Load from environment file (.env) relative to execution cwd
    model_config = SettingsConfigDict(
        env_file="../.env.development",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate config
settings = Settings()
# # print("MONGODB_URI =", settings.MONGODB_URI)
# # print("DATABASE_NAME =", settings.DATABASE_NAME)
# print("JWT_SECRET =", settings.JWT_SECRET)
# # print("ENV =", settings.ENVIRONMENT)
# # print("GEMINI =", settings.GEMINI_API_KEY)
