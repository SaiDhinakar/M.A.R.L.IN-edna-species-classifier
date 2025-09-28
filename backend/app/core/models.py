from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    PREPROCESSING = "preprocessing"
    EMBEDDING = "embedding"
    CLUSTERING = "clustering"
    TAXONOMY = "taxonomy"
    METRICS = "metrics"
    FULL_ANALYSIS = "full_analysis"


# Base models
class SequenceBase(BaseModel):
    id: str
    sequence_data: str
    length: int
    quality_score: float
    taxa: Optional[str] = None
    novelty_score: Optional[float] = None
    sample_date: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class SequenceCreate(BaseModel):
    id: str
    sequence_data: str
    quality_score: float
    sample_date: Optional[datetime] = None
    location: Optional[str] = None


class SequenceUpdate(BaseModel):
    notes: Optional[str] = None
    taxa: Optional[str] = None
    novelty_score: Optional[float] = None


class SequenceResponse(SequenceBase):
    cluster_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ClusterBase(BaseModel):
    id: str
    sequence_count: int = 0
    consensus_sequence: Optional[str] = None
    novelty_score: Optional[float] = None
    dominant_taxa: Optional[str] = None
    avg_quality: Optional[float] = None


class ClusterResponse(ClusterBase):
    sequences: List[str] = []  # List of sequence IDs
    locations: List[str] = []  # List of unique locations
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MetricsResponse(BaseModel):
    shannon_index: Optional[float] = None
    richness: Optional[int] = None
    evenness: Optional[float] = None
    known_taxa_percent: Optional[float] = None
    novel_taxa_percent: Optional[float] = None
    total_sequences: Optional[int] = None
    total_clusters: Optional[int] = None
    novel_taxa_count: Optional[int] = None
    quality_score_avg: Optional[float] = None
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class TaxonomicDistribution(BaseModel):
    name: str
    value: float
    count: int


class DiversityOverTime(BaseModel):
    date: str
    shannon: float
    richness: int
    samples: int


class ClusterSizeData(BaseModel):
    cluster: str
    size: int
    novelty: float


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    input_data: Optional[Dict[str, Any]] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    file_type: str
    status: str
    sequence_count: Optional[int] = None
    job_id: Optional[str] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    upload_id: Optional[str] = None
    sequence_ids: Optional[List[str]] = None
    run_preprocessing: bool = True
    run_embedding: bool = True
    run_clustering: bool = True
    run_taxonomy: bool = True
    run_metrics: bool = True


class SearchResponse(BaseModel):
    sequences: List[SequenceResponse] = []
    clusters: List[ClusterResponse] = []
    total_count: int = 0


# Pagination models
class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 10
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int
    
    @classmethod
    def create(cls, items: List[Any], total: int, page: int, limit: int):
        pages = (total + limit - 1) // limit
        return cls(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )