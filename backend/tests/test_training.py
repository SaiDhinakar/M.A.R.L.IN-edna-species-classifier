"""
Test the custom training workflow with a small sample dataset.
"""

import logging
import sys
from app.services.training_workflow import training_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_training_workflow():
    """
    Test training workflow with the sample 16S rRNA dataset.
    """
    
    # Sample dataset parameters (adjust these based on your uploaded datasets)
    dataset_id = 1
    minio_path = "datasets/16S_ribosomal_RNA.tar.gz"  # Adjust if different
    model_name = "test_model"
    
    hyperparameters = {
        "min_length": 50,
        "max_length": 2000,
        "batch_size": 16,  # Smaller batch for testing
        "min_cluster_size": 5,
        "min_samples": 3
    }
    
    try:
        logger.info("=" * 60)
        logger.info("Testing Training Workflow")
        logger.info("=" * 60)
        
        # Run the workflow
        mlflow_run_id, metrics, results_path = training_workflow.run_training_pipeline(
            dataset_id=dataset_id,
            minio_path=minio_path,
            model_name=model_name,
            hyperparameters=hyperparameters
        )
        
        logger.info("=" * 60)
        logger.info("✅ Training Workflow Completed Successfully!")
        logger.info("=" * 60)
        logger.info(f"MLflow Run ID: {mlflow_run_id}")
        logger.info(f"Results Path: {results_path}")
        logger.info("\nMetrics:")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Training workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_training_workflow()
    sys.exit(0 if success else 1)
