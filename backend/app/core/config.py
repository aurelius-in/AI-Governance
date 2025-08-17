from typing import List, Optional
from pydantic import BaseSettings, Field, validator
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    POSTGRES_URL: str = Field(..., env="POSTGRES_URL")
    REDIS_URL: str = Field(..., env="REDIS_URL")
    
    # OPA Policy Engine
    OPA_URL: str = Field(..., env="OPA_URL")
    
    # OpenTelemetry
    OTEL_ENDPOINT: Optional[str] = Field(default=None, env="OTEL_ENDPOINT")
    OTEL_SERVICE_NAME: str = Field(default="ai-governance-backend", env="OTEL_SERVICE_NAME")
    
    # Authentication
    OIDC_ISSUER_URL: Optional[str] = Field(default=None, env="OIDC_ISSUER_URL")
    OIDC_CLIENT_ID: Optional[str] = Field(default=None, env="OIDC_CLIENT_ID")
    OIDC_CLIENT_SECRET: Optional[str] = Field(default=None, env="OIDC_CLIENT_SECRET")
    OIDC_AUDIENCE: Optional[str] = Field(default=None, env="OIDC_AUDIENCE")
    
    # JWT
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:5173"], env="CORS_ORIGINS")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ENCRYPTION_KEY: str = Field(..., env="ENCRYPTION_KEY")
    
    # Cost Tracking
    DEFAULT_DAILY_BUDGET: float = Field(default=100.0, env="DEFAULT_DAILY_BUDGET")
    DEFAULT_MONTHLY_BUDGET: float = Field(default=1000.0, env="DEFAULT_MONTHLY_BUDGET")
    
    # Evaluation
    EVAL_DATASET_PATH: str = Field(default="/app/datasets", env="EVAL_DATASET_PATH")
    EVAL_RESULTS_PATH: str = Field(default="/app/eval_results", env="EVAL_RESULTS_PATH")
    
    # Monitoring
    PROMETHEUS_MULTIPROC_DIR: str = Field(default="/tmp", env="PROMETHEUS_MULTIPROC_DIR")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Email
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # File Upload
    MAX_FILE_SIZE: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    UPLOAD_PATH: str = Field(default="/app/uploads", env="UPLOAD_PATH")
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ENCRYPTION_KEY")
    def validate_encryption_key(cls, v):
        if len(v) != 32:
            raise ValueError("ENCRYPTION_KEY must be exactly 32 bytes")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
os.makedirs(settings.EVAL_DATASET_PATH, exist_ok=True)
os.makedirs(settings.EVAL_RESULTS_PATH, exist_ok=True)
os.makedirs(settings.PROMETHEUS_MULTIPROC_DIR, exist_ok=True)
