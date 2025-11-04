"""
Search API endpoints for querying sequences and clusters.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
import pandas as pd
import tempfile
import os
from datetime import datetime

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.database_models import User, Sequence, Model, TrainingRun
from app.models.schemas import SearchQuery, SearchResponse, SequenceResult
from app.services.minio_service import minio_service
from app.utils.logger import get_logger


logger = get_logger(__name__, log_file="logs/search.log")
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/query", response_model=SearchResponse)
async def search_sequences(
    query: SearchQuery,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search sequences by taxonomy, cluster, or sequence ID.
    
    Searches in the processed parquet files from the active model's dataset.
    """
    
    # Get the active model to determine which dataset to search
    active_model = db.query(Model).filter(Model.is_active == True).first()
    
    if not active_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active model found. Please train or activate a model first."
        )
    
    # Get the dataset_id from training run
    training_run = db.query(TrainingRun).filter(TrainingRun.model_id == active_model.id).first()
    
    if not training_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No training run found for model {active_model.id}"
        )
    
    dataset_id = training_run.dataset_id
    
    logger.info(f"Searching in dataset {dataset_id} for query '{query.query}' (type: {query.search_type})")
    
    # Load processed parquet file from MinIO
    try:
        parquet_path = f"processed/dataset_{dataset_id}_processed.parquet"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "processed.parquet")
            
            # Download from MinIO
            minio_service.download_file(
                parquet_path,
                local_path,
                bucket_name="datasets"
            )
            
            # Load parquet file
            df = pd.read_parquet(local_path)
            logger.info(f"Loaded {len(df)} sequences from {parquet_path}")
            
            # Apply search filter based on search type
            if query.search_type == "taxonomy":
                # Search in sequence_id (which contains taxonomy info)
                filtered_df = df[df['sequence_id'].str.contains(query.query, case=False, na=False)]
            
            elif query.search_type == "cluster":
                # Search by cluster ID
                try:
                    cluster_id = int(query.query)
                    filtered_df = df[df['cluster_id'] == cluster_id]
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cluster ID must be an integer"
                    )
            
            elif query.search_type == "sequence_id":
                # Search by sequence ID
                filtered_df = df[df['sequence_id'].str.contains(query.query, case=False, na=False)]
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid search type: {query.search_type}"
                )
            
            total = len(filtered_df)
            logger.info(f"Found {total} matches")
            
            # Apply pagination
            paginated_df = filtered_df.iloc[query.offset:query.offset + query.limit]
            
            # Convert to SequenceResult objects
            results = []
            for idx, row in paginated_df.iterrows():
                result = SequenceResult(
                    id=int(idx),
                    sequence_id=row['sequence_id'],
                    length=int(row['sequence_length']),
                    cluster_id=int(row['cluster_id']) if pd.notna(row['cluster_id']) else None,
                    taxonomy=row['sequence_id'],  # Use sequence_id as taxonomy
                    confidence=None,
                    created_at=datetime.utcnow()  # Use current time as placeholder
                )
                results.append(result)
            
            return SearchResponse(
                results=results,
                total=total,
                query=query.query,
                search_type=query.search_type
            )
    
    except Exception as e:
        logger.error(f"Error searching sequences: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search sequences: {str(e)}"
        )


@router.get("/clusters")
async def list_clusters(
    model_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all unique clusters from the active model's dataset."""
    
    # Get the active model or specified model
    if model_id:
        model = db.query(Model).filter(Model.id == model_id).first()
    else:
        model = db.query(Model).filter(Model.is_active == True).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No model found"
        )
    
    # Get dataset_id from training run
    training_run = db.query(TrainingRun).filter(TrainingRun.model_id == model.id).first()
    
    if not training_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No training run found for model {model.id}"
        )
    
    dataset_id = training_run.dataset_id
    
    try:
        parquet_path = f"processed/dataset_{dataset_id}_processed.parquet"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "processed.parquet")
            
            minio_service.download_file(
                parquet_path,
                local_path,
                bucket_name="datasets"
            )
            
            df = pd.read_parquet(local_path)
            
            # Get unique clusters (excluding NaN)
            clusters = df['cluster_id'].dropna().unique().tolist()
            clusters = sorted([int(c) for c in clusters])
            
            # Get cluster stats
            cluster_stats = []
            for cluster_id in clusters:
                count = len(df[df['cluster_id'] == cluster_id])
                cluster_stats.append({
                    "cluster_id": cluster_id,
                    "size": count
                })
            
            return {
                "clusters": clusters,
                "total": len(clusters),
                "cluster_stats": cluster_stats,
                "dataset_id": dataset_id,
                "model_id": model.id
            }
    
    except Exception as e:
        logger.error(f"Error listing clusters: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list clusters: {str(e)}"
        )


@router.get("/taxonomies")
async def list_taxonomies(
    limit: int = 100,
    model_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List unique sequence IDs (taxonomies) from the active model's dataset."""
    
    # Get the active model or specified model
    if model_id:
        model = db.query(Model).filter(Model.id == model_id).first()
    else:
        model = db.query(Model).filter(Model.is_active == True).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No model found"
        )
    
    # Get dataset_id from training run
    training_run = db.query(TrainingRun).filter(TrainingRun.model_id == model.id).first()
    
    if not training_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No training run found for model {model.id}"
        )
    
    dataset_id = training_run.dataset_id
    
    try:
        parquet_path = f"processed/dataset_{dataset_id}_processed.parquet"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, "processed.parquet")
            
            minio_service.download_file(
                parquet_path,
                "datasets",
                local_path,
                # bucket_name="datasets",
                # bucket_name=minio_service.settings.minio_bucket_datasets
            )
            
            df = pd.read_parquet(local_path)
            
            # Get unique sequence IDs (limit to first N)
            taxonomies = df['sequence_id'].unique()[:limit].tolist()
            
            return {
                "taxonomies": taxonomies,
                "total": len(taxonomies),
                "total_in_dataset": len(df['sequence_id'].unique()),
                "dataset_id": dataset_id,
                "model_id": model.id
            }
    
    except Exception as e:
        logger.error(f"Error listing taxonomies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list taxonomies: {str(e)}"
        )
