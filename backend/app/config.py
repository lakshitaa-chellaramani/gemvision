"""
GemVision Configuration
Centralized configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file explicitly before creating Settings
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, override=True)  # Force override existing env vars


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # AI API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    tripo_api_key: str = ""  # Tripo3D API for 3D model generation

    # AWS Settings
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = "gemvision-images"

    # Database
    database_url: str = "sqlite:///./gemvision.db"

    # Application
    backend_url: str = "https://gemvision.ai"
    backend_port: int = 8000

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # CORS
    allowed_origins: str = "https://gemvision.ai,http://localhost:3000,http://localhost:8000"

    # Image Generation
    default_image_model: str = "dall-e-3"
    image_quality: str = "hd"
    image_size: str = "1024x1024"
    max_images_per_generation: int = 4

    # QC Inspector
    qc_mode: str = "simulated"  # simulated or ml
    qc_confidence_threshold: float = 0.7
    qc_model_path: str = "./models/qc_model.h5"

    # File Upload
    max_upload_size_mb: int = 10
    allowed_image_types: str = "image/jpeg,image/png,image/webp"

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Logging
    log_level: str = "INFO"

    # Optional: Redis
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600

    # Email/SMTP Settings
    smtp_host: str = Field(default="smtp.gmail.com", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_user: str = Field(default="", validation_alias="SMTP_USER")
    smtp_password: str = Field(default="", validation_alias="SMTP_PASSWORD")
    from_email: str = Field(default="", validation_alias="FROM_EMAIL")
    frontend_url: str = Field(default="https://gemvision.ai", validation_alias="FRONTEND_URL")

    class Config:
        # Look for .env file in the project root directory
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def allowed_mime_types(self) -> List[str]:
        """Parse allowed image types from comma-separated string"""
        return [mime.strip() for mime in self.allowed_image_types.split(",")]


# Global settings instance
settings = Settings()
