"""
ZenML training pipeline for the eDNA species classifier.
Connects all pipeline steps from notebooks 01-06.
Run from the 'backend' folder as: python -m pipelines.training_pipeline
"""

from zenml import pipeline
import mlflow
from steps.ingestion import ingest_data_from_minio
from steps.preprocessing import preprocess_sequences
from steps.embedding import generate_embeddings
from steps.clustering import cluster_sequences
from steps.training import train_models
from steps.evaluate import evaluate_models
import os
from dotenv import load_dotenv


@pipeline(enable_cache=False)
def training_pipeline(
    # MinIO parameters
    minio_bucket: str = "edna-data",
    minio_archive: str = "16S_ribosomal_RNA.tar.gz",
    
    # Preprocessing parameters
    min_length: int = 100,
    max_length: int = 1500,
    min_gc: float = 0.10,
    max_gc: float = 0.90,
    max_ambiguous_ratio: float = 0.05,
    
    # Embedding parameters
    k_sizes: list = [3, 4, 5],
    embedding_method: str = 'tfidf',
    
    # Clustering parameters
    clustering_methods: list = ['hdbscan', 'kmeans'],
    
    # Training parameters
    num_epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    
    # Output directories
    model_output_dir: str = "./model",
    evaluation_output_dir: str = "./evaluation"
):
    """
    Complete eDNA species classifier training pipeline.
    
    Pipeline steps:
    1. Ingest data from MinIO → Extract sequences from BLAST databases
    2. Preprocess sequences → Quality control and filtering
    3. Generate embeddings → K-mer and compositional features
    4. Cluster sequences → Multiple clustering algorithms
    5. Train models → Taxonomic classifier and novelty detector
    6. Evaluate models → Comprehensive evaluation metrics
    
    Args:
        minio_bucket: MinIO bucket name
        minio_archive: Archive file to download
        min_length: Minimum sequence length
        max_length: Maximum sequence length
        min_gc: Minimum GC content
        max_gc: Maximum GC content
        max_ambiguous_ratio: Maximum ratio of ambiguous bases
        k_sizes: K-mer sizes for embedding
        embedding_method: Vectorization method ('tfidf' or 'count')
        clustering_methods: List of clustering algorithms to apply
        num_epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate
        model_output_dir: Directory to save models
        evaluation_output_dir: Directory to save evaluation results
    """
    
    # Step 1: Data Ingestion - Download from MinIO and extract sequences
    sequences_df = ingest_data_from_minio(
        bucket_name=minio_bucket,
        archive_name=minio_archive
    )
    
    # Step 2: Preprocessing - Quality control and filtering
    filtered_sequences_df = preprocess_sequences(
        sequences_df=sequences_df,
        min_length=min_length,
        max_length=max_length,
        min_gc_content=min_gc,
        max_gc_content=max_gc,
        max_ambiguous_ratio=max_ambiguous_ratio
    )
    
    # Step 3: Embedding - Generate k-mer and compositional features
    kmer_embeddings, comp_embeddings, combined_embeddings = generate_embeddings(
        sequences_df=filtered_sequences_df,
        k_sizes=k_sizes,
        embedding_method=embedding_method
    )
    
    # Step 4: Clustering - Apply multiple clustering algorithms
    cluster_labels, cluster_metrics = cluster_sequences(
        embeddings=combined_embeddings,
        sequences_df=filtered_sequences_df,
        clustering_methods=clustering_methods
    )
    
    # Step 5: Training - Train taxonomic classifier and novelty detector
    # For demo, we'll use cluster labels as classification targets
    # In production, you would use actual taxonomic labels
    import numpy as np
    # Use the first clustering method's labels as targets
    target_labels = cluster_labels[clustering_methods[0]]
    # Filter out noise points (-1) for classification
    non_noise_mask = target_labels != -1
    train_embeddings = combined_embeddings[non_noise_mask]
    train_labels = target_labels[non_noise_mask]
    
    trained_models, training_history = train_models(
        embeddings=train_embeddings,
        labels=train_labels,
        model_output_dir=model_output_dir,
        num_epochs=num_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate
    )
    
    # Step 6: Evaluation - Evaluate trained models
    # For demo, we'll use the same data for evaluation
    # In production, you would have a separate test set
    evaluation_results = evaluate_models(
        trained_models=trained_models,
        training_history=training_history,
        test_embeddings=train_embeddings,
        test_labels=train_labels,
        evaluation_output_dir=evaluation_output_dir
    )
    
    return evaluation_results


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Set MLflow tracking URI
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    
    print("=" * 80)
    print("  🌿 eDNA Species Classifier - ZenML Training Pipeline")
    print("=" * 80)
    print()
    print("Pipeline Configuration:")
    print("  • Data Source: MinIO (16S ribosomal RNA)")
    print("  • Preprocessing: Quality control + filtering")
    print("  • Embedding: K-mer (3,4,5) + compositional features")
    print("  • Clustering: HDBSCAN + K-means")
    print("  • Training: Taxonomic classifier + Novelty detector")
    print("  • Evaluation: Comprehensive metrics + reports")
    print()
    print("  • MLflow Tracking: " + mlflow_tracking_uri)
    print("=" * 80)
    print()
    
    # Run the pipeline
    try:
        pipeline_run = training_pipeline()
        results = pipeline_run.run()
        
        print()
        print("=" * 80)
        print("✅ Pipeline execution completed successfully!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Check MLflow UI for experiment tracking")
        print("  2. Review model checkpoints in ./model/")
        print("  3. View evaluation results in ./evaluation/")
        print()
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ Pipeline execution failed: {e}")
        print("=" * 80)
        raise
