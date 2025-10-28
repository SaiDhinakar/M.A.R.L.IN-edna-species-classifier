"""
ZenML step for sequence embedding generation.
Implements k-mer and compositional feature extraction from notebook 02.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Annotated
from itertools import product
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from zenml import step
import mlflow


class KmerEmbedder:
    """K-mer based sequence embedding generator"""
    
    def __init__(self, k_sizes=[3, 4, 5, 6], method='tfidf'):
        self.k_sizes = k_sizes
        self.method = method
        self.vectorizers = {}
        self.embeddings = {}
        
    def generate_kmers(self, sequence, k):
        """Generate k-mers from sequence"""
        sequence = sequence.upper()
        kmers = []
        for i in range(len(sequence) - k + 1):
            kmer = sequence[i:i+k]
            if 'N' not in kmer:  # Skip k-mers with ambiguous nucleotides
                kmers.append(kmer)
        return ' '.join(kmers)
    
    def fit_transform(self, sequences):
        """Fit vectorizers and transform sequences"""
        print(f"Generating k-mer embeddings using {self.method}...")
        
        all_embeddings = []
        
        for k in self.k_sizes:
            print(f"Processing {k}-mers...")
            
            # Generate k-mer strings for all sequences
            kmer_docs = [self.generate_kmers(seq, k) for seq in sequences]
            
            # Initialize vectorizer
            if self.method == 'tfidf':
                vectorizer = TfidfVectorizer(
                    analyzer='word',
                    ngram_range=(1, 1),
                    min_df=2,
                    max_features=1000,
                    token_pattern=r'\S+'
                )
            else:  # count
                vectorizer = CountVectorizer(
                    analyzer='word',
                    ngram_range=(1, 1),
                    min_df=2,
                    max_features=1000,
                    token_pattern=r'\S+'
                )
            
            # Fit and transform
            try:
                embedding = vectorizer.fit_transform(kmer_docs).toarray()
                self.vectorizers[k] = vectorizer
                self.embeddings[k] = embedding
                all_embeddings.append(embedding)
                print(f"{k}-mer embedding shape: {embedding.shape}")
            except ValueError as e:
                print(f"Error with {k}-mers: {e}")
                continue
        
        # Concatenate all k-mer embeddings
        if all_embeddings:
            combined_embedding = np.hstack(all_embeddings)
            print(f"Combined k-mer embedding shape: {combined_embedding.shape}")
            return combined_embedding
        else:
            return np.array([])
    
    def get_feature_names(self):
        """Get feature names for interpretation"""
        feature_names = []
        for k in self.k_sizes:
            if k in self.vectorizers:
                kmer_features = [f"{k}mer_{feature}" for feature in self.vectorizers[k].get_feature_names_out()]
                feature_names.extend(kmer_features)
        return feature_names


class CompositionEmbedder:
    """Compositional feature-based embedding generator"""
    
    def __init__(self):
        self.feature_names = []
        
    def calculate_nucleotide_composition(self, sequence):
        """Calculate single nucleotide composition"""
        sequence = sequence.upper()
        length = len(sequence)
        if length == 0:
            return [0, 0, 0, 0]
        
        return [
            sequence.count('A') / length,
            sequence.count('T') / length,
            sequence.count('G') / length,
            sequence.count('C') / length
        ]
    
    def calculate_dinucleotide_composition(self, sequence):
        """Calculate dinucleotide composition"""
        sequence = sequence.upper()
        dinucs = [''.join(p) for p in product('ATGC', repeat=2)]
        length = len(sequence) - 1
        if length <= 0:
            return [0] * 16
        
        counts = []
        for dinuc in dinucs:
            count = 0
            for i in range(len(sequence) - 1):
                if sequence[i:i+2] == dinuc:
                    count += 1
            counts.append(count / length)
        return counts
    
    def calculate_gc_features(self, sequence):
        """Calculate GC-related features"""
        sequence = sequence.upper()
        length = len(sequence)
        if length == 0:
            return [0, 0, 0, 0]
        
        gc_content = (sequence.count('G') + sequence.count('C')) / length
        
        # GC skew: (G-C)/(G+C)
        g_count = sequence.count('G')
        c_count = sequence.count('C')
        gc_skew = (g_count - c_count) / (g_count + c_count) if (g_count + c_count) > 0 else 0
        
        # AT skew: (A-T)/(A+T)  
        a_count = sequence.count('A')
        t_count = sequence.count('T')
        at_skew = (a_count - t_count) / (a_count + t_count) if (a_count + t_count) > 0 else 0
        
        return [gc_content, gc_skew, at_skew, length]
    
    def fit_transform(self, sequences):
        """Generate compositional features"""
        print("Generating compositional features...")
        
        features = []
        self.feature_names = []
        
        for seq in sequences:
            seq_features = []
            
            # Nucleotide composition
            nuc_comp = self.calculate_nucleotide_composition(seq)
            seq_features.extend(nuc_comp)
            
            # Dinucleotide composition
            dinuc_comp = self.calculate_dinucleotide_composition(seq)
            seq_features.extend(dinuc_comp)
            
            # GC features
            gc_features = self.calculate_gc_features(seq)
            seq_features.extend(gc_features)
            
            features.append(seq_features)
        
        # Set feature names
        self.feature_names = (['A_freq', 'T_freq', 'G_freq', 'C_freq'] + 
                             [f'{dinuc}_freq' for dinuc in [''.join(p) for p in product('ATGC', repeat=2)]] +
                             ['GC_content', 'GC_skew', 'AT_skew', 'length'])
        
        embedding = np.array(features)
        print(f"Compositional embedding shape: {embedding.shape}")
        return embedding


@step
def generate_embeddings(
    sequences_df: pd.DataFrame,
    k_sizes: list = [3, 4, 5],
    embedding_method: str = 'tfidf'
) -> Tuple[
    Annotated[np.ndarray, "kmer_embeddings"],
    Annotated[np.ndarray, "compositional_embeddings"],
    Annotated[np.ndarray, "combined_embeddings"]
]:
    """
    Generate k-mer and compositional embeddings from sequences.
    
    Args:
        sequences_df: DataFrame with 'sequence' column
        k_sizes: List of k-mer sizes to use (default: [3,4,5])
        embedding_method: Vectorization method ('tfidf' or 'count')
    
    Returns:
        Tuple of (kmer_embeddings, compositional_embeddings, combined_embeddings)
    """
    with mlflow.start_run(nested=True, run_name="embedding"):
        # Log parameters
        mlflow.log_param("k_sizes", k_sizes)
        mlflow.log_param("embedding_method", embedding_method)
        mlflow.log_param("num_sequences", len(sequences_df))
        
        # Extract sequences
        sequences = sequences_df['sequence'].tolist()
        
        # Generate k-mer embeddings
        kmer_embedder = KmerEmbedder(k_sizes=k_sizes, method=embedding_method)
        kmer_embeddings = kmer_embedder.fit_transform(sequences)
        
        # Generate compositional embeddings
        comp_embedder = CompositionEmbedder()
        comp_embeddings = comp_embedder.fit_transform(sequences)
        
        # Combine embeddings
        combined_embeddings = np.hstack([kmer_embeddings, comp_embeddings])
        
        # Log metrics
        mlflow.log_metric("kmer_embedding_dim", kmer_embeddings.shape[1])
        mlflow.log_metric("comp_embedding_dim", comp_embeddings.shape[1])
        mlflow.log_metric("combined_embedding_dim", combined_embeddings.shape[1])
        
        print(f"✅ Embedding generation complete:")
        print(f"   K-mer embeddings: {kmer_embeddings.shape}")
        print(f"   Compositional embeddings: {comp_embeddings.shape}")
        print(f"   Combined embeddings: {combined_embeddings.shape}")
        
        return kmer_embeddings, comp_embeddings, combined_embeddings
