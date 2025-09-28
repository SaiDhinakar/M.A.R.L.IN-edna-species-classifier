import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
import logging
from typing import List, Dict, Any, Optional
from app.core.config import get_settings
from app.core.utils import get_minio_client

logger = logging.getLogger(__name__)
settings = get_settings()


class DNAPreprocessor:
    """Handles DNA sequence preprocessing and quality control"""
    
    def __init__(self):
        self.valid_bases = set('ATCG')
        self.min_length = 50
        self.max_length = 10000
    
    def clean_sequence(self, sequence: str) -> str:
        """Clean and normalize DNA sequence"""
        # Convert to uppercase and remove whitespace
        sequence = sequence.upper().strip()
        
        # Remove non-DNA characters (keep only ATCG)
        cleaned = ''.join(c for c in sequence if c in self.valid_bases)
        
        return cleaned
    
    def validate_sequence(self, sequence: str) -> tuple[bool, str]:
        """Validate DNA sequence quality"""
        cleaned = self.clean_sequence(sequence)
        
        if len(cleaned) < self.min_length:
            return False, f"Sequence too short: {len(cleaned)} < {self.min_length}"
        
        if len(cleaned) > self.max_length:
            return False, f"Sequence too long: {len(cleaned)} > {self.max_length}"
        
        # Check for too many ambiguous bases
        original_length = len(sequence.upper().strip())
        if len(cleaned) / original_length < 0.8:
            return False, "Too many ambiguous bases (>20%)"
        
        return True, "Valid"
    
    def get_gc_content(self, sequence: str) -> float:
        """Calculate GC content of sequence"""
        cleaned = self.clean_sequence(sequence)
        if not cleaned:
            return 0.0
        
        gc_count = cleaned.count('G') + cleaned.count('C')
        return gc_count / len(cleaned)
    
    def get_sequence_stats(self, sequence: str) -> Dict[str, Any]:
        """Get comprehensive sequence statistics"""
        cleaned = self.clean_sequence(sequence)
        
        if not cleaned:
            return {
                "length": 0,
                "gc_content": 0.0,
                "base_counts": {"A": 0, "T": 0, "C": 0, "G": 0},
                "valid": False
            }
        
        base_counts = {
            "A": cleaned.count('A'),
            "T": cleaned.count('T'),
            "C": cleaned.count('C'),
            "G": cleaned.count('G')
        }
        
        return {
            "length": len(cleaned),
            "gc_content": self.get_gc_content(sequence),
            "base_counts": base_counts,
            "valid": True
        }


class DNAEmbedder:
    """Generates embeddings for DNA sequences using pre-trained models"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = "microsoft/DialoGPT-medium"  # Placeholder - use actual DNA model
        self.tokenizer = None
        self.model = None
        self.minio_client = get_minio_client()
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model for DNA sequence embedding"""
        try:
            # Check if model exists in MinIO first
            model_path = "dna_embedder/model"
            if self.minio_client.file_exists(settings.minio_bucket_models, f"{model_path}/config.json"):
                logger.info("Loading model from MinIO storage...")
                # In production, implement model loading from MinIO
                # For now, use HuggingFace transformers
            
            logger.info(f"Loading DNA embedding model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def _tokenize_dna(self, sequence: str, max_length: int = 512) -> Dict[str, torch.Tensor]:
        """Tokenize DNA sequence for model input"""
        # Simple k-mer tokenization approach
        k = 6  # 6-mer tokenization
        kmers = []
        
        for i in range(len(sequence) - k + 1):
            kmer = sequence[i:i+k]
            kmers.append(kmer)
        
        # Join k-mers with spaces for tokenizer
        kmer_string = " ".join(kmers[:max_length//k])
        
        return self.tokenizer(
            kmer_string,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length
        )
    
    def generate_embedding(self, sequence: str) -> Optional[np.ndarray]:
        """Generate embedding vector for DNA sequence"""
        try:
            if not sequence:
                return None
            
            # Tokenize sequence
            inputs = self._tokenize_dna(sequence)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden states
                embeddings = outputs.last_hidden_state.mean(dim=1)
                
            return embeddings.cpu().numpy().flatten()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_batch_embeddings(self, sequences: List[str], batch_size: int = 32) -> List[Optional[np.ndarray]]:
        """Generate embeddings for multiple sequences in batches"""
        embeddings = []
        
        for i in range(0, len(sequences), batch_size):
            batch = sequences[i:i+batch_size]
            batch_embeddings = []
            
            for seq in batch:
                embedding = self.generate_embedding(seq)
                batch_embeddings.append(embedding)
            
            embeddings.extend(batch_embeddings)
            
            if (i // batch_size + 1) % 10 == 0:
                logger.info(f"Processed {i + len(batch)}/{len(sequences)} sequences")
        
        return embeddings


# Global instances
dna_preprocessor = DNAPreprocessor()
dna_embedder = DNAEmbedder()


def get_dna_preprocessor() -> DNAPreprocessor:
    """Get the global DNA preprocessor instance"""
    return dna_preprocessor


def get_dna_embedder() -> DNAEmbedder:
    """Get the global DNA embedder instance"""
    return dna_embedder