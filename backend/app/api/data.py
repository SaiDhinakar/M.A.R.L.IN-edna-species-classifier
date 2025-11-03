"""
Dataset management API endpoints.
"""

import os
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.database_models import User, Dataset
from app.models.schemas import DatasetResponse, DatasetList, DatasetCreate
from app.services.minio_service import minio_service
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dataset", tags=["datasets"])


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


async def process_dataset_background(dataset_id: int, db: Session):
    """Process uploaded dataset in the background using TrainingWorkflow."""
    from app.database.session import SessionLocal
    from app.services.training_workflow import TrainingWorkflow
    
    # Get fresh db session for background task
    db_session = SessionLocal()
    
    try:
        dataset = db_session.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            logger.error(f"Dataset {dataset_id} not found")
            return
        
        # Update status to processing
        dataset.status = "processing"
        db_session.commit()
        
        logger.info(f"Starting background processing for dataset {dataset_id}")
        
        # Initialize training workflow
        workflow = TrainingWorkflow()
        
        # Load data using TrainingWorkflow (handles both archives and direct files, plus BLAST databases)
        logger.info(f"Loading data from {dataset.minio_path}")
        sequences, sequence_ids = workflow.load_data(dataset_id, dataset.minio_path)
        
        if not sequences or len(sequences) == 0:
            raise ValueError("No sequences loaded from dataset")
        
        logger.info(f"Loaded {len(sequences)} sequences")
        
        # Preprocess data using TrainingWorkflow
        logger.info("Preprocessing sequences")
        filtered_sequences, filtered_ids = workflow.preprocess(sequences, sequence_ids)
        
        logger.info(f"Preprocessed {len(filtered_sequences)} sequences")
        
        # Update dataset with sequence count
        dataset.num_sequences = len(filtered_sequences)
        dataset.status = "processed"  # Changed from "completed" - needs admin approval
        dataset.processed_at = datetime.utcnow()
        db_session.commit()
        
        logger.info(f"Successfully processed dataset {dataset_id} with {len(filtered_sequences)} sequences - awaiting admin approval")
        
    except Exception as e:
        logger.error(f"Error processing dataset {dataset_id}: {e}", exc_info=True)
        dataset = db_session.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset:
            dataset.status = "failed"
            dataset.error_message = str(e)
            db_session.commit()
    finally:
        db_session.close()


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Dataset file (.tar.gz)"),
    description: Optional[str] = Form(None),
    sample_location: Optional[str] = Form(None),
    sample_depth: Optional[float] = Form(None),
    sample_date: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a new dataset (compressed archive or FASTA/FASTQ file) and trigger automatic processing."""
    
    # Validate file extension - accept compressed archives or sequence files
    valid_extensions = ('.tar.gz', '.tgz', '.gz', '.zip', '.fasta', '.fa', '.fna', '.fastq', '.fq', '.txt')
    if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only sequence files or compressed archives are accepted: {', '.join(valid_extensions)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_upload_size} bytes"
        )
    
    # Save file temporarily
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file_path = os.path.join(tmpdir, file.filename)
        
        # Save uploaded file
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Compute file hash
        file_hash = compute_file_hash(temp_file_path)
        
        # Check if file hash already exists
        existing_dataset = db.query(Dataset).filter(Dataset.file_hash == file_hash).first()
        if existing_dataset:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This dataset has already been uploaded"
            )
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{current_user.id}_{timestamp}_{file.filename}"
        object_name = f"users/{current_user.id}/{unique_filename}"
        
        # Upload to MinIO
        try:
            minio_path = minio_service.upload_file(
                temp_file_path,
                object_name,
                settings.minio_bucket_raw,
                content_type="application/gzip"
            )
        except Exception as e:
            logger.error(f"Error uploading to MinIO: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage"
            )
    
    # Parse sample_date if provided
    parsed_date = None
    if sample_date:
        try:
            parsed_date = datetime.fromisoformat(sample_date)
        except ValueError:
            pass
    
    # Create database record
    new_dataset = Dataset(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename,
        file_size=file_size,
        file_hash=file_hash,
        minio_path=minio_path,
        status="uploaded",
        description=description,
        sample_location=sample_location,
        sample_depth=sample_depth,
        sample_date=parsed_date
    )
    
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    
    logger.info(f"User {current_user.username} uploaded dataset {new_dataset.id}")
    
    # Trigger background processing
    background_tasks.add_task(process_dataset_background, new_dataset.id, db)
    logger.info(f"Queued background processing for dataset {new_dataset.id}")
    
    return new_dataset


@router.get("/list", response_model=DatasetList)
async def list_datasets(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    user_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List datasets with pagination.
    
    - If user_only=True: Returns only current user's datasets
    - If admin: Returns all datasets
    - If regular user: Returns only approved datasets (public)
    """
    
    # Build query based on user role and filter
    if user_only:
        # Return only current user's datasets
        query = db.query(Dataset).filter(Dataset.user_id == current_user.id)
    elif current_user.role == "admin":
        # Admins see all datasets
        query = db.query(Dataset)
    else:
        # Regular users see only approved datasets
        query = db.query(Dataset).filter(Dataset.status == "approved")
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter(Dataset.status == status_filter)
    
    # Get total count
    total = query.count()
    
    # Paginate
    datasets = query.order_by(Dataset.uploaded_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return DatasetList(
        datasets=datasets,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dataset details."""
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check ownership or admin
    if dataset.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this dataset"
        )
    
    return dataset


@router.get("/{dataset_id}/download")
async def download_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download dataset file."""
    from fastapi.responses import FileResponse
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check ownership or admin
    if dataset.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this dataset"
        )
    
    # Download from MinIO to temporary file
    try:
        # Parse minio_path (format: "bucket/path/to/file")
        parts = dataset.minio_path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid minio_path format: {dataset.minio_path}")
        
        bucket = parts[0]
        object_name = parts[1]
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        local_file_path = os.path.join(temp_dir, dataset.original_filename or dataset.filename)
        
        # Download from MinIO
        minio_service.download_file(object_name, bucket, local_file_path)
        
        # Return file
        return FileResponse(
            path=local_file_path,
            filename=dataset.original_filename or dataset.filename,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={dataset.original_filename or dataset.filename}"
            }
        )
    except Exception as e:
        logger.error(f"Error downloading dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download dataset: {str(e)}"
        )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a dataset."""
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Check ownership or admin
    if dataset.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this dataset"
        )
    
    # Delete from MinIO
    try:
        parts = dataset.minio_path.split("/", 1)
        if len(parts) == 2:
            minio_service.delete_object(parts[1], parts[0])
    except Exception as e:
        logger.error(f"Error deleting from MinIO: {e}")
    
    # Delete from database
    db.delete(dataset)
    db.commit()
    
    logger.info(f"Deleted dataset {dataset_id}")
    
    return None
