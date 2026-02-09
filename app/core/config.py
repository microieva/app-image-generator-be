import os
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field, validator


class Settings(BaseSettings):
    # ===== Application Settings =====
    APP_ENV: str = Field(default="development", description="Environment: development, staging, production")
    APP_NAME: str = Field(default="Image Generator API", description="Application name")
    APP_HOST: str = Field(default="0.0.0.0", description="Host to bind the application")
    APP_PORT: int = Field(default=8000, description="Port to bind the application")
    DEBUG: bool = Field(default=True, description="Debug mode")
    
    # ===== Database Settings (MSSQL) =====
    DB_SERVER: str = Field(..., description="MSSQL server hostname or IP")
    DB_PORT: str = Field(default="1433", description="MSSQL server port")
    DB_NAME: str = Field(..., description="Database name")
    DB_USER: str = Field(..., description="Database username")
    DB_PASSWORD: str = Field(..., description="Database password")
    DB_DRIVER: str = Field(
        default="ODBC Driver 17 for SQL Server", 
        description="ODBC driver name for MSSQL"
    )
    
    # ===== API Keys =====
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_SPACE_URL: str = os.getenv("HF_SPACE_URL", "https://microieva-generator.hf.space")
    
    GROQ_API_KEY: Optional[str] = Field(
        default=None, 
        description="Groq API key for LLM services (optional)"
    )
    
    # ===== Hugging Face Model Settings =====
    HF_API_URL: str = Field(
        default="https://", 
        description="Base URL for Hugging Face model inference API"
    )
    HF_MODEL_ID: str = Field(
        default="stabilityai/sdxl-turbo", 
        description="Default Hugging Face model ID for image generation"
    )
    HF_SPACE_ID: str = Field(
        default="microieva/generators", 
        description="Default Hugging Face Space ID for image generation"
    )
    HF_MODEL_CACHE_DIR: str = Field(
        default="./data/models", 
        description="Directory to cache downloaded models"
    )
    HF_MODEL_REVISION: Optional[str] = Field(
        default=None, 
        description="Specific model revision (branch/tag/commit)"
    )
    
    # ===== Image Generation Settings =====
    DEFAULT_IMAGE_WIDTH: int = Field(default=512, description="Default generated image width")
    DEFAULT_IMAGE_HEIGHT: int = Field(default=512, description="Default generated image height")
    DEFAULT_NUM_INFERENCE_STEPS: int = Field(default=50, description="Default number of inference steps")
    DEFAULT_GUIDANCE_SCALE: float = Field(default=7.5, description="Default guidance scale")
    
    # ===== File Storage Settings =====
    MAX_IMAGE_SIZE_MB: int = Field(default=10, description="Maximum uploaded image size in MB")
    ALLOWED_IMAGE_EXTENSIONS: List[str] = Field(
        default=["png", "jpg", "jpeg", "webp"], 
        description="Allowed image file extensions"
    )
    GENERATED_IMAGES_DIR: str = Field(
        default="./data/generated", 
        description="Directory to store generated images"
    )
    UPLOADED_IMAGES_DIR: str = Field(
        default="./data/uploads", 
        description="Directory to store uploaded images"
    )
    
    # ===== Caching Settings =====
    REDIS_URL: Optional[str] = Field(
        default=None, 
        description="Redis URL for caching (optional)"
    )
    CACHE_TTL_SECONDS: int = Field(
        default=3600, 
        description="Default cache TTL in seconds"
    )
    
    # ===== Security Settings =====
    SECRET_KEY: str = Field(
        default="change-this-in-production-to-a-secure-random-string",
        description="Secret key for JWT tokens and security"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        description="JWT access token expiration time in minutes"
    )
    CORS_ORIGINS: List[str] = Field(
        default=["*"], 
        description="Allowed CORS origins"
    )
    
    # ===== Rate Limiting =====
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per minute per IP")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")

    REQUEST_TIMEOUT: int = Field(default=300, description="Timeout for external API requests in seconds")
    
    # ===== Logging Settings =====
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="./data/logs/app.log", description="Log file path")
    
    # ===== Validation and computed properties =====
    
    @validator("DB_PORT")
    def validate_db_port(cls, v):
        """Validate database port."""
        if not v.isdigit():
            raise ValueError("DB_PORT must be a valid port number")
        port = int(v)
        if not (1 <= port <= 65535):
            raise ValueError("DB_PORT must be between 1 and 65535")
        return v
    
    @validator("ALLOWED_IMAGE_EXTENSIONS")
    def validate_image_extensions(cls, v):
        """Validate and normalize image extensions."""
        return [ext.lower().strip() for ext in v]
    
    @property
    def database_url(self) -> str:
        """
        Returns the SQLAlchemy connection URL for MSSQL.
        """
        return (
            f"mssql+pyodbc://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
            f"?driver={self.DB_DRIVER.replace(' ', '+')}"
        )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.APP_ENV.lower() == "testing"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore" 


settings = Settings()


def get_settings() -> Settings:
    return settings