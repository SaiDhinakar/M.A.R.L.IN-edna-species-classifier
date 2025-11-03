"""
Model inference service for DNA sequence classification.
"""

import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging

from app.core.config import settings
from app.services.embedding_service import embedding_service
from app.services.faiss_indexer import FAISSIndexer
from app.services.redis_service import redis_service
from app.models.schemas import InferenceResponse, SimilarSequence
from app.utils.species_parser import parse_species_from_header, build_species_mapping_from_fasta


logger = logging.getLogger(__name__)


class InferenceService:
    """Service for DNA sequence inference and classification."""
    
    def __init__(self):
        self.current_model_version: Optional[str] = None
        self.faiss_index: Optional[FAISSIndexer] = None
        self.cluster_metadata: Dict[str, Dict[str, Any]] = {}  # seq_id -> {cluster_id, taxonomy}
        self.species_mapping: Dict[str, str] = {}  # accession -> species_name
    
    def _compute_sequence_hash(self, sequence: str) -> str:
        """Compute hash for sequence."""
        return hashlib.sha256(sequence.encode()).hexdigest()
    
    def load_model(self, model_version: str, index_name: str, dataset_id: Optional[int] = None):
        """Load model and FAISS index."""
        try:
            # Initialize FAISS indexer
            self.faiss_index = FAISSIndexer()
            
            # Load index from MinIO
            self.faiss_index.load_index(index_name)
            
            # Load cluster metadata from processed data if dataset_id provided
            if dataset_id:
                self._load_cluster_metadata(dataset_id)
            
            self.current_model_version = model_version
            logger.info(f"Loaded model version {model_version} with index {index_name}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def _load_cluster_metadata(self, dataset_id: int):
        """Load cluster metadata from processed parquet file and species names from FASTA."""
        try:
            import pandas as pd
            import tempfile
            import os
            from app.services.minio_service import minio_service
            from sqlalchemy.orm import Session
            from app.models.database_models import Dataset
            from app.core.database import SessionLocal
            
            # Download processed data from MinIO
            parquet_path = f"processed/dataset_{dataset_id}_processed.parquet"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                local_path = os.path.join(tmpdir, "processed.parquet")
                
                # Download from MinIO
                minio_service.download_file(
                    parquet_path,
                    settings.minio_bucket_processed,
                    local_path
                )
                
                # Load parquet
                df = pd.read_parquet(local_path)
                
                # Build metadata dictionary: sequence_id -> {cluster_id, taxonomy}
                for _, row in df.iterrows():
                    seq_id = row['sequence_id']
                    cluster_id = row['cluster_id']
                    
                    # Extract taxonomy from sequence_id (e.g., "NR_114010.1")
                    # For now, use the accession number as taxonomy placeholder
                    taxonomy = seq_id.split('.')[0] if '.' in seq_id else seq_id
                    
                    self.cluster_metadata[seq_id] = {
                        'cluster_id': int(cluster_id) if cluster_id >= 0 else None,
                        'taxonomy': taxonomy
                    }
                
                logger.info(f"Loaded metadata for {len(self.cluster_metadata)} sequences from dataset {dataset_id}")
                
                # Load species names from local FASTA file
                try:
                    import os as os_module
                    from pathlib import Path
                    
                    # Get absolute path to backend directory
                    backend_dir = Path(__file__).parent.parent.parent
                    
                    # Check for local FASTA file (from BLAST extraction or direct upload)
                    local_fasta_paths = [
                        backend_dir / 'data' / 'archives' / '16S_ribosomal_RNA.fasta',
                        backend_dir / 'data' / 'archives' / '18S_fungal_sequences.fasta',
                        backend_dir / 'data' / 'archives' / '28S_fungal_sequences.fasta',
                    ]
                    
                    species_loaded = False
                    for fasta_path in local_fasta_paths:
                        if fasta_path.exists():
                            # Build species mapping from FASTA headers
                            logger.info(f"Loading species names from {fasta_path}")
                            self.species_mapping = build_species_mapping_from_fasta(str(fasta_path))
                            logger.info(f"Loaded species names for {len(self.species_mapping)} sequences from {fasta_path.name}")
                            species_loaded = True
                            break
                    
                    if not species_loaded:
                        logger.warning(f"No local FASTA file found for species name extraction. Checked: {[str(p) for p in local_fasta_paths]}")
                    
                except Exception as e:
                    logger.warning(f"Could not load species names: {e}")
                    # Continue without species names
                
        except Exception as e:
            logger.warning(f"Could not load cluster metadata: {e}")
            # Continue without metadata - inference will still work
    
    def _get_from_cache(self, sequence_hash: str) -> Optional[Dict[str, Any]]:
        """Get inference result from cache."""
        cache_key = f"inference:{sequence_hash}"
        return redis_service.get_json(cache_key)
    
    def _save_to_cache(self, sequence_hash: str, result: Dict[str, Any]):
        """Save inference result to cache."""
        cache_key = f"inference:{sequence_hash}"
        redis_service.set_json(cache_key, result, expire=settings.redis_cache_expire)
    
    def infer(
        self,
        sequence: str,
        top_k: int = 5
    ) -> InferenceResponse:
        """Classify a DNA sequence."""
        start_time = time.time()
        
        # Compute sequence hash
        sequence_hash = self._compute_sequence_hash(sequence)
        
        # Check cache
        cached_result = self._get_from_cache(sequence_hash)
        if cached_result:
            logger.info(f"Retrieved result from cache for sequence {sequence_hash[:8]}")
            cached_result["processing_time"] = time.time() - start_time
            return InferenceResponse(**cached_result)
        
        # Ensure model is loaded
        if self.faiss_index is None or self.faiss_index.index is None:
            raise ValueError("Model not loaded. Please load a model first.")
        
        # Generate embedding
        embedding = embedding_service.embed_sequence(sequence)
        
        # Search for similar sequences
        similar_ids, similarities = self.faiss_index.search(
            embedding,
            k=top_k
        )
        
        # Build similar sequences list
        similar_sequences = []
        cluster_predictions = []
        
        for seq_id, similarity in zip(similar_ids, similarities):
            # Get metadata for this sequence
            metadata = self.cluster_metadata.get(seq_id, {})
            cluster_id = metadata.get('cluster_id')
            taxonomy = metadata.get('taxonomy')
            
            # Get species name from mapping
            species_name = self.species_mapping.get(seq_id)
            
            similar_seq = SimilarSequence(
                sequence_id=seq_id,
                similarity=float(similarity),
                cluster_id=cluster_id,
                taxonomy=taxonomy,
                species_name=species_name
            )
            similar_sequences.append(similar_seq)
            
            # Collect cluster predictions for voting
            # Use cosine similarity threshold (closer to 1.0 is better, closer to 0 or negative is worse)
            # Since we're using L2 distance, smaller values mean more similar
            # Normalize to 0-1 range where 1 is most similar
            normalized_sim = 1.0 / (1.0 + abs(similarity))
            
            if cluster_id is not None and normalized_sim > 0.5:  # Threshold for considering cluster
                cluster_predictions.append((cluster_id, normalized_sim))
        
        # Determine most likely cluster by voting
        predicted_cluster = None
        confidence = 0.0
        predicted_taxonomy = None
        
        predicted_species = None
        
        if cluster_predictions:
            # Count votes per cluster, weighted by similarity
            from collections import defaultdict
            cluster_votes = defaultdict(float)
            
            for cluster_id, sim in cluster_predictions:
                cluster_votes[cluster_id] += sim
            
            # Get cluster with highest vote
            if cluster_votes:
                predicted_cluster = max(cluster_votes.items(), key=lambda x: x[1])[0]
                confidence = cluster_votes[predicted_cluster] / len(cluster_predictions)
                
                # Get taxonomy and species from most similar sequence in predicted cluster
                for seq in similar_sequences:
                    if seq.cluster_id == predicted_cluster:
                        predicted_taxonomy = seq.taxonomy
                        predicted_species = seq.species_name
                        break
        
        # Build response
        response = InferenceResponse(
            sequence_hash=sequence_hash,
            cluster_id=predicted_cluster,
            predicted_taxonomy=predicted_taxonomy,
            predicted_species=predicted_species,
            confidence=confidence if confidence > 0 else None,
            similar_sequences=similar_sequences,
            processing_time=time.time() - start_time
        )
        
        # Cache result
        self._save_to_cache(sequence_hash, response.model_dump())
        
        logger.info(f"Inference completed in {response.processing_time:.3f}s")
        return response
    
    def batch_infer(
        self,
        sequences: List[str],
        top_k: int = 5
    ) -> List[InferenceResponse]:
        """Classify multiple DNA sequences."""
        results = []
        
        for sequence in sequences:
            try:
                result = self.infer(sequence, top_k)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch inference: {e}")
                # Add error placeholder
                results.append(None)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model."""
        if self.faiss_index is None:
            return {"status": "no_model_loaded"}
        
        stats = self.faiss_index.get_stats()
        
        return {
            "status": "loaded",
            "version": self.current_model_version,
            "index_stats": stats
        }


# Global inference service instance
inference_service = InferenceService()
