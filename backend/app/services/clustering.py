import io
import numpy as np
import hdbscan
import faiss
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any, Optional, Tuple
import logging
from app.core.config import get_settings
from app.core.utils import get_minio_client

logger = logging.getLogger(__name__)
settings = get_settings()


class SequenceClusterer:
    """Handles clustering of DNA sequence embeddings using HDBSCAN"""
    
    def __init__(self):
        self.clusterer = None
        self.scaler = StandardScaler()
        self.minio_client = get_minio_client()
        self.min_cluster_size = 5
        self.min_samples = 3
    
    def _prepare_embeddings(self, embeddings: List[np.ndarray]) -> np.ndarray:
        """Prepare embeddings for clustering"""
        # Filter out None embeddings
        valid_embeddings = [emb for emb in embeddings if emb is not None]
        
        if not valid_embeddings:
            raise ValueError("No valid embeddings provided")
        
        # Stack embeddings into matrix
        embedding_matrix = np.vstack(valid_embeddings)
        
        # Normalize embeddings
        normalized_embeddings = self.scaler.fit_transform(embedding_matrix)
        
        return normalized_embeddings
    
    def cluster_sequences(self, embeddings: List[np.ndarray], 
                         min_cluster_size: Optional[int] = None,
                         min_samples: Optional[int] = None) -> Dict[str, Any]:
        """Cluster sequences based on their embeddings"""
        try:
            if min_cluster_size is None:
                min_cluster_size = self.min_cluster_size
            if min_samples is None:
                min_samples = self.min_samples
            
            # Prepare embeddings
            normalized_embeddings = self._prepare_embeddings(embeddings)
            
            # Initialize HDBSCAN clusterer
            self.clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                metric='euclidean',
                cluster_selection_method='eom'
            )
            
            # Perform clustering
            cluster_labels = self.clusterer.fit_predict(normalized_embeddings)
            
            # Calculate cluster statistics
            unique_labels = np.unique(cluster_labels)
            n_clusters = len(unique_labels) - (1 if -1 in cluster_labels else 0)
            n_noise = list(cluster_labels).count(-1)
            
            # Get cluster probabilities
            cluster_probabilities = self.clusterer.probabilities_
            
            # Create cluster assignments
            cluster_assignments = []
            for i, label in enumerate(cluster_labels):
                cluster_assignments.append({
                    "sequence_index": i,
                    "cluster_id": int(label) if label != -1 else None,
                    "probability": float(cluster_probabilities[i]) if cluster_probabilities is not None else 0.0,
                    "is_noise": label == -1
                })
            
            return {
                "n_clusters": n_clusters,
                "n_noise": n_noise,
                "cluster_labels": cluster_labels.tolist(),
                "cluster_assignments": cluster_assignments,
                "cluster_centers": self._calculate_cluster_centers(normalized_embeddings, cluster_labels)
            }
            
        except Exception as e:
            logger.error(f"Error clustering sequences: {e}")
            raise
    
    def _calculate_cluster_centers(self, embeddings: np.ndarray, labels: np.ndarray) -> Dict[int, List[float]]:
        """Calculate cluster centers"""
        centers = {}
        unique_labels = np.unique(labels)
        
        for label in unique_labels:
            if label == -1:  # Skip noise
                continue
                
            cluster_mask = labels == label
            cluster_embeddings = embeddings[cluster_mask]
            center = np.mean(cluster_embeddings, axis=0)
            centers[int(label)] = center.tolist()
        
        return centers
    
    def save_cluster_model(self, model_id: str) -> bool:
        """Save clustering model to MinIO"""
        try:
            if self.clusterer is None:
                logger.error("No clusterer model to save")
                return False
            
            model_data = {
                "clusterer": self.clusterer,
                "scaler": self.scaler,
                "min_cluster_size": self.min_cluster_size,
                "min_samples": self.min_samples
            }
            
            object_name = f"clustering_models/{model_id}.pkl"
            return self.minio_client.upload_pickle(
                settings.minio_bucket_models, object_name, model_data
            )
            
        except Exception as e:
            logger.error(f"Error saving cluster model: {e}")
            return False
    
    def load_cluster_model(self, model_id: str) -> bool:
        """Load clustering model from MinIO"""
        try:
            object_name = f"clustering_models/{model_id}.pkl"
            model_data = self.minio_client.download_pickle(
                settings.minio_bucket_models, object_name
            )
            
            if model_data is None:
                logger.error(f"Cluster model {model_id} not found")
                return False
            
            self.clusterer = model_data["clusterer"]
            self.scaler = model_data["scaler"]
            self.min_cluster_size = model_data["min_cluster_size"]
            self.min_samples = model_data["min_samples"]
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading cluster model: {e}")
            return False


class SimilaritySearcher:
    """Handles similarity search using FAISS"""
    
    def __init__(self):
        self.index = None
        self.embeddings = None
        self.sequence_ids = None
        self.minio_client = get_minio_client()
    
    def build_index(self, embeddings: List[np.ndarray], sequence_ids: List[str]) -> bool:
        """Build FAISS index for similarity search"""
        try:
            # Filter valid embeddings
            valid_data = [(emb, seq_id) for emb, seq_id in zip(embeddings, sequence_ids) 
                         if emb is not None]
            
            if not valid_data:
                logger.error("No valid embeddings to build index")
                return False
            
            valid_embeddings, valid_ids = zip(*valid_data)
            embedding_matrix = np.vstack(valid_embeddings).astype(np.float32)
            
            # Build FAISS index
            dimension = embedding_matrix.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embedding_matrix)
            
            # Add embeddings to index
            self.index.add(embedding_matrix)
            
            self.embeddings = embedding_matrix
            self.sequence_ids = list(valid_ids)
            
            logger.info(f"Built FAISS index with {len(valid_ids)} sequences")
            return True
            
        except Exception as e:
            logger.error(f"Error building FAISS index: {e}")
            return False
    
    def search_similar(self, query_embedding: np.ndarray, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar sequences"""
        try:
            if self.index is None:
                logger.error("No index built for similarity search")
                return []
            
            if query_embedding is None:
                return []
            
            # Prepare query
            query = query_embedding.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(query)
            
            # Search
            scores, indices = self.index.search(query, k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.sequence_ids):
                    results.append({
                        "sequence_id": self.sequence_ids[idx],
                        "similarity_score": float(score),
                        "index": int(idx)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar sequences: {e}")
            return []
    
    def save_index(self, index_id: str) -> bool:
        """Save FAISS index to MinIO"""
        try:
            if self.index is None:
                logger.error("No index to save")
                return False
            
            # Save index to bytes
            index_data = faiss.serialize_index(self.index)
            
            # Save index
            index_success = self.minio_client.upload_file(
                settings.minio_bucket_models,
                f"faiss_indices/{index_id}.index",
                io.BytesIO(index_data),
                content_type="application/octet-stream"
            )
            
            # Save metadata
            metadata = {
                "sequence_ids": self.sequence_ids,
                "embeddings_shape": self.embeddings.shape if self.embeddings is not None else None
            }
            
            metadata_success = self.minio_client.upload_json(
                settings.minio_bucket_models,
                f"faiss_indices/{index_id}_metadata.json",
                metadata
            )
            
            return index_success and metadata_success
            
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
            return False
    
    def load_index(self, index_id: str) -> bool:
        """Load FAISS index from MinIO"""
        try:
            # Load index
            index_data = self.minio_client.download_file(
                settings.minio_bucket_models,
                f"faiss_indices/{index_id}.index"
            )
            
            if index_data is None:
                logger.error(f"FAISS index {index_id} not found")
                return False
            
            self.index = faiss.deserialize_index(index_data)
            
            # Load metadata
            metadata = self.minio_client.download_json(
                settings.minio_bucket_models,
                f"faiss_indices/{index_id}_metadata.json"
            )
            
            if metadata:
                self.sequence_ids = metadata.get("sequence_ids", [])
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            return False


# Global instances
sequence_clusterer = SequenceClusterer()
similarity_searcher = SimilaritySearcher()


def get_sequence_clusterer() -> SequenceClusterer:
    """Get the global sequence clusterer instance"""
    return sequence_clusterer


def get_similarity_searcher() -> SimilaritySearcher:
    """Get the global similarity searcher instance"""
    return similarity_searcher