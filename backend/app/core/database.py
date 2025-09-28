from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from app.core.config import get_settings
import datetime

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class Sequence(Base):
    __tablename__ = "sequences"
    
    id = Column(String, primary_key=True, index=True)
    cluster_id = Column(String, ForeignKey("clusters.id"), nullable=True)
    sequence_data = Column(Text, nullable=False)
    length = Column(Integer, nullable=False)
    quality_score = Column(Float, nullable=False)
    taxa = Column(String, nullable=True)
    novelty_score = Column(Float, nullable=True)
    sample_date = Column(DateTime, default=datetime.datetime.utcnow)
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    embedding_path = Column(String, nullable=True)  # Path in MinIO
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    cluster = relationship("Cluster", back_populates="sequences")


class Cluster(Base):
    __tablename__ = "clusters"
    
    id = Column(String, primary_key=True, index=True)
    sequence_count = Column(Integer, default=0)
    consensus_sequence = Column(Text, nullable=True)
    novelty_score = Column(Float, nullable=True)
    dominant_taxa = Column(String, nullable=True)
    avg_quality = Column(Float, nullable=True)
    model_path = Column(String, nullable=True)  # Path to clustering model in MinIO
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sequences = relationship("Sequence", back_populates="cluster")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    job_type = Column(String, nullable=False)  # preprocessing, embedding, clustering, etc.
    status = Column(String, nullable=False, default="pending")  # pending, running, completed, failed
    input_data = Column(Text, nullable=True)  # JSON string of input parameters
    result_data = Column(Text, nullable=True)  # JSON string of results
    error_message = Column(Text, nullable=True)
    progress = Column(Float, default=0.0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Metrics(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    shannon_index = Column(Float, nullable=True)
    richness = Column(Integer, nullable=True)
    evenness = Column(Float, nullable=True)
    known_taxa_percent = Column(Float, nullable=True)
    novel_taxa_percent = Column(Float, nullable=True)
    total_sequences = Column(Integer, nullable=True)
    total_clusters = Column(Integer, nullable=True)
    novel_taxa_count = Column(Integer, nullable=True)
    quality_score_avg = Column(Float, nullable=True)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())


class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Path in MinIO
    file_size = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="uploaded")  # uploaded, processing, completed, failed
    sequence_count = Column(Integer, nullable=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


# Dependency to get DB session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)