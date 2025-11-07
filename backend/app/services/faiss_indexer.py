"""
FAISS indexer service for similarity search on DNA sequence embeddings.
"""

import faiss
import numpy as np
from typing import List, Tuple, Optional
import pickle
import logging
from pathlib import Path

from app.core.config import settings
from app.services.minio_service import minio_service

from app.utils.logger import LoggerSetup

logger = LoggerSetup.get_logger(
    name=__name__,
    level=logging.INFO,
    log_file="logs/faiss_indexer.log",
    max_bytes=5 * 1024 * 1024,  # 5MB
    backup_count=3,
    console_output=True
)


class FAISSIndexer:
    """Service for managing FAISS vector indices."""
    
    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.dimension: int = settings.model_embedding_dim
        self.sequence_ids: List[str] = []
    
    def create_index(
        self,
        dimension: Optional[int] = None
    ) -> faiss.Index:
        """Create a new FAISS index."""
        dim = dimension or self.dimension
        
        # Use IndexFlatL2 for exact search (can upgrade to IVF for large datasets)
        index = faiss.IndexFlatL2(dim)
        
        # Add index to enable IDs
        index = faiss.IndexIDMap(index)
        
        self.index = index
        self.dimension = dim
        logger.info(f"Created FAISS index with dimension {dim}")
        return index
    
    def add_vectors(
        self,
        embeddings: np.ndarray,
        sequence_ids: List[str]
    ):
        """Add vectors to the index."""
        if self.index is None:
            self.create_index()
        
        # Ensure embeddings are float32
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create IDs for the vectors
        n = len(embeddings)
        ids = np.arange(len(self.sequence_ids), len(self.sequence_ids) + n, dtype=np.int64)
        
        # Add to index
        self.index.add_with_ids(embeddings, ids)
        
        # Store sequence IDs
        self.sequence_ids.extend(sequence_ids)
        
        logger.info(f"Added {n} vectors to FAISS index. Total: {self.index.ntotal}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> Tuple[List[str], List[float]]:
        """Search for k nearest neighbors."""
        if self.index is None or self.index.ntotal == 0:
            return [], []
        
        # Ensure query is 2D float32 and normalized
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)
        
        faiss.normalize_L2(query_embedding)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)
        
        # Convert distances to similarities (1 - distance)
        similarities = (1 - distances[0]).tolist()
        
        # Get sequence IDs
        result_ids = []
        for idx in indices[0]:
            if 0 <= idx < len(self.sequence_ids):
                result_ids.append(self.sequence_ids[int(idx)])
        
        return result_ids, similarities
    
    def save_index(
        self,
        index_name: str,
        local_path: Optional[str] = None
    ) -> str:
        """Save index to file and upload to MinIO."""
        if self.index is None:
            raise ValueError("No index to save")
        
        # Create local path if not provided
        if local_path is None:
            local_path = f"./data/indices/{index_name}.faiss"
        
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, local_path)
        
        # Save sequence IDs mapping
        metadata_path = local_path.replace(".faiss", "_metadata.pkl")
        with open(metadata_path, "wb") as f:
            pickle.dump({
                "sequence_ids": self.sequence_ids,
                "dimension": self.dimension
            }, f)
        
        # Upload to MinIO
        minio_path = minio_service.upload_file(
            local_path,
            f"indices/{index_name}.faiss",
            settings.minio_bucket_models
        )
        
        minio_service.upload_file(
            metadata_path,
            f"indices/{index_name}_metadata.pkl",
            settings.minio_bucket_models
        )
        
        logger.info(f"Saved FAISS index to {minio_path}")
        return minio_path
    
    def load_index(
        self,
        index_name: str,
        local_path: Optional[str] = None
    ):
        """Load index from MinIO."""
        if local_path is None:
            local_path = f"./data/indices/{index_name}.faiss"
        
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Download from MinIO
        minio_service.download_file(
            f"indices/{index_name}.faiss",
            settings.minio_bucket_models,
            local_path
        )
        
        metadata_path = local_path.replace(".faiss", "_metadata.pkl")
        minio_service.download_file(
            f"indices/{index_name}_metadata.pkl",
            settings.minio_bucket_models,
            metadata_path
        )
        
        # Load FAISS index
        self.index = faiss.read_index(local_path)
        
        # Load metadata
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)
            self.sequence_ids = metadata["sequence_ids"]
            self.dimension = metadata["dimension"]
        
        logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        if self.index is None:
            return {
                "total_vectors": 0,
                "dimension": self.dimension,
                "is_trained": False
            }
        
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "is_trained": True
        }


# Global FAISS indexer instance
faiss_indexer = FAISSIndexer()
