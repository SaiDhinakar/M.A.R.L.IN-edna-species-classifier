# backend/pipelines/training_pipeline.py

"""
ZenML training pipeline for the eDNA species classifier.
Run from the 'backend' folder as:
  python -m pipelines.training_pipeline
"""

from zenml import pipeline
from steps import (
    data_ingestion_step,
    data_preprocessing_step,
    embedding_step,
    clustering_step,
    training_step,
    evaluate_step,
)

@pipeline
def training_pipeline():
    # Compose the pipeline steps in order
    df = data_ingestion_step()
    X_train, X_test, y_train, y_test = data_preprocessing_step(df)
    X_train_emb, X_test_emb = embedding_step(X_train, X_test)
    clustering_step(X_train_emb)
    model = training_step(X_train_emb, y_train)
    evaluate_step(model, X_test_emb, y_test)

if __name__ == "__main__":
    print("==============================================")
    print("  🌿 eDNA Species Classifier - ZenML Training Pipeline")
    print("==============================================")
    # Run the pipeline locally
    training_pipeline().run()
    print("==============================================")
    print("✅ Pipeline execution completed successfully!")
    print("==============================================")
