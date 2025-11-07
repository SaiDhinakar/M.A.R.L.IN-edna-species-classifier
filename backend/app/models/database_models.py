"""
SQLAlchemy database models for users, datasets, models, and sequences.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class User(Base):
    """User account model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # 'user' or 'admin'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    datasets = relationship("Dataset", foreign_keys="[Dataset.user_id]", back_populates="owner", cascade="all, delete-orphan")


class Dataset(Base):
    """Uploaded dataset metadata."""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_hash = Column(String(64), nullable=True)  # SHA256 hash
    minio_path = Column(String(500), nullable=False)
    
    # Metadata
    status = Column(String(50), default="uploaded", nullable=False)
    # status: uploaded, validated, approved, processing, completed, failed
    
    description = Column(Text, nullable=True)
    sample_location = Column(String(255), nullable=True)
    sample_depth = Column(Float, nullable=True)
    sample_date = Column(DateTime, nullable=True)
    
    # Processing info
    num_sequences = Column(Integer, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    owner = relationship("User", foreign_keys="[Dataset.user_id]", back_populates="datasets")
    approver = relationship("User", foreign_keys="[Dataset.approved_by]")
    training_runs = relationship("TrainingRun", back_populates="dataset")


class Model(Base):
    """Trained model metadata."""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Storage
    minio_path = Column(String(500), nullable=False)
    model_type = Column(String(50), nullable=False)  # 'embedding', 'clustering', etc.
    
    # MLflow tracking
    mlflow_run_id = Column(String(100), nullable=True)
    mlflow_experiment_id = Column(String(100), nullable=True)
    
    # Metrics
    metrics = Column(JSON, nullable=True)
    # Example: {"accuracy": 0.95, "num_clusters": 45, "silhouette_score": 0.78}
    
    # Hyperparameters
    hyperparameters = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(50), default="training", nullable=False)
    # status: training, completed, failed, deployed
    is_active = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    trained_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    trainer = relationship("User", foreign_keys="[Model.trained_by]")
    training_runs = relationship("TrainingRun", back_populates="model")


class TrainingRun(Base):
    """Training pipeline execution record."""
    __tablename__ = "training_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    
    # Pipeline info
    pipeline_name = Column(String(100), nullable=False)
    zenml_run_id = Column(String(100), nullable=True)
    mlflow_run_id = Column(String(100), nullable=True)
    
    # Status
    status = Column(String(50), default="initiated", nullable=False)
    # status: initiated, running, completed, failed
    
    # Results
    num_sequences_processed = Column(Integer, nullable=True)
    num_clusters_found = Column(Integer, nullable=True)
    metrics = Column(JSON, nullable=True)
    error_log = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="training_runs")
    model = relationship("Model", back_populates="training_runs")
    initiator = relationship("User", foreign_keys="[TrainingRun.initiated_by]")


class Sequence(Base):
    """Individual DNA sequence metadata (for quick lookup)."""
    __tablename__ = "sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    
    # Sequence data
    sequence_id = Column(String(100), nullable=False, index=True)
    sequence_hash = Column(String(64), nullable=True, index=True)
    length = Column(Integer, nullable=False)
    
    # Classification
    cluster_id = Column(Integer, nullable=True, index=True)
    taxonomy = Column(String(500), nullable=True)
    confidence = Column(Float, nullable=True)
    
    # Vector embedding reference (stored in PostgreSQL/FAISS)
    embedding_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    dataset = relationship("Dataset", foreign_keys="[Sequence.dataset_id]")


class ClusterMetadata(Base):
    """Cluster information and statistics."""
    __tablename__ = "cluster_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    
    cluster_id = Column(Integer, nullable=False, index=True)
    cluster_size = Column(Integer, nullable=False)
    
    # Representative sequence
    representative_sequence_id = Column(String(100), nullable=True)
    
    # Taxonomy (if known)
    predicted_taxonomy = Column(String(500), nullable=True)
    taxonomy_confidence = Column(Float, nullable=True)
    
    # Statistics
    avg_sequence_length = Column(Float, nullable=True)
    diversity_index = Column(Float, nullable=True)
    
    # Additional cluster information (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    cluster_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    model = relationship("Model", foreign_keys="[ClusterMetadata.model_id]")
