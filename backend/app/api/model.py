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


@router.get("/{model_id}/metrics")
async def get_model_metrics(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed evaluation metrics for a specific model.
    
    Returns comprehensive clustering quality metrics, diversity indices,
    and overall quality assessment.
    """
    
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    metrics = model.metrics or {}
    
    # Extract detailed evaluation if available
    detailed_eval = metrics.get('detailed_evaluation', {})
    
    return {
        "model_id": model.id,
        "model_name": model.name,
        "model_version": model.version,
        "status": model.status,
        "is_active": model.is_active,
        "created_at": model.created_at,
        
        # Summary metrics
        "summary": {
            "num_sequences": metrics.get('num_sequences', 0),
            "num_clusters": metrics.get('num_clusters', 0),
            "num_noise_points": metrics.get('num_noise_points', 0),
            "overall_quality_score": metrics.get('overall_quality_score', 0.0)
        },
        
        # Clustering quality
        "clustering_quality": {
            "silhouette_score": metrics.get('silhouette_score'),
            "davies_bouldin_index": metrics.get('davies_bouldin_index'),
            "calinski_harabasz_score": metrics.get('calinski_harabasz_score'),
            "noise_ratio": metrics.get('noise_ratio', 0.0),
            "clustered_ratio": metrics.get('clustered_ratio', 0.0)
        },
        
        # Cluster statistics
        "cluster_stats": {
            "min_cluster_size": metrics.get('min_cluster_size_actual'),
            "max_cluster_size": metrics.get('max_cluster_size'),
            "avg_cluster_size": metrics.get('avg_cluster_size'),
            "median_cluster_size": metrics.get('median_cluster_size'),
            "top_clusters": detailed_eval.get('clustering', {}).get('top_clusters', [])
        },
        
        # Diversity metrics
        "diversity": {
            "shannon_diversity": metrics.get('shannon_diversity', 0.0),
            "simpson_diversity": metrics.get('simpson_diversity', 0.0),
            "effective_n_clusters": metrics.get('effective_n_clusters')
        },
        
        # Sequence statistics
        "sequence_stats": {
            "avg_length": metrics.get('avg_sequence_length'),
            "min_length": metrics.get('min_sequence_length'),
            "max_length": metrics.get('max_sequence_length'),
            "embedding_dim": metrics.get('embedding_dim', 768)
        },
        
        # Full metrics (for advanced users)
        "full_metrics": metrics
    }


@router.get("/{model_id}/evaluation")
async def get_model_evaluation_report(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a human-readable evaluation report for a model.
    
    Returns a formatted report with interpretations and recommendations.
    """
    
    model = db.query(Model).filter(Model.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    metrics = model.metrics or {}
    
    # Generate interpretation
    quality_score = metrics.get('overall_quality_score', 0.0)
    silhouette = metrics.get('silhouette_score')
    noise_ratio = metrics.get('noise_ratio', 0.0)
    n_clusters = metrics.get('num_clusters', 0)
    
    # Quality interpretation
    if quality_score >= 7.0:
        quality_level = "Excellent"
        quality_desc = "The model shows strong clustering performance with well-separated, cohesive clusters."
    elif quality_score >= 5.0:
        quality_level = "Good"
        quality_desc = "The model performs well with reasonable cluster quality."
    elif quality_score >= 3.0:
        quality_level = "Fair"
        quality_desc = "The model shows moderate clustering quality. Consider tuning hyperparameters."
    else:
        quality_level = "Poor"
        quality_desc = "The model shows weak clustering. Dataset may need more preprocessing or different parameters."
    
    # Recommendations
    recommendations = []
    
    if noise_ratio > 0.5:
        recommendations.append(
            f"High noise ratio ({noise_ratio*100:.1f}%). Consider: "
            "1) Reducing min_cluster_size parameter, "
            "2) Adding more diverse training data, "
            "3) Improving sequence quality control"
        )
    
    if silhouette and silhouette < 0.3:
        recommendations.append(
            f"Low silhouette score ({silhouette:.3f}). Clusters may overlap. "
            "Consider using different clustering parameters or feature engineering."
        )
    
    if n_clusters < 3:
        recommendations.append(
            f"Very few clusters ({n_clusters}). Dataset may be too homogeneous or "
            "clustering parameters may be too strict."
        )
    
    return {
        "model_id": model.id,
        "model_name": model.name,
        "model_version": model.version,
        "evaluation_date": model.created_at,
        
        "overall_assessment": {
            "quality_score": quality_score,
            "quality_level": quality_level,
            "description": quality_desc
        },
        
        "key_metrics": {
            "Total Sequences": metrics.get('num_sequences', 0),
            "Clusters Found": n_clusters,
            "Noise Points": metrics.get('num_noise_points', 0),
            "Clustering Quality (Silhouette)": f"{silhouette:.3f}" if silhouette else "N/A",
            "Diversity (Shannon Index)": f"{metrics.get('shannon_diversity', 0):.3f}",
            "Average Cluster Size": metrics.get('avg_cluster_size')
        },
        
        "interpretation": {
            "clustering_quality": (
                f"Silhouette score of {silhouette:.3f} " if silhouette else "No silhouette score available. "
            ) + (
                "indicates excellent cluster separation." if silhouette and silhouette > 0.7
                else "indicates good cluster separation." if silhouette and silhouette > 0.5
                else "indicates moderate cluster separation." if silhouette and silhouette > 0.3
                else "indicates weak cluster separation." if silhouette
                else ""
            ),
            
            "diversity": f"Shannon diversity index of {metrics.get('shannon_diversity', 0):.2f} "
                        f"suggests {'high' if metrics.get('shannon_diversity', 0) > 3 else 'moderate' if metrics.get('shannon_diversity', 0) > 1.5 else 'low'} "
                        f"taxonomic diversity in the dataset.",
            
            "noise": f"{noise_ratio*100:.1f}% of sequences are marked as noise (not fitting any cluster well). "
                    f"This is {'acceptable' if noise_ratio < 0.3 else 'moderate' if noise_ratio < 0.5 else 'high'}."
        },
        
        "recommendations": recommendations if recommendations else [
            "Model quality is good. No specific recommendations at this time."
        ],
        
        "metrics_guide": {
            "Silhouette Score": "Ranges from -1 to 1. >0.7 excellent, 0.5-0.7 good, 0.3-0.5 moderate, <0.3 poor",
            "Davies-Bouldin Index": "Lower is better. <1.0 excellent, 1.0-2.0 good, >2.0 poor",
            "Shannon Diversity": "Higher indicates more diversity. >3 high, 1.5-3 moderate, <1.5 low",
            "Overall Quality Score": "0-10 scale. >7 excellent, 5-7 good, 3-5 fair, <3 poor"
        }
    }
