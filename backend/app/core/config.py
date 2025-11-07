"""
Core configuration module for M.A.R.L.IN eDNA Classifier Backend.
Loads and validates environment variables.
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "M.A.R.L.IN eDNA Classifier"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    
    # Database
    sqlite_path: str = "./data/app.db"
    postgres_url: str
    
    # MinIO Object Storage
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool = False
    minio_bucket_raw: str = "raw-datasets"
    minio_bucket_processed: str = "processed"
    minio_bucket_models: str = "models"
    minio_bucket_logs: str = "logs"
    
    # Redis
    redis_url: str
    redis_cache_expire: int = 3600
    
    # MLflow
    mlflow_tracking_uri: str
    mlflow_experiment_name: str = "edna_classification"
    mlflow_s3_endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    
    # ZenML
    zenml_server_url: str = ""
    zenml_store_type: str = "local"
    zenml_artifact_store: str = "./data/zenml_artifacts"
    
    # Model Configuration
    model_embedding_dim: int = 768
    model_max_seq_length: int = 512
    model_cache_size: int = 5
    
    # Pipeline Configuration
    batch_size: int = 32
    num_clusters: int = 50
    min_cluster_size: int = 5
    
    # API Configuration
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    max_upload_size: int = 524288000  # 500MB
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def database_url(self) -> str:
        """Get SQLite database URL."""
        return f"sqlite:///{self.sqlite_path}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
