"""
ZenML training pipeline for eDNA sequence classification.
"""

import os
import tarfile
import tempfile
from pathlib import Path
from typing import Tuple, Dict, Any, List
import numpy as np
import pandas as pd
from Bio import SeqIO
import torch
from sklearn.cluster import HDBSCAN
import logging

from zenml import step, pipeline
from zenml.config import DockerSettings

from app.core.config import settings
from app.services.minio_service import minio_service
from app.services.mlflow_service import mlflow_service
from app.services.faiss_indexer import faiss_indexer
from app.services.embedding_service import embedding_service


logger = logging.getLogger(__name__)


# Configure Docker settings for ZenML
docker_settings = DockerSettings(
    requirements=[
        "torch>=2.5.0",
        "transformers>=4.40.0",
        "biopython>=1.84",
        "scikit-learn>=1.5.0",
        "hdbscan>=0.8.38",
        "pandas>=2.2.0",
        "numpy>=1.26.0"
    ]
)


@step
def load_data_step(dataset_id: int, minio_path: str) -> Tuple[List[str], List[str]]:
    """Load and extract sequences from tar.gz dataset."""
    logger.info(f"Loading dataset {dataset_id} from {minio_path}")
    
    # Parse bucket and object name
    parts = minio_path.split("/", 1)
    bucket = parts[0]
    object_name = parts[1]
    
    # Download from MinIO
    with tempfile.TemporaryDirectory() as tmpdir:
        local_file = os.path.join(tmpdir, "dataset.tar.gz")
        minio_service.download_file(object_name, bucket, local_file)
        
        # Extract tar.gz
        extract_dir = os.path.join(tmpdir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with tarfile.open(local_file, "r:gz") as tar:
            tar.extractall(extract_dir)
        
        # Find FASTA/FASTQ files and parse sequences
        sequences = []
        sequence_ids = []
        
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.endswith(('.fasta', '.fa', '.fna', '.fastq', '.fq')):
                    filepath = os.path.join(root, file)
                    
                    # Determine format
                    fmt = 'fastq' if file.endswith(('.fastq', '.fq')) else 'fasta'
                    
                    try:
                        for record in SeqIO.parse(filepath, fmt):
                            sequences.append(str(record.seq))
                            sequence_ids.append(record.id)
                    except Exception as e:
                        logger.error(f"Error parsing {filepath}: {e}")
        
        logger.info(f"Loaded {len(sequences)} sequences")
        return sequences, sequence_ids


@step
def preprocess_step(
    sequences: List[str],
    sequence_ids: List[str],
    min_length: int = 50,
    max_length: int = 1000
) -> Tuple[List[str], List[str]]:
    """Filter and preprocess sequences."""
    logger.info(f"Preprocessing {len(sequences)} sequences")
    
    filtered_seqs = []
    filtered_ids = []
    
    for seq, seq_id in zip(sequences, sequence_ids):
        # Filter by length
        if min_length <= len(seq) <= max_length:
            # Convert to uppercase and remove invalid characters
            clean_seq = seq.upper().replace('N', '')
            
            # Check if valid DNA sequence
            if all(base in 'ATGC' for base in clean_seq):
                filtered_seqs.append(clean_seq)
                filtered_ids.append(seq_id)
    
    logger.info(f"Filtered to {len(filtered_seqs)} valid sequences")
    return filtered_seqs, filtered_ids


@step
def embedding_step(
    sequences: List[str],
    batch_size: int = 32
) -> np.ndarray:
    """Generate embeddings for sequences using PyTorch model."""
    logger.info(f"Generating embeddings for {len(sequences)} sequences")
    
    # Generate embeddings using the embedding service
    embeddings = embedding_service.embed_sequences(sequences, batch_size=batch_size)
    
    logger.info(f"Generated embeddings with shape {embeddings.shape}")
    return embeddings


@step
def clustering_step(
    embeddings: np.ndarray,
    min_cluster_size: int = 5,
    min_samples: int = 3
) -> np.ndarray:
    """Cluster sequences using HDBSCAN."""
    logger.info(f"Clustering {len(embeddings)} embeddings")
    
    # Perform HDBSCAN clustering
    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',
        cluster_selection_epsilon=0.0
    )
    
    cluster_labels = clusterer.fit_predict(embeddings)
    
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = list(cluster_labels).count(-1)
    
    logger.info(f"Found {n_clusters} clusters, {n_noise} noise points")
    
    return cluster_labels


