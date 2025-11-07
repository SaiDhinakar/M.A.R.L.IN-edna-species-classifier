#!/usr/bin/env python3
"""
Create Model record for completed training run.
This fixes the issue where training completed but no Model record was created.
"""

import sys
sys.path.insert(0, '/run/media/spidey/35f48b83-0fe4-4b1f-ba92-81ad5e6b81f61/M.A.R.L.IN-edna-species-classifier/backend')

from app.database.session import SessionLocal
from app.models.database_models import Model, TrainingRun
from datetime import datetime

def create_model_from_training_run(training_run_id: int):
    """Create Model record from completed training run."""
    db = SessionLocal()
    
    try:
        # Get training run
        training_run = db.query(TrainingRun).filter(TrainingRun.id == training_run_id).first()
        
        if not training_run:
            print(f"❌ Training run {training_run_id} not found")
            return
        
        if training_run.status != "completed":
            print(f"❌ Training run {training_run_id} has status '{training_run.status}', not 'completed'")
            return
        
        print(f"\n✅ Found completed training run:")
        print(f"   ID: {training_run.id}")
        print(f"   Dataset ID: {training_run.dataset_id}")
        print(f"   Sequences: {training_run.num_sequences_processed}")
        print(f"   Clusters: {training_run.num_clusters_found}")
        print(f"   MLflow Run ID: {training_run.mlflow_run_id}")
        
        # Check if model already exists
        if training_run.model_id:
            existing_model = db.query(Model).filter(Model.id == training_run.model_id).first()
            if existing_model:
                print(f"\n✅ Model already exists:")
                print(f"   ID: {existing_model.id}")
                print(f"   Name: {existing_model.name}")
                print(f"   Version: {existing_model.version}")
                print(f"   Status: {existing_model.status}")
                print(f"   Active: {existing_model.is_active}")
                return
        
        # Create model record
        model_name = "edna_classifier_v1"
        dataset_id = training_run.dataset_id
        index_name = f"model_{model_name}_{dataset_id}"
        faiss_index_minio_path = f"indices/{index_name}.faiss"
        
        # Generate version
        version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Get metrics
        metrics = training_run.metrics or {}
        
        print(f"\n📝 Creating model record:")
        print(f"   Name: {model_name}")
        print(f"   Version: {version}")
        print(f"   MinIO Path: models/{faiss_index_minio_path}")
        
        # Deactivate all existing models first (only one should be active)
        db.query(Model).update({"is_active": False})
        db.commit()
        print(f"   Deactivated all existing models")
        
        new_model = Model(
            name=model_name,
            version=version,
            description=f"Model trained on dataset {dataset_id} with {training_run.num_sequences_processed} sequences",
            minio_path=faiss_index_minio_path,
            model_type="faiss_index",
            mlflow_run_id=training_run.mlflow_run_id,
            mlflow_experiment_id=None,
            metrics=metrics,
            hyperparameters={},
            status="completed",  # Status represents training state, not deployment
            is_active=True,      # This new model becomes the active one
            trained_by=training_run.initiated_by,
            created_at=datetime.utcnow()
        )
        
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        
        # Link model to training run
        training_run.model_id = new_model.id
        db.commit()
        
        print(f"\n✅ Model created successfully!")
        print(f"   Model ID: {new_model.id}")
        print(f"   Name: {new_model.name}")
        print(f"   Version: {new_model.version}")
        print(f"   MinIO Path: {new_model.minio_path}")
        print(f"   Status: {new_model.status}")
        print(f"   Active: {new_model.is_active}")
        
        print(f"\n🔗 Linked to training run {training_run.id}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_model_record.py <training_run_id>")
        print("\nExample:")
        print("  python create_model_record.py 2")
        sys.exit(1)
    
    training_run_id = int(sys.argv[1])
    
    print("=" * 60)
    print("Create Model Record from Training Run")
    print("=" * 60)
    
    create_model_from_training_run(training_run_id)
    
    print("\n" + "=" * 60)
