"""
Visualization and metrics API endpoints.
"""

from collections import Counter
import math
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.database_models import User, Sequence, Dataset, ClusterMetadata
from app.models.schemas import VisualizationResponse, BiodiversityMetrics, ClusterSummary
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/visualize", tags=["visualization"])


def calculate_shannon_index(counts: list) -> float:
    """Calculate Shannon diversity index."""
    total = sum(counts)
    if total == 0:
        return 0.0
    
    shannon = 0.0
    for count in counts:
        if count > 0:
            proportion = count / total
            shannon -= proportion * math.log(proportion)
    
    return shannon


def calculate_simpson_index(counts: list) -> float:
    """Calculate Simpson diversity index."""
    total = sum(counts)
    if total == 0:
        return 0.0
    
    simpson = sum((count / total) ** 2 for count in counts)
    return simpson


@router.get("/summary", response_model=VisualizationResponse)
async def get_biodiversity_summary(
    dataset_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get biodiversity metrics and cluster summaries."""
    
    # Build base query
    query = db.query(Sequence)
    
    if dataset_id:
        # Validate dataset access
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        if dataset.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this dataset"
            )
        
        query = query.filter(Sequence.dataset_id == dataset_id)
    
    # Get all sequences
    sequences = query.all()
    
    if not sequences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sequences found"
        )
    
    total_sequences = len(sequences)
    
    # Count clusters
    cluster_counts = Counter(seq.cluster_id for seq in sequences if seq.cluster_id is not None)
    unique_clusters = len(cluster_counts)
    
    # Calculate diversity indices
    counts = list(cluster_counts.values())
    shannon_index = calculate_shannon_index(counts)
    simpson_index = calculate_simpson_index(counts)
    
    # Count unique taxonomies
    taxonomies = set(seq.taxonomy for seq in sequences if seq.taxonomy)
    taxa_richness = len(taxonomies)
    
    # Create biodiversity metrics
    biodiversity = BiodiversityMetrics(
        total_sequences=total_sequences,
        unique_clusters=unique_clusters,
        shannon_index=shannon_index,
        simpson_index=simpson_index,
        taxa_richness=taxa_richness
    )
    
    # Get top clusters
    top_clusters_data = cluster_counts.most_common(10)
    top_clusters = []
    
    for cluster_id, count in top_clusters_data:
        # Get sequences in this cluster
        cluster_seqs = [s for s in sequences if s.cluster_id == cluster_id]
        
        # Get representative taxonomy
        taxonomies_in_cluster = [s.taxonomy for s in cluster_seqs if s.taxonomy]
        representative_taxonomy = None
        if taxonomies_in_cluster:
            # Most common taxonomy in cluster
            taxonomy_counts = Counter(taxonomies_in_cluster)
            representative_taxonomy = taxonomy_counts.most_common(1)[0][0]
        
        # Average confidence
        confidences = [s.confidence for s in cluster_seqs if s.confidence is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else None
        
        cluster_summary = ClusterSummary(
            cluster_id=cluster_id,
            size=count,
            representative_taxonomy=representative_taxonomy,
            avg_confidence=avg_confidence,
            percentage=(count / total_sequences) * 100
        )
        top_clusters.append(cluster_summary)
    
    return VisualizationResponse(
        biodiversity=biodiversity,
        top_clusters=top_clusters,
        dataset_id=dataset_id,
        model_version=None  # Would be populated from model info
    )


@router.get("/cluster/{cluster_id}")
async def get_cluster_details(
    cluster_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific cluster."""
    
    # Get sequences in cluster
    sequences = db.query(Sequence).filter(Sequence.cluster_id == cluster_id).all()
    
    if not sequences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster {cluster_id} not found"
        )
    
    # Aggregate statistics
    taxonomies = [s.taxonomy for s in sequences if s.taxonomy]
    taxonomy_counts = Counter(taxonomies)
    
    confidences = [s.confidence for s in sequences if s.confidence is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else None
    
    lengths = [s.length for s in sequences]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    
    return {
        "cluster_id": cluster_id,
        "size": len(sequences),
        "taxonomies": dict(taxonomy_counts.most_common(10)),
        "avg_confidence": avg_confidence,
        "avg_sequence_length": avg_length,
        "min_length": min(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0
    }


@router.get("/dataset/{dataset_id}/stats")
async def get_dataset_stats(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get statistics for a specific dataset."""
    
    # Validate dataset access
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    if dataset.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this dataset"
        )
    
    # Get sequence statistics
    sequence_stats = db.query(
        func.count(Sequence.id).label('total'),
        func.avg(Sequence.length).label('avg_length'),
        func.min(Sequence.length).label('min_length'),
        func.max(Sequence.length).label('max_length')
    ).filter(Sequence.dataset_id == dataset_id).first()
    
    # Get cluster count
    cluster_count = db.query(Sequence.cluster_id).filter(
        Sequence.dataset_id == dataset_id,
        Sequence.cluster_id.isnot(None)
    ).distinct().count()
    
    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset.original_filename,
        "total_sequences": sequence_stats.total or 0,
        "avg_sequence_length": float(sequence_stats.avg_length) if sequence_stats.avg_length else 0,
        "min_sequence_length": sequence_stats.min_length or 0,
        "max_sequence_length": sequence_stats.max_length or 0,
        "num_clusters": cluster_count,
        "status": dataset.status,
        "uploaded_at": dataset.uploaded_at.isoformat(),
        "processed_at": dataset.processed_at.isoformat() if dataset.processed_at else None
    }
