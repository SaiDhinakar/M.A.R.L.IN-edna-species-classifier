"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ===== Auth Schemas =====

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


# ===== Dataset Schemas =====

class DatasetBase(BaseModel):
    description: Optional[str] = None
    sample_location: Optional[str] = None
    sample_depth: Optional[float] = None
    sample_date: Optional[datetime] = None


class DatasetCreate(DatasetBase):
    pass


class DatasetResponse(DatasetBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    filename: str
    original_filename: str
    file_size: int
    status: str
    num_sequences: Optional[int] = None
    uploaded_at: datetime
    approved_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DatasetList(BaseModel):
    datasets: List[DatasetResponse]
    total: int
    page: int
    page_size: int


class DatasetApprove(BaseModel):
    dataset_id: int
    approved: bool = True


# ===== Model Schemas =====

class ModelBase(BaseModel):
    name: str
    description: Optional[str] = None


class ModelResponse(ModelBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    version: str
    model_type: str
    status: str
    is_active: bool
    metrics: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    created_at: datetime


class ModelList(BaseModel):
    models: List[ModelResponse]
    total: int


# ===== Training Schemas =====

class TrainingRequest(BaseModel):
    dataset_ids: List[int]
    model_name: Optional[str] = "edna_classifier"
    hyperparameters: Optional[Dict[str, Any]] = None


class TrainingRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    dataset_id: int
    model_id: Optional[int] = None
    pipeline_name: str
    status: str
    num_sequences_processed: Optional[int] = None
    num_clusters_found: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None
    error_log: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


# ===== Inference Schemas =====

class InferenceRequest(BaseModel):
    sequence: str = Field(..., min_length=10, description="DNA sequence to classify")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of similar sequences to return")


class SimilarSequence(BaseModel):
    sequence_id: str
    similarity: float
    cluster_id: Optional[int] = Field(
        None, 
        description="Cluster ID: -1 = noise/outlier, >= 0 = valid cluster, None = not clustered"
    )
    taxonomy: Optional[str] = None
    species_name: Optional[str] = None


class InferenceResponse(BaseModel):
    sequence_hash: str
    cluster_id: Optional[int] = Field(
        None,
        description="Predicted cluster ID: -1 = noise/outlier, >= 0 = valid cluster, None = no prediction"
    )
    predicted_taxonomy: Optional[str] = None
    predicted_species: Optional[str] = None
    confidence: Optional[float] = None
    similar_sequences: List[SimilarSequence]
    processing_time: float


# ===== Search Schemas =====

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    search_type: str = Field(default="taxonomy", description="Search type: taxonomy, cluster, sequence_id")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SequenceResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sequence_id: str
    length: int
    cluster_id: Optional[int] = None
    taxonomy: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime


class SearchResponse(BaseModel):
    results: List[SequenceResult]
    total: int
    query: str
    search_type: str


# ===== Visualization Schemas =====

class BiodiversityMetrics(BaseModel):
    total_sequences: int
    unique_clusters: int
    shannon_index: float
    simpson_index: float
    taxa_richness: int


class ClusterSummary(BaseModel):
    cluster_id: int
    size: int
    representative_taxonomy: Optional[str] = None
    avg_confidence: Optional[float] = None
    percentage: float


class VisualizationResponse(BaseModel):
    biodiversity: BiodiversityMetrics
    top_clusters: List[ClusterSummary]
    dataset_id: Optional[int] = None
    model_version: Optional[str] = None


# ===== Health Check =====

class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, bool] = {}
