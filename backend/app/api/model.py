"""
Model inference API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.database_models import User, Model
from app.models.schemas import InferenceRequest, InferenceResponse, ModelList, ModelResponse
from app.services.inference import inference_service
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/model", tags=["model"])


@router.post("/infer", response_model=InferenceResponse)
async def infer_sequence(
    request: InferenceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Classify a DNA sequence using the trained model."""
    
    # Validate sequence (basic validation)
    sequence = request.sequence.upper().replace(' ', '').replace('\n', '')
    
    if not all(base in 'ATGCN' for base in sequence):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid DNA sequence. Only A, T, G, C, N characters allowed."
        )
    
    if len(sequence) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sequence too short. Minimum length is 10 bases."
        )
    
    # Check if model is loaded
    model_info = inference_service.get_model_info()
    if model_info["status"] == "no_model_loaded":
        # Try to load the latest active model
        latest_model = db.query(Model).filter(
            Model.is_active == True,
            Model.status == "active"
        ).order_by(Model.created_at.desc()).first()
        
        if not latest_model:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No trained model available. Please train a model first."
            )
        
        try:
            # Extract index name from minio_path
            # minio_path format: indices/model_edna_classifier_v1_2.faiss
            # index_name format: model_edna_classifier_v1_2
            minio_path = latest_model.minio_path
            if minio_path.endswith('.faiss'):
                index_name = minio_path.split('/')[-1].replace('.faiss', '')
            else:
                # Fallback: construct from model name and find dataset_id from training_run
                from app.models.database_models import TrainingRun
                training_run = db.query(TrainingRun).filter(TrainingRun.model_id == latest_model.id).first()
                dataset_id = training_run.dataset_id if training_run else latest_model.id
                index_name = f"model_{latest_model.name}_{dataset_id}"
            
            # Get dataset_id for loading cluster metadata
            from app.models.database_models import TrainingRun
            training_run = db.query(TrainingRun).filter(TrainingRun.model_id == latest_model.id).first()
            dataset_id = training_run.dataset_id if training_run else None
            
            logger.info(f"Loading model '{latest_model.name}' with index '{index_name}' and dataset_id={dataset_id}")
            inference_service.load_model(latest_model.version, index_name, dataset_id=dataset_id)
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load model: {str(e)}"
            )
    
    # Perform inference
    try:
        result = inference_service.infer(sequence, top_k=request.top_k)
        return result
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        )


@router.get("/versions", response_model=ModelList)
async def list_model_versions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all available model versions."""
    
    models = db.query(Model).order_by(Model.created_at.desc()).all()
    
    return ModelList(
        models=models,
        total=len(models)
    )


@router.get("/info")
async def get_model_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get currently loaded model information."""
    
    return inference_service.get_model_info()


@router.post("/activate/{model_id}")
async def activate_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark a model as the active model (for auto-loading).
    This does NOT load the model into memory - use /load endpoint for that.
    """
    
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.status not in ["completed", "active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model training not completed (status: {model.status})"
        )
    
    try:
        # Deactivate all other models
        db.query(Model).update({"is_active": False})
        
        # Activate this model
        model.is_active = True
        db.commit()
        
        logger.info(f"Activated model {model.id} ({model.name} {model.version})")
        
        return {
            "message": f"Model {model.name} version {model.version} is now active",
            "model_id": model.id,
            "note": "Model is marked as active but not loaded. Use /load endpoint to load it into memory."
        }
    except Exception as e:
        logger.error(f"Error activating model: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate model: {str(e)}"
        )


@router.post("/load/{model_id}")
async def load_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Load a specific model version into memory for inference."""
    
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Check if training completed successfully
    if model.status not in ["completed", "active"]:  # Support legacy 'active' status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model training not completed (status: {model.status})"
        )
    
    try:
        # Extract index name from minio_path
        # minio_path format: indices/model_edna_classifier_v1_2.faiss
        minio_path = model.minio_path
        if minio_path.endswith('.faiss'):
            index_name = minio_path.split('/')[-1].replace('.faiss', '')
        else:
            # Fallback: construct from model name and id
            index_name = f"model_{model.name}_{model.id}"
        
        # Get dataset_id for loading cluster metadata
        from app.models.database_models import TrainingRun
        training_run = db.query(TrainingRun).filter(TrainingRun.model_id == model.id).first()
        dataset_id = training_run.dataset_id if training_run else None
        
        logger.info(f"Loading model '{model.name}' (ID: {model.id}) with index '{index_name}', dataset_id={dataset_id}")
        
        inference_service.load_model(model.version, index_name, dataset_id=dataset_id)
        
        # Mark this model as active and others as inactive
        db.query(Model).update({"is_active": False})
        model.is_active = True
        db.commit()
        
        return {
            "message": f"Successfully loaded model {model.name} version {model.version}",
            "model_id": model.id,
            "index_name": index_name,
            "dataset_id": dataset_id
        }
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {str(e)}"
        )
