"""
Custom training workflow without ZenML dependencies.
This replaces the ZenML pipeline with plain Python functions for better reliability.

The original ZenML pipeline is preserved in training_pipeline.py for reference.
"""

import logging
import os
import tempfile
import tarfile
import subprocess
import shutil
from typing import List, Tuple, Dict, Any
from collections import Counter

import numpy as np
import pandas as pd
from Bio import SeqIO
import hdbscan

from app.core.config import settings
from app.services.minio_service import minio_service
from app.services.embedding_service import embedding_service
from app.services.faiss_indexer import faiss_indexer
from app.services.mlflow_service import mlflow_service


logger = logging.getLogger(__name__)


class TrainingWorkflow:
    """
    Custom training workflow for eDNA sequence analysis.
    Implements the same pipeline logic as ZenML version but without decorators.
    """
    
    def __init__(self):
        self.logger = logger
    
    def load_data(
        self,
        dataset_id: int,
        minio_path: str
    ) -> Tuple[List[str], List[str]]:
        """
        Load and extract sequences from MinIO (handles both archives and direct files).
        Automatically converts BLAST databases to FASTA format if detected.
        
        Args:
            dataset_id: Dataset ID for logging
            minio_path: Path to file in MinIO (can be archive or direct sequence file)
            
        Returns:
            Tuple of (sequences, sequence_ids)
        """
        self.logger.info(f"Loading dataset {dataset_id} from {minio_path}")
        
        # Download from MinIO
        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract just the object name from the full minio_path
            object_name = minio_path.replace(f"{settings.minio_bucket_raw}/", "")
            
            # Keep original filename to determine file type
            original_filename = os.path.basename(object_name)
            local_path = os.path.join(tmpdir, original_filename)
            
            # Download file - correct order: object_name, bucket, file_path
            minio_service.download_file(
                object_name,
                settings.minio_bucket_raw,
                local_path
            )
            
            # Check if it's a direct sequence file or an archive
            extract_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            if original_filename.endswith(('.fasta', '.fa', '.fna', '.fastq', '.fq', '.txt')):
                # Direct sequence file - just copy it to extract_dir
                self.logger.info(f"Processing direct sequence file: {original_filename}")
                import shutil
                shutil.copy(local_path, os.path.join(extract_dir, original_filename))
            elif original_filename.endswith(('.tar.gz', '.tgz')):
                # Tar.gz archive
                self.logger.info(f"Extracting tar.gz archive: {original_filename}")
                with tarfile.open(local_path, "r:gz") as tar:
                    tar.extractall(extract_dir)
            elif original_filename.endswith('.zip'):
                # Zip archive
                self.logger.info(f"Extracting zip archive: {original_filename}")
                import zipfile
                with zipfile.ZipFile(local_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif original_filename.endswith('.gz'):
                # Single gzip file
                self.logger.info(f"Extracting gzip file: {original_filename}")
                import gzip
                import shutil
                with gzip.open(local_path, 'rb') as f_in:
                    extracted_filename = original_filename[:-3]  # Remove .gz extension
                    with open(os.path.join(extract_dir, extracted_filename), 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                raise ValueError(f"Unsupported file format: {original_filename}")
            
            # Parse sequences
            sequences = []
            sequence_ids = []
            
            # Look for sequence files with various extensions
            sequence_extensions = ['.fasta', '.fa', '.fastq', '.fq', '.fna', '.ffn', '.faa', '.frn']
            
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    # Check if it's a sequence file
                    file_lower = file.lower()
                    if any(file_lower.endswith(ext) for ext in sequence_extensions):
                        filepath = os.path.join(root, file)
                        
                        # Determine format
                        fmt = 'fasta' if any(file_lower.endswith(ext) for ext in ['.fasta', '.fa', '.fna', '.ffn', '.faa', '.frn']) else 'fastq'
                        
                        self.logger.info(f"Parsing sequence file: {file} (format: {fmt})")
                        
                        # Parse sequences
                        try:
                            for record in SeqIO.parse(filepath, fmt):
                                sequences.append(str(record.seq))
                                sequence_ids.append(record.id)
                        except Exception as e:
                            self.logger.warning(f"Error parsing {filepath}: {e}")
                            # Try the other format if first fails
                            try:
                                alt_fmt = 'fastq' if fmt == 'fasta' else 'fasta'
                                self.logger.info(f"Retrying with format: {alt_fmt}")
                                for record in SeqIO.parse(filepath, alt_fmt):
                                    sequences.append(str(record.seq))
                                    sequence_ids.append(record.id)
                            except Exception as e2:
                                self.logger.error(f"Failed to parse {filepath} with both formats: {e2}")
            
            # If no sequences found, check if this is a BLAST database and convert
            if len(sequences) == 0:
                self.logger.warning("No FASTA/FASTQ files found in archive")
                self.logger.info("Checking for BLAST database files...")
                
                # Look for BLAST database files
                blast_db_files = {}
                for file in os.listdir(extract_dir):
                    if file.endswith(('.nhr', '.nin', '.nsq')):
                        # Extract base name (e.g., "16S_ribosomal_RNA" from "16S_ribosomal_RNA.nhr")
                        base_name = file.rsplit('.', 1)[0]
                        if base_name not in blast_db_files:
                            blast_db_files[base_name] = []
                        blast_db_files[base_name].append(file)
                
                if blast_db_files:
                    self.logger.info(f"🔄 Detected BLAST database files. Auto-converting to FASTA...")
                    
                    # Try to convert using blastdbcmd
                    for db_name, files in blast_db_files.items():
                        self.logger.info(f"Converting BLAST database: {db_name}")
                        
                        db_path = os.path.join(extract_dir, db_name)
                        fasta_output = os.path.join(extract_dir, f"{db_name}.fasta")
                        
                        try:
                            # Run blastdbcmd to extract sequences
                            cmd = [
                                "blastdbcmd",
                                "-db", db_path,
                                "-entry", "all",
                                "-out", fasta_output
                            ]
                            
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=300  # 5 minute timeout
                            )
                            
                            if result.returncode == 0:
                                self.logger.info(f"✅ Successfully converted BLAST database to FASTA")
                                
                                # Parse the converted FASTA file
                                for record in SeqIO.parse(fasta_output, 'fasta'):
                                    sequences.append(str(record.seq))
                                    sequence_ids.append(record.id)
                                
                                self.logger.info(f"Extracted {len(sequences)} sequences from BLAST database")
                                
                                # Clean up BLAST database files (keep only FASTA)
                                self.logger.info("Cleaning up BLAST database files...")
                                for file in os.listdir(extract_dir):
                                    if not file.endswith('.fasta') and file != os.path.basename(local_path):
                                        file_path = os.path.join(extract_dir, file)
                                        try:
                                            if os.path.isfile(file_path):
                                                os.remove(file_path)
                                            elif os.path.isdir(file_path):
                                                shutil.rmtree(file_path)
                                        except Exception as e:
                                            self.logger.warning(f"Could not remove {file}: {e}")
                                
                                self.logger.info("✅ Cleanup complete - kept FASTA file only")
                                break  # Successfully converted
                            else:
                                self.logger.error(f"blastdbcmd failed: {result.stderr}")
                                
                        except FileNotFoundError:
                            self.logger.error(
                                "❌ blastdbcmd not found. Please install BLAST+ toolkit:\n"
                                "   Ubuntu/Debian: sudo apt-get install ncbi-blast+\n"
                                "   macOS: brew install blast\n"
                                "   Or download from: https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/"
                            )
                            raise ValueError(
                                "BLAST database detected but blastdbcmd not available. "
                                "Please install BLAST+ toolkit or upload FASTA files directly."
                            )
                        except subprocess.TimeoutExpired:
                            self.logger.error("blastdbcmd timed out after 5 minutes")
                            raise ValueError("BLAST database conversion timed out. Please upload FASTA files directly.")
                        except Exception as e:
                            self.logger.error(f"Error converting BLAST database: {e}")
                            raise ValueError(f"Failed to convert BLAST database: {e}")
                
                # If still no sequences after conversion attempt
                if len(sequences) == 0:
                    # List what files were found
                    all_files = []
                    for root, dirs, files in os.walk(extract_dir):
                        for file in files:
                            all_files.append(file)
                    
                    self.logger.error(f"No sequence files found. Files in archive: {all_files[:20]}")
                    raise ValueError(
                        f"No sequence files found in archive. "
                        f"Expected FASTA/FASTQ files but found: {', '.join(all_files[:10])}"
                    )
            
            self.logger.info(f"✅ Loaded {len(sequences)} sequences from archive")
            return sequences, sequence_ids
    
    def preprocess(
        self,
        sequences: List[str],
        sequence_ids: List[str],
        min_length: int = 50,
        max_length: int = 1000
    ) -> Tuple[List[str], List[str]]:
        """
        Preprocess sequences: filter by length and validate DNA content.
        
        Args:
            sequences: List of sequence strings
            sequence_ids: List of sequence IDs
            min_length: Minimum sequence length
            max_length: Maximum sequence length
            
        Returns:
            Tuple of (filtered_sequences, filtered_ids)
        """
        self.logger.info(f"Preprocessing {len(sequences)} sequences")
        
        if len(sequences) == 0:
            raise ValueError("No sequences to preprocess. Cannot proceed with empty dataset.")
        
        filtered_seqs = []
        filtered_ids = []
        
        for seq, seq_id in zip(sequences, sequence_ids):
            # Skip empty sequences
            if not seq or len(seq) == 0:
                continue
                
            # Filter by length
            if min_length <= len(seq) <= max_length:
                # Convert to uppercase and remove invalid characters
                clean_seq = seq.upper().replace('N', '')
                
                # Check if valid DNA sequence (at least 80% ATGC)
                if len(clean_seq) > 0:
                    valid_bases = sum(1 for base in clean_seq if base in 'ATGC')
                    if valid_bases / len(clean_seq) >= 0.8:
                        filtered_seqs.append(clean_seq)
                        filtered_ids.append(seq_id)
        
        self.logger.info(f"Filtered to {len(filtered_seqs)} valid sequences")
        
        if len(filtered_seqs) == 0:
            raise ValueError(
                f"No valid sequences after preprocessing. "
                f"Original count: {len(sequences)}. "
                f"Check sequence length requirements (min: {min_length}, max: {max_length}) "
                f"and DNA content validity."
            )
        
        return filtered_seqs, filtered_ids
    
    def generate_embeddings(
        self,
        sequences: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Generate embeddings for sequences using PyTorch model.
        
        Args:
            sequences: List of sequence strings
            batch_size: Batch size for embedding generation
            
        Returns:
            NumPy array of embeddings
        """
        self.logger.info(f"Generating embeddings for {len(sequences)} sequences")
        
        # Generate embeddings using the embedding service
        embeddings = embedding_service.embed_sequences(sequences, batch_size=batch_size)
        
        self.logger.info(f"Generated embeddings with shape {embeddings.shape}")
        return embeddings
    
    def cluster_sequences(
        self,
        embeddings: np.ndarray,
        min_cluster_size: int = 5,
        min_samples: int = 3
    ) -> np.ndarray:
        """
        Cluster sequences using HDBSCAN.
        
        Args:
            embeddings: NumPy array of embeddings
            min_cluster_size: Minimum cluster size for HDBSCAN
            min_samples: Minimum samples for HDBSCAN
            
        Returns:
            NumPy array of cluster labels
        """
        self.logger.info(f"Clustering {len(embeddings)} embeddings")
        
        # Validate embeddings shape
        if len(embeddings.shape) != 2:
            raise ValueError(
                f"Embeddings must be 2D array, got shape {embeddings.shape}. "
                f"Expected (n_samples, n_features)."
            )
        
        if embeddings.shape[0] == 0:
            raise ValueError("Cannot cluster empty embeddings array.")
        
        # Adjust min_cluster_size if dataset is small
        effective_min_cluster_size = min(min_cluster_size, max(2, len(embeddings) // 10))
        effective_min_samples = min(min_samples, max(1, effective_min_cluster_size - 1))
        
        if effective_min_cluster_size != min_cluster_size:
            self.logger.info(
                f"Adjusted min_cluster_size from {min_cluster_size} to {effective_min_cluster_size} "
                f"for small dataset (n={len(embeddings)})"
            )
        
        # Perform HDBSCAN clustering
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=effective_min_cluster_size,
            min_samples=effective_min_samples,
            metric='euclidean',
            cluster_selection_epsilon=0.0
        )
        
        cluster_labels = clusterer.fit_predict(embeddings)
        
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        self.logger.info(f"Found {n_clusters} clusters, {n_noise} noise points")
        
        return cluster_labels
    
    def build_index(
        self,
        embeddings: np.ndarray,
        sequence_ids: List[str],
        index_name: str
    ) -> str:
        """
        Build and save FAISS index.
        
        Args:
            embeddings: NumPy array of embeddings
            sequence_ids: List of sequence IDs
            index_name: Name for the index
            
        Returns:
            MinIO path to saved index
        """
        self.logger.info(f"Building FAISS index for {len(embeddings)} vectors")
        
        # Create new index
        faiss_indexer.create_index(dimension=embeddings.shape[1])
        
        # Add vectors
        faiss_indexer.add_vectors(embeddings, sequence_ids)
        
        # Save index
        minio_path = faiss_indexer.save_index(index_name)
        
        self.logger.info(f"Saved FAISS index to {minio_path}")
        return minio_path
    
    def calculate_metrics(
        self,
        embeddings: np.ndarray,
        cluster_labels: np.ndarray,
        sequences: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate biodiversity and clustering metrics.
        
        Args:
            embeddings: NumPy array of embeddings
            cluster_labels: NumPy array of cluster labels
            sequences: List of sequence strings
            
        Returns:
            Dictionary of metrics
        """
        self.logger.info("Calculating metrics")
        
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        # Shannon diversity index
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
        
        self.logger.info(f"Metrics: {metrics}")
        return metrics
    
    def log_to_mlflow(
        self,
        metrics: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        run_name: str
    ) -> str:
        """
        Log metrics and parameters to MLflow.
        
        Args:
            metrics: Dictionary of metrics
            hyperparameters: Dictionary of hyperparameters
            run_name: Name for the MLflow run
            
        Returns:
            MLflow run ID
        """
        self.logger.info("Logging to MLflow")
        
        # Start MLflow run
        run_id = mlflow_service.start_run(run_name=run_name)
        
        # Log parameters
        mlflow_service.log_params(hyperparameters)
        
        # Log metrics
        mlflow_service.log_metrics(metrics)
        
        # End run
        mlflow_service.end_run()
        
        self.logger.info(f"MLflow run ID: {run_id}")
        return run_id
    
    def save_results(
        self,
        sequences: List[str],
        sequence_ids: List[str],
        embeddings: np.ndarray,
        cluster_labels: np.ndarray,
        dataset_id: int
    ) -> str:
        """
        Save processed results to MinIO.
        
        Args:
            sequences: List of sequence strings
            sequence_ids: List of sequence IDs
            embeddings: NumPy array of embeddings
            cluster_labels: NumPy array of cluster labels
            dataset_id: Dataset ID
            
        Returns:
            MinIO path to saved results
        """
        self.logger.info("Saving results")
        
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
        
        self.logger.info(f"Saved results to {minio_path}")
        return minio_path
    
    def run_training_pipeline(
        self,
        dataset_id: int,
        minio_path: str,
        model_name: str,
        hyperparameters: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any], str]:
        """
        Run the complete eDNA training workflow.
        
        This is the main entry point that orchestrates all pipeline steps.
        
        Args:
            dataset_id: Dataset ID
            minio_path: Path to dataset in MinIO
            model_name: Name for the model/index
            hyperparameters: Dictionary of hyperparameters
            
        Returns:
            Tuple of (mlflow_run_id, metrics, results_path)
        """
        self.logger.info(f"Starting training workflow for dataset {dataset_id}")
        
        try:
            # Step 1: Load data
            sequences, sequence_ids = self.load_data(dataset_id, minio_path)
            
            # Step 2: Preprocess
            clean_seqs, clean_ids = self.preprocess(
                sequences,
                sequence_ids,
                min_length=hyperparameters.get("min_length", 50),
                max_length=hyperparameters.get("max_length", 1000)
            )
            
            # Step 3: Generate embeddings
            embeddings = self.generate_embeddings(
                clean_seqs,
                batch_size=hyperparameters.get("batch_size", 32)
            )
            
            # Step 4: Cluster sequences
            clusters = self.cluster_sequences(
                embeddings,
                min_cluster_size=hyperparameters.get("min_cluster_size", 5),
                min_samples=hyperparameters.get("min_samples", 3)
            )
            
            # Step 5: Build FAISS index
            index_name = f"model_{model_name}_{dataset_id}"
            index_path = self.build_index(embeddings, clean_ids, index_name)
            
            # Step 6: Calculate metrics
            metrics = self.calculate_metrics(embeddings, clusters, clean_seqs)
            
            # Step 7: Log to MLflow
            run_id = self.log_to_mlflow(
                metrics,
                hyperparameters,
                run_name=f"training_{dataset_id}_{model_name}"
            )
            
            # Step 8: Save results
            results_path = self.save_results(
                clean_seqs,
                clean_ids,
                embeddings,
                clusters,
                dataset_id
            )
            
            self.logger.info(f"Training workflow completed successfully for dataset {dataset_id}")
            self.logger.info(f"  - MLflow run ID: {run_id}")
            self.logger.info(f"  - FAISS index: {index_path}")
            self.logger.info(f"  - Results: {results_path}")
            self.logger.info(f"  - Metrics: {metrics}")
            
            return run_id, metrics, results_path
            
        except Exception as e:
            self.logger.error(f"Training workflow failed for dataset {dataset_id}: {e}")
            raise


# Global instance
training_workflow = TrainingWorkflow()
