from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Sequence models
class SequenceBase(BaseModel):
    name: str = Field(..., description="Name of the sequence")
    sequence_data: str = Field(..., description="DNA sequence data")


class SequenceCreate(SequenceBase):
    pass


class SequenceResponse(SequenceBase):
    id: int
    length: int
    gc_content: float
    quality_score: float
    status: str
    taxonomy: Optional[Dict[str, str]] = None
    taxonomy_confidence: Optional[float] = None
    cluster_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Cluster models
class ClusterBase(BaseModel):
    name: str = Field(..., description="Name of the cluster")


class ClusterRequest(BaseModel):
    min_cluster_size: int = Field(default=5, description="Minimum cluster size for HDBSCAN")
    min_samples: int = Field(default=3, description="Minimum samples for HDBSCAN")


class ClusterResponse(ClusterBase):
    id: int
    size: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Job models
class JobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Metrics models
class MetricsResponse(BaseModel):
    id: int
    metric_name: str
    metric_value: float
    sequence_id: Optional[int] = None
    cluster_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Analysis request models
class SimilarityRequest(BaseModel):
    sequence_id: int = Field(..., description="ID of the query sequence")
    limit: Optional[int] = Field(default=10, description="Maximum number of similar sequences to return")


class TaxonomyRequest(BaseModel):
    sequence_ids: List[int] = Field(..., description="List of sequence IDs to assign taxonomy")
    method: Optional[str] = Field(default="local", description="Taxonomy assignment method (local, ncbi, auto)")


# Upload response models
class UploadResponse(BaseModel):
    message: str
    sequences: List[Dict[str, Any]]


# Analysis response models
class SimilarityResponse(BaseModel):
    results: List[Dict[str, Any]]


class TaxonomyResponse(BaseModel):
    results: List[Dict[str, Any]]


# Error models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None