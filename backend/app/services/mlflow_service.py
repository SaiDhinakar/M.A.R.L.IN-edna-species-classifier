"""
MLflow service for experiment tracking and model registry.
"""

import mlflow
from mlflow.tracking import MlflowClient
from typing import Optional, Dict, Any, List
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


class MLflowService:
    """Service for interacting with MLflow."""
    
    def __init__(self):
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        
        # Configure S3 (MinIO) for artifact storage
        import os
        os.environ["AWS_ACCESS_KEY_ID"] = settings.aws_access_key_id
        os.environ["AWS_SECRET_ACCESS_KEY"] = settings.aws_secret_access_key
        os.environ["MLFLOW_S3_ENDPOINT_URL"] = settings.mlflow_s3_endpoint_url
        
        self.client = MlflowClient()
        self._ensure_experiment()
    
    def _ensure_experiment(self):
        """Ensure the experiment exists."""
        try:
            experiment = self.client.get_experiment_by_name(settings.mlflow_experiment_name)
            if experiment is None:
                experiment_id = self.client.create_experiment(
                    settings.mlflow_experiment_name,
                    artifact_location=f"s3://{settings.minio_bucket_models}/mlflow/"
                )
                logger.info(f"Created MLflow experiment: {settings.mlflow_experiment_name} (ID: {experiment_id})")
            else:
                logger.info(f"Using existing MLflow experiment: {settings.mlflow_experiment_name}")
        except Exception as e:
            logger.error(f"Error ensuring MLflow experiment: {e}")
    
    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Start a new MLflow run."""
        try:
            mlflow.set_experiment(settings.mlflow_experiment_name)
            run = mlflow.start_run(run_name=run_name, tags=tags)
            logger.info(f"Started MLflow run: {run.info.run_id}")
            return run.info.run_id
        except Exception as e:
            logger.error(f"Error starting MLflow run: {e}")
            raise
    
    def end_run(self):
        """End the current MLflow run."""
        try:
            mlflow.end_run()
        except Exception as e:
            logger.error(f"Error ending MLflow run: {e}")
    
    def log_params(self, params: Dict[str, Any]):
        """Log parameters to MLflow."""
        try:
            mlflow.log_params(params)
        except Exception as e:
            logger.error(f"Error logging params: {e}")
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics to MLflow."""
        try:
            mlflow.log_metrics(metrics, step=step)
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """Log an artifact to MLflow."""
        try:
            mlflow.log_artifact(local_path, artifact_path)
        except Exception as e:
            logger.error(f"Error logging artifact: {e}")
    
    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: Optional[str] = None
    ):
        """Log a model to MLflow."""
        try:
            mlflow.pytorch.log_model(
                model,
                artifact_path,
                registered_model_name=registered_model_name
            )
            logger.info(f"Logged model to {artifact_path}")
        except Exception as e:
            logger.error(f"Error logging model: {e}")
            raise
    
    def get_run(self, run_id: str) -> Optional[Any]:
        """Get a run by ID."""
        try:
            return self.client.get_run(run_id)
        except Exception as e:
            logger.error(f"Error getting run {run_id}: {e}")
            return None
    
    def search_runs(
        self,
        filter_string: str = "",
        max_results: int = 100
    ) -> List[Any]:
        """Search for runs."""
        try:
            experiment = self.client.get_experiment_by_name(settings.mlflow_experiment_name)
            if experiment is None:
                return []
            
            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=filter_string,
                max_results=max_results,
                order_by=["start_time DESC"]
            )
            return runs
        except Exception as e:
            logger.error(f"Error searching runs: {e}")
            return []
    
    def get_latest_model_version(
        self,
        model_name: str
    ) -> Optional[str]:
        """Get the latest version of a registered model."""
        try:
            versions = self.client.search_model_versions(f"name='{model_name}'")
            if not versions:
                return None
            
            # Sort by version number and get latest
            latest = max(versions, key=lambda v: int(v.version))
            return latest.version
        except Exception as e:
            logger.error(f"Error getting latest model version: {e}")
            return None
    
    def load_model(
        self,
        model_uri: str
    ) -> Any:
        """Load a model from MLflow."""
        try:
            model = mlflow.pytorch.load_model(model_uri)
            logger.info(f"Loaded model from {model_uri}")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def register_model(
        self,
        model_uri: str,
        model_name: str
    ) -> str:
        """Register a model in the model registry."""
        try:
            result = mlflow.register_model(model_uri, model_name)
            logger.info(f"Registered model {model_name} version {result.version}")
            return result.version
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            raise
    
    def transition_model_stage(
        self,
        model_name: str,
        version: str,
        stage: str
    ):
        """Transition a model to a different stage."""
        try:
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage
            )
            logger.info(f"Transitioned model {model_name} v{version} to {stage}")
        except Exception as e:
            logger.error(f"Error transitioning model stage: {e}")


# Global MLflow service instance
mlflow_service = MLflowService()
