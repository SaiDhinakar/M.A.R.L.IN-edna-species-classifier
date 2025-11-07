"""
Admin API endpoints for dataset approval and training pipeline management.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.dependencies import get_admin_user
from app.database.session import get_db
from app.models.database_models import User, Dataset, TrainingRun, Model
from app.models.schemas import (
    DatasetApprove, DatasetList, TrainingRequest,
    TrainingRunResponse, ModelResponse
)
from app.services.training_workflow import training_workflow
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


async def run_training_pipeline_background(
    dataset_id: int,
    minio_path: str,
    model_name: str,
    hyperparameters: dict,
    training_run_id: int,
    db: Session
):
    """Background task to run training pipeline."""
    try:
        # Update status to running
        training_run = db.query(TrainingRun).filter(TrainingRun.id == training_run_id).first()
        if training_run:
            training_run.status = "running"
            db.commit()
        
        # Run custom training workflow (no ZenML dependencies)
        mlflow_run_id, metrics, results_path = training_workflow.run_training_pipeline(
            dataset_id=dataset_id,
            minio_path=minio_path,
            model_name=model_name,
            hyperparameters=hyperparameters
        )
        
        # Update training run with results
        if training_run:
            training_run.status = "completed"
            training_run.completed_at = datetime.utcnow()
            training_run.mlflow_run_id = mlflow_run_id
            training_run.num_sequences_processed = metrics.get("num_sequences", 0)
            training_run.num_clusters_found = metrics.get("num_clusters", 0)
            training_run.metrics = metrics
            db.commit()
        
        # Update dataset status
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset:
            dataset.status = "completed"
            dataset.processed_at = datetime.utcnow()
            dataset.num_sequences = metrics.get("num_sequences")
            db.commit()
        
        # Create Model record for inference API
        # Check if model with this name already exists
        existing_model = db.query(Model).filter(Model.name == model_name).first()
        
        if existing_model:
            # Deactivate old version
            existing_model.is_active = False
            db.commit()
        
        # Create new model record
        index_name = f"model_{model_name}_{dataset_id}"
        faiss_index_minio_path = f"faiss-indexes/{index_name}.index"
        
        # Generate version string
        from datetime import datetime as dt
        version = f"v{dt.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        new_model = Model(
            name=model_name,
            version=version,
            description=f"Model trained on dataset {dataset_id} with {metrics.get('num_sequences', 0)} sequences",
            minio_path=faiss_index_minio_path,
            model_type="faiss_index",
            mlflow_run_id=mlflow_run_id,
            mlflow_experiment_id=None,  # Can be retrieved from MLflow if needed
            metrics=metrics,
            hyperparameters=hyperparameters,
            status="active",
            is_active=True,
            trained_by=training_run.initiated_by,
            created_at=datetime.utcnow()
        )
        
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        
        # Link model to training run
        training_run.model_id = new_model.id
        db.commit()
        
        logger.info(f"Training pipeline completed for dataset {dataset_id}")
        logger.info(f"Created model: {model_name} (ID: {new_model.id}, Version: {version})")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        
        # Update status to failed
        training_run = db.query(TrainingRun).filter(TrainingRun.id == training_run_id).first()
        if training_run:
            training_run.status = "failed"
            training_run.error_log = str(e)
            training_run.completed_at = datetime.utcnow()
            db.commit()
        
        # Update dataset status
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset:
            dataset.status = "failed"
            dataset.error_message = str(e)
            db.commit()


@router.get("/datasets/pending", response_model=DatasetList)
async def list_pending_datasets(
    page: int = 1,
    page_size: int = 20,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all pending datasets awaiting approval."""
    
    query = db.query(Dataset).filter(Dataset.status.in_(["uploaded", "processed"]))
    
    total = query.count()
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


@router.post("/datasets/{dataset_id}/approve", response_model=DatasetApprove)
async def approve_dataset(
    dataset_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Approve a dataset for training."""
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    if dataset.status not in ["uploaded", "processed", "completed", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset cannot be approved in current status: {dataset.status}"
        )
    
    # Update dataset
    dataset.status = "approved"
    dataset.approved_at = datetime.utcnow()
    dataset.approved_by = admin_user.id
    db.commit()
    
    logger.info(f"Admin {admin_user.username} approved dataset {dataset_id}")
    
    return DatasetApprove(dataset_id=dataset_id, approved=True)


@router.post("/train", response_model=TrainingRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Trigger training pipeline for approved datasets."""
    
    # Validate datasets
    datasets = db.query(Dataset).filter(
        Dataset.id.in_(request.dataset_ids),
        Dataset.status == "approved"
    ).all()
    
    if len(datasets) != len(request.dataset_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some datasets not found or not approved"
        )
    
    # For MVP, train on first dataset only
    dataset = datasets[0]
    
    # Create training run record
    training_run = TrainingRun(
        dataset_id=dataset.id,
        pipeline_name="edna_training_pipeline",
        status="initiated",
        initiated_by=admin_user.id
    )
    
    db.add(training_run)
    db.commit()
    db.refresh(training_run)
    
    # Update dataset status
    dataset.status = "processing"
    db.commit()
    
    # Prepare hyperparameters
    hyperparameters = request.hyperparameters or {}
    hyperparameters.setdefault("batch_size", 32)
    hyperparameters.setdefault("min_cluster_size", 5)
    hyperparameters.setdefault("min_samples", 3)
    
    # Schedule background training
    background_tasks.add_task(
        run_training_pipeline_background,
        dataset_id=dataset.id,
        minio_path=dataset.minio_path,
        model_name=request.model_name,
        hyperparameters=hyperparameters,
        training_run_id=training_run.id,
        db=db
    )
    
    logger.info(f"Training initiated for dataset {dataset.id} by {admin_user.username}")
    
    return training_run


@router.get("/training-runs", response_model=List[TrainingRunResponse])
async def list_training_runs(
    status_filter: str = None,
    limit: int = 20,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List training runs."""
    
    query = db.query(TrainingRun)
    
    if status_filter:
        query = query.filter(TrainingRun.status == status_filter)
    
    runs = query.order_by(TrainingRun.started_at.desc()).limit(limit).all()
    
    return runs


@router.get("/training-runs/{run_id}", response_model=TrainingRunResponse)
async def get_training_run(
    run_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get training run details."""
    
    run = db.query(TrainingRun).filter(TrainingRun.id == run_id).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training run not found"
        )
    
    return run
