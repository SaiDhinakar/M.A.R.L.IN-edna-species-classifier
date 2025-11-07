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
    """Load and extract sequences from dataset (archive or raw FASTA/FASTQ)."""
    logger.info(f"Loading dataset {dataset_id} from {minio_path}")
    
    # Parse bucket and object name
    parts = minio_path.split("/", 1)
    bucket = parts[0]
    object_name = parts[1]
    
    sequences = []
    sequence_ids = []
    
    # Download from MinIO
    with tempfile.TemporaryDirectory() as tmpdir:
        # Determine file type from object name
        filename = os.path.basename(object_name)
        local_file = os.path.join(tmpdir, filename)
        minio_service.download_file(object_name, bucket, local_file)
        
        # Check if it's a direct sequence file or an archive
        if filename.endswith(('.fasta', '.fa', '.fna', '.fastq', '.fq', '.txt')):
            # Direct sequence file - parse it directly
            fmt = 'fastq' if filename.endswith(('.fastq', '.fq')) else 'fasta'
            try:
                for record in SeqIO.parse(local_file, fmt):
                    sequences.append(str(record.seq))
                    sequence_ids.append(record.id)
                logger.info(f"Loaded {len(sequences)} sequences from direct file")
            except Exception as e:
                logger.error(f"Error parsing {filename}: {e}")
                raise
        else:
            # Archive file - extract and parse
            extract_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            try:
                # Try to extract as tar.gz
                if filename.endswith(('.tar.gz', '.tgz')):
                    with tarfile.open(local_file, "r:gz") as tar:
                        tar.extractall(extract_dir)
                elif filename.endswith('.zip'):
                    import zipfile
                    with zipfile.ZipFile(local_file, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                elif filename.endswith('.gz'):
                    import gzip
                    import shutil
                    with gzip.open(local_file, 'rb') as f_in:
                        extracted_file = os.path.join(extract_dir, filename[:-3])
                        with open(extracted_file, 'wb') as f_out:
                            shutil.copyfile(f_in, f_out)
                else:
                    raise ValueError(f"Unsupported archive format: {filename}")
                
                # Find and parse all FASTA/FASTQ files
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith(('.fasta', '.fa', '.fna', '.fastq', '.fq')):
                            filepath = os.path.join(root, file)
                            fmt = 'fastq' if file.endswith(('.fastq', '.fq')) else 'fasta'
                            
                            try:
                                for record in SeqIO.parse(filepath, fmt):
                                    sequences.append(str(record.seq))
                                    sequence_ids.append(record.id)
                            except Exception as e:
                                logger.error(f"Error parsing {filepath}: {e}")
                
                logger.info(f"Loaded {len(sequences)} sequences from archive")
            except Exception as e:
                logger.error(f"Error extracting archive {filename}: {e}")
                raise
        
        if len(sequences) == 0:
            raise ValueError("No valid sequences found in the uploaded file")
        
        logger.info(f"Successfully loaded {len(sequences)} sequences")
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
    sequences: List[str],
    min_cluster_size: int = 5
) -> Dict[str, Any]:
    """Calculate comprehensive model evaluation metrics."""
    logger.info("=" * 80)
    logger.info("Calculating comprehensive model evaluation metrics")
    logger.info("=" * 80)
    
    from app.utils.model_evaluator import evaluate_model
    
    # Calculate sequence lengths
    sequence_lengths = np.array([len(s) for s in sequences])
    
    # Perform comprehensive evaluation
    evaluation = evaluate_model(
        embeddings=embeddings,
        cluster_labels=cluster_labels,
        sequence_lengths=sequence_lengths,
        true_labels=None,  # No ground truth available for unsupervised clustering
        min_cluster_size=min_cluster_size
    )
    
    # Extract key metrics for backward compatibility
    clustering_metrics = evaluation.get('clustering', {})
    diversity_metrics = evaluation.get('diversity', {})
    
    # Combine into flat metrics dict for MLflow/DB storage
    metrics = {
        # Basic stats
        "num_sequences": int(evaluation['n_samples']),
        "embedding_dim": int(evaluation['embedding_dim']),
        
        # Clustering metrics
        "num_clusters": clustering_metrics.get('n_clusters', 0),
        "num_noise_points": clustering_metrics.get('n_noise_points', 0),
        "noise_ratio": clustering_metrics.get('noise_ratio', 0.0),
        "clustered_ratio": clustering_metrics.get('clustered_ratio', 0.0),
        
        # Cluster size statistics
        "min_cluster_size_actual": clustering_metrics.get('min_cluster_size_actual'),
        "max_cluster_size": clustering_metrics.get('max_cluster_size'),
        "avg_cluster_size": clustering_metrics.get('avg_cluster_size'),
        "median_cluster_size": clustering_metrics.get('median_cluster_size'),
        
        # Quality metrics
        "silhouette_score": clustering_metrics.get('silhouette_score'),
        "davies_bouldin_index": clustering_metrics.get('davies_bouldin_index'),
        "calinski_harabasz_score": clustering_metrics.get('calinski_harabasz_score'),
        
        # Diversity metrics
        "shannon_diversity": diversity_metrics.get('shannon_diversity', 0.0),
        "simpson_diversity": diversity_metrics.get('simpson_diversity', 0.0),
        "effective_n_clusters": diversity_metrics.get('effective_n_clusters'),
        
        # Sequence statistics
        "avg_sequence_length": diversity_metrics.get('avg_sequence_length', 0.0),
        "min_sequence_length": diversity_metrics.get('min_sequence_length'),
        "max_sequence_length": diversity_metrics.get('max_sequence_length'),
        
        # Overall quality
        "overall_quality_score": evaluation.get('overall_quality_score', 0.0),
        
        # Store full evaluation for detailed inspection
        "detailed_evaluation": evaluation
    }
    
    logger.info("=" * 80)
    logger.info("Metrics Summary:")
    logger.info(f"  Sequences: {metrics['num_sequences']}")
    logger.info(f"  Clusters: {metrics['num_clusters']} (+ {metrics['num_noise_points']} noise)")
    logger.info(f"  Silhouette Score: {metrics['silhouette_score']}")
    logger.info(f"  Davies-Bouldin Index: {metrics['davies_bouldin_index']}")
    logger.info(f"  Shannon Diversity: {metrics['shannon_diversity']:.3f}")
    logger.info(f"  Overall Quality: {metrics['overall_quality_score']:.2f}/10")
    logger.info("=" * 80)
    
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
    metrics = calculate_metrics_step(
        embeddings,
        clusters,
        clean_seqs,
        min_cluster_size=hyperparameters.get("min_cluster_size", 5)
    )
    
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