@step
def index_step(
    embeddings: np.ndarray,
    sequence_ids: List[str],
    index_name: str
) -> str:
    """Build and save FAISS index."""
    logger.info(f"Building FAISS index for {len(embeddings)} vectors")
    
    # Create new index
    faiss_indexer.create_index(dimension=embeddings.shape[1])
    
    # Add vectors
    faiss_indexer.add_vectors(embeddings, sequence_ids)
    
    # Save index
    minio_path = faiss_indexer.save_index(index_name)
    
    logger.info(f"Saved FAISS index to {minio_path}")
    return minio_path


@step
def calculate_metrics_step(
    embeddings: np.ndarray,
    cluster_labels: np.ndarray,
    sequences: List[str]
) -> Dict[str, Any]:
    """Calculate biodiversity and clustering metrics."""
    logger.info("Calculating metrics")
    
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = list(cluster_labels).count(-1)
    
    # Shannon diversity index
    from collections import Counter
    cluster_counts = Counter(cluster_labels)
    total = len(cluster_labels)
    
    shannon_index = 0.0
    for count in cluster_counts.values():
        if count > 0:
            proportion = count / total
            shannon_index -= proportion * np.log(proportion)
    
    # Simpson index
    simpson_index = sum((count / total) ** 2 for count in cluster_counts.values())
    
    metrics = {
        "num_sequences": len(sequences),
        "num_clusters": n_clusters,
        "num_noise_points": n_noise,
        "shannon_diversity": float(shannon_index),
        "simpson_diversity": float(simpson_index),
        "avg_sequence_length": float(np.mean([len(s) for s in sequences])),
        "embedding_dim": embeddings.shape[1]
    }
    
    logger.info(f"Metrics: {metrics}")
    return metrics


@step
def mlflow_logging_step(
    metrics: Dict[str, Any],
    hyperparameters: Dict[str, Any],
    run_name: str
) -> str:
    """Log metrics and parameters to MLflow."""
    logger.info("Logging to MLflow")
    
    # Start MLflow run
    run_id = mlflow_service.start_run(run_name=run_name)
    
    # Log parameters
    mlflow_service.log_params(hyperparameters)
    
    # Log metrics
    mlflow_service.log_metrics(metrics)
    
    # End run
    mlflow_service.end_run()
    
    logger.info(f"MLflow run ID: {run_id}")
    return run_id


@step
def save_results_step(
    sequences: List[str],
    sequence_ids: List[str],
    embeddings: np.ndarray,
    cluster_labels: np.ndarray,
    dataset_id: int
) -> str:
    """Save processed results to MinIO."""
    logger.info("Saving results")
    
    # Create DataFrame
    df = pd.DataFrame({
        'sequence_id': sequence_ids,
        'sequence': sequences,
        'cluster_id': cluster_labels.tolist(),
        'sequence_length': [len(s) for s in sequences]
    })
    
    # Save to parquet
    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = os.path.join(tmpdir, f"dataset_{dataset_id}_processed.parquet")
        df.to_parquet(parquet_path, index=False)
        
        # Upload to MinIO
        minio_path = minio_service.upload_file(
            parquet_path,
            f"processed/dataset_{dataset_id}_processed.parquet",
            settings.minio_bucket_processed
        )
    
    logger.info(f"Saved results to {minio_path}")
    return minio_path


@pipeline(enable_cache=False, settings={"docker": docker_settings})
def edna_training_pipeline(
    dataset_id: int,
    minio_path: str,
    model_name: str,
    hyperparameters: Dict[str, Any]
):
    """Complete eDNA training pipeline."""
    
    # Load data
    sequences, sequence_ids = load_data_step(dataset_id, minio_path)
    
    # Preprocess
    clean_seqs, clean_ids = preprocess_step(
        sequences,
        sequence_ids,
        min_length=hyperparameters.get("min_length", 50),
        max_length=hyperparameters.get("max_length", 1000)
    )
    
    # Generate embeddings
    embeddings = embedding_step(
        clean_seqs,
        batch_size=hyperparameters.get("batch_size", 32)
    )
    
    # Cluster sequences
    clusters = clustering_step(
        embeddings,
        min_cluster_size=hyperparameters.get("min_cluster_size", 5),
        min_samples=hyperparameters.get("min_samples", 3)
    )
    
    # Build FAISS index
    index_name = f"model_{model_name}_{dataset_id}"
    index_path = index_step(embeddings, clean_ids, index_name)
    
    # Calculate metrics
    metrics = calculate_metrics_step(embeddings, clusters, clean_seqs)
    
    # Log to MLflow
    run_id = mlflow_logging_step(
        metrics,
        hyperparameters,
        run_name=f"training_{dataset_id}_{model_name}"
    )
    
    # Save results
    results_path = save_results_step(
        clean_seqs,
        clean_ids,
        embeddings,
        clusters,
        dataset_id
    )
    
    return run_id, metrics, results_path
