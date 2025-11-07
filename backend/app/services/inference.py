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
from app.utils.logger import LoggerSetup


# Custom logger setup
logger = LoggerSetup.get_logger(
    name="inference_service",
    level=logging.DEBUG,
    log_file="logs/inference.log",
    max_bytes=5 * 1024 * 1024,  # 5MB
    backup_count=3,
    console_output=True
)


class InferenceService:
    """Service for DNA sequence inference and classification."""
    
    def __init__(self):
        self.current_model_version: Optional[str] = None
        self.faiss_index: Optional[FAISSIndexer] = None
        self.cluster_metadata: Dict[str, Dict[str, Any]] = {}  # seq_id -> {cluster_id, taxonomy}
        self.species_mapping: Dict[str, str] = {}  # accession -> species_name
        self.embeddings: Optional[np.ndarray] = None  # Loaded embeddings from MinIO
    
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
            
            # Load cluster metadata and embeddings from processed data if dataset_id provided
            if dataset_id:
                self._load_cluster_metadata(dataset_id)
                self._load_embeddings(dataset_id)
            
            self.current_model_version = model_version
            logger.info(f"Loaded model version {model_version} with index {index_name}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            raise
    
    def _load_embeddings(self, dataset_id: int):
        """Load embeddings from MinIO."""
        try:
            import tempfile
            import os
            from app.services.minio_service import minio_service
            
            # Download embeddings from MinIO
            embeddings_path = f"processed/dataset_{dataset_id}_embeddings.npy"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                local_path = os.path.join(tmpdir, "embeddings.npy")
                
                # Download from MinIO
                minio_service.download_file(
                    embeddings_path,
                    settings.minio_bucket_processed,
                    local_path
                )
                
                # Load embeddings
                self.embeddings = np.load(local_path)
                
                logger.info(f"Loaded embeddings with shape {self.embeddings.shape} from dataset {dataset_id}")
                
        except Exception as e:
            logger.warning(f"Could not load embeddings: {e}", exc_info=True)
            self.embeddings = None
    
    def _load_cluster_metadata(self, dataset_id: int):
        """Load cluster metadata from processed parquet file and species names from FASTA."""
        try:
            import pandas as pd
            import tempfile
            import os
            from app.services.minio_service import minio_service
            from sqlalchemy.orm import Session
            from app.models.database_models import Dataset
            from app.database.session import SessionLocal
            
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
                        # Keep -1 for noise points instead of converting to None
                        # This allows us to distinguish between "noise" and "not clustered"
                        'cluster_id': int(cluster_id),
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
                    logger.warning(f"Could not load species names: {e}", exc_info=True)
                    # Continue without species names
                
        except Exception as e:
            logger.warning(f"Could not load cluster metadata: {e}", exc_info=True)
            # Continue without metadata - inference will still work
    
    def _get_species_name_for_sequence(self, seq_id: str) -> Optional[str]:
        """
        Get species name for a sequence ID, trying multiple approaches:
        1. Direct lookup in species_mapping
        2. Try without version number (e.g., NG_065604.1 -> NG_065604)
        3. Try converting NG_ to NR_ prefix (Gene -> RNA record)
        4. Extract from the sequence ID itself if it contains species info
        
        Args:
            seq_id: Sequence accession ID (e.g., "NG_065604.1" or "NR_118889.1")
            
        Returns:
            Species name if found, None otherwise
        """
        # Try direct lookup
        if seq_id in self.species_mapping:
            return self.species_mapping[seq_id]
        
        # Try without version number
        base_id = seq_id.split('.')[0]
        if base_id in self.species_mapping:
            return self.species_mapping[base_id]
        
        # Try with version .1
        if '.' not in seq_id:
            versioned_id = f"{seq_id}.1"
            if versioned_id in self.species_mapping:
                return self.species_mapping[versioned_id]
        
        # Try converting NG_ to NR_ (Gene records to RNA records)
        # NG_ = RefSeq Gene, NR_ = RefSeq RNA - they might refer to the same organism
        if seq_id.startswith('NG_'):
            nr_id = seq_id.replace('NG_', 'NR_', 1)
            if nr_id in self.species_mapping:
                logger.debug(f"Found species for {seq_id} using NR_ conversion: {nr_id}")
                return self.species_mapping[nr_id]
            
            # Try without version
            nr_base = nr_id.split('.')[0]
            if nr_base in self.species_mapping:
                logger.debug(f"Found species for {seq_id} using NR_ base conversion: {nr_base}")
                return self.species_mapping[nr_base]
        
        # Try all entries that have the same numeric ID (regardless of prefix)
        # Extract numeric part: NG_065604.1 -> 065604
        try:
            numeric_part = seq_id.split('_')[1].split('.')[0]
            for mapped_id, species in self.species_mapping.items():
                if numeric_part in mapped_id:
                    logger.debug(f"Found species for {seq_id} using numeric match with {mapped_id}")
                    return species
        except (IndexError, AttributeError):
            pass
        
        logger.debug(f"No species name found for sequence {seq_id}")
        return None
    
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
            logger.error("Model not loaded")
            raise ValueError("Model not loaded. Please load a model first.")
        
        logger.debug(f"Starting inference for sequence {sequence_hash[:8]}")
        
        # Generate embedding
        embedding = embedding_service.embed_sequence(sequence)
        logger.debug(f"Generated embedding with shape {embedding.shape}")
        
        # Search for similar sequences
        similar_ids, similarities = self.faiss_index.search(
            embedding,
            k=top_k
        )
        
        logger.debug(f"Found {len(similar_ids)} similar sequences")
        logger.debug(f"Raw similarities: {similarities}")
        
        # Build similar sequences list
        similar_sequences = []
        cluster_predictions = []
        
        for seq_id, similarity in zip(similar_ids, similarities):
            # Get metadata for this sequence
            metadata = self.cluster_metadata.get(seq_id, {})
            cluster_id = metadata.get('cluster_id')
            taxonomy = metadata.get('taxonomy')
            
            # Get species name from mapping - try multiple approaches
            species_name = self._get_species_name_for_sequence(seq_id)
            
            similar_seq = SimilarSequence(
                sequence_id=seq_id,
                similarity=float(similarity),
                cluster_id=cluster_id,
                taxonomy=taxonomy,
                species_name=species_name
            )
            similar_sequences.append(similar_seq)
            
            # Collect cluster predictions for voting
            # similarity is (1 - L2_distance), but L2 distances can be > 1, resulting in negative values
            # For voting, use max(0, similarity) to ensure non-negative weights
            # Only consider sequences with positive similarity (distance < 1)
            vote_weight = max(0.0, float(similarity))
            
            logger.debug(f"Seq {seq_id}: similarity={similarity:.4f}, vote_weight={vote_weight:.4f}, cluster={cluster_id}")
            
            # Include both clustered sequences (>= 0) and noise points (-1) in voting
            # Skip only if cluster_id is truly missing (None)
            if cluster_id is not None and vote_weight > 0.0:  # Any positive similarity counts
                cluster_predictions.append((cluster_id, vote_weight))
        
        # Determine most likely cluster/species by voting
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
                total_weight = sum(cluster_votes.values())
                confidence = cluster_votes[predicted_cluster] / total_weight if total_weight > 0 else 0.0
                
                # Get taxonomy and species from most similar sequence in predicted cluster
                for seq in similar_sequences:
                    if seq.cluster_id == predicted_cluster:
                        predicted_taxonomy = seq.taxonomy
                        predicted_species = seq.species_name
                        break
        
        # If no cluster predictions (all similarities < 0 or all cluster_ids are None), 
        # use the top result anyway based on species name
        if predicted_species is None and similar_sequences:
            top_match = similar_sequences[0]
            predicted_cluster = top_match.cluster_id
            predicted_taxonomy = top_match.taxonomy
            predicted_species = top_match.species_name
            # Use absolute similarity as confidence (clamped to 0-1)
            confidence = max(0.0, min(1.0, top_match.similarity))
            
            logger.info(f"Using fallback: top match species={predicted_species}, similarity={top_match.similarity:.4f}")
        
        # Alternative voting by species name if all cluster_ids are None
        if predicted_species is None and similar_sequences:
            from collections import defaultdict
            species_votes = defaultdict(float)
            
            for seq in similar_sequences:
                if seq.species_name and seq.similarity > 0:
                    species_votes[seq.species_name] += max(0.0, seq.similarity)
            
            if species_votes:
                predicted_species = max(species_votes.items(), key=lambda x: x[1])[0]
                total_weight = sum(species_votes.values())
                confidence = species_votes[predicted_species] / total_weight if total_weight > 0 else 0.0
                
                # Find cluster and taxonomy for this species
                for seq in similar_sequences:
                    if seq.species_name == predicted_species:
                        predicted_cluster = seq.cluster_id
                        predicted_taxonomy = seq.taxonomy
                        break
                
                logger.info(f"Predicted by species voting: {predicted_species}, confidence: {confidence:.3f}")
        
        logger.info(f"Final prediction - cluster: {predicted_cluster}, species: {predicted_species}, confidence: {confidence:.3f}")
        
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
        logger.info(f"Starting batch inference for {len(sequences)} sequences")
        results = []
        
        for idx, sequence in enumerate(sequences):
            try:
                result = self.infer(sequence, top_k)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch inference for sequence {idx}: {e}", exc_info=True)
                # Add error placeholder
                results.append(None)
        
        logger.info(f"Batch inference completed. {len([r for r in results if r is not None])}/{len(sequences)} successful")
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model."""
        if self.faiss_index is None:
            return {"status": "no_model_loaded"}
        
        stats = self.faiss_index.get_stats()
        
        return {
            "status": "loaded",
            "version": self.current_model_version,
            "index_stats": stats,
            "embeddings_loaded": self.embeddings is not None,
            "embeddings_shape": self.embeddings.shape if self.embeddings is not None else None,
            "metadata_count": len(self.cluster_metadata),
            "species_mapping_count": len(self.species_mapping)
        }


# Global inference service instance
inference_service = InferenceService()
