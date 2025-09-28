import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # FastAPI settings
    app_name: str = "eDNA Species Classifier API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database settings
    database_url: str = "sqlite:///./edna_database.db"
    
    # MinIO settings
    minio_endpoint: str = "127.0.0.1:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "admin123"
    minio_secure: bool = False
    minio_bucket_raw: str = "edna-raw-data"
    minio_bucket_processed: str = "edna-processed"
    minio_bucket_models: str = "edna-models"
    
    # Redis settings (for background jobs)
    redis_url: str = "redis://localhost:6379"
    
    # ML Pipeline settings
    min_sequence_length: int = 100
    min_quality_score: float = 90.0
    embedding_model_name: str = "zhihan1996/DNABERT-2-117M"
    clustering_min_cluster_size: int = 5
    kmer_size: int = 6
    
    # Security settings
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-frontend-domain.com"
    ]
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
