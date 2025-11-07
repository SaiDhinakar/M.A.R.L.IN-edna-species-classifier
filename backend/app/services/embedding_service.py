"""
DNA sequence embedding service using PyTorch and Transformers.
"""

import torch
import numpy as np
from typing import List
from itertools import product
import logging

from app.core.config import settings
from app.utils.logger import LoggerSetup


logger = LoggerSetup.get_logger(
    name=__name__,
    level=logging.DEBUG,
    log_file="logs/embedding_service.log",
    max_bytes=5 * 1024 * 1024,  # 5MB
    backup_count=3,
    console_output=True
)


class EmbeddingService:
    """Service for generating DNA sequence embeddings."""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained DNA language model."""
        try:
            # Using a DNA-BERT style model (or can use simpler k-mer approach)
            # For MVP, we'll use a simple k-mer based embedding
            # In production, use models like "zhihan1996/DNA_bert_6" or similar
            # Uncomment below if using transformers:
            # from transformers import AutoTokenizer, AutoModel
            # self.tokenizer = AutoTokenizer.from_pretrained("zhihan1996/DNA_bert_6")
            # self.model = AutoModel.from_pretrained("zhihan1996/DNA_bert_6")
            
            logger.info(f"Embedding service initialized on device: {self.device}")
            logger.info("Using k-mer based embeddings for MVP")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def _sequence_to_kmers(self, sequence: str, k: int = 6) -> List[str]:
        """Convert DNA sequence to k-mers."""
        kmers = []
        for i in range(len(sequence) - k + 1):
            kmers.append(sequence[i:i+k])
        return kmers
    
    def _kmer_embedding(self, sequence: str, k: int = 6) -> np.ndarray:
        """
        Generate embedding using k-mer frequency vectors.
        Simple but effective approach for MVP.
        """
        # All possible k-mers for DNA (4^k possibilities)
        bases = ['A', 'T', 'G', 'C']
        
        # Generate all k-mers
        all_kmers = [''.join(p) for p in product(bases, repeat=k)]
        kmer_to_idx = {kmer: idx for idx, kmer in enumerate(all_kmers)}
        
        # Initialize frequency vector
        embedding = np.zeros(len(all_kmers), dtype=np.float32)
        
        # Count k-mers in sequence
        kmers = self._sequence_to_kmers(sequence, k)
        for kmer in kmers:
            if kmer in kmer_to_idx:
                embedding[kmer_to_idx[kmer]] += 1
        
        # Normalize
        if embedding.sum() > 0:
            embedding = embedding / embedding.sum()
        
        # Pad or truncate to match embedding dimension
        if len(embedding) > settings.model_embedding_dim:
            # Truncate
            embedding = embedding[:settings.model_embedding_dim]
        elif len(embedding) < settings.model_embedding_dim:
            # Pad with zeros
            padding = np.zeros(settings.model_embedding_dim - len(embedding), dtype=np.float32)
            embedding = np.concatenate([embedding, padding])
        
        return embedding
    
    def embed_sequence(self, sequence: str) -> np.ndarray:
        """Generate embedding for a single sequence."""
        # Clean sequence
        sequence = sequence.upper().replace('N', '')
        
        # Generate k-mer embedding
        embedding = self._kmer_embedding(sequence, k=6)
        
        return embedding
    
    def embed_sequences(
        self,
        sequences: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """Generate embeddings for multiple sequences."""
        embeddings = []
        
        for seq in sequences:
            embedding = self.embed_sequence(seq)
            embeddings.append(embedding)
        
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings_array
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        # Normalize
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)


# Global embedding service instance
embedding_service = EmbeddingService()
