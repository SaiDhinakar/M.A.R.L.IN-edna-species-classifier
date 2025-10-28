"""
Data Preprocessing Step for eDNA Classifier
Based on notebooks/01_preprocessing.ipynb cells 6-10
Quality control and filtering of sequences
"""

import pandas as pd
import numpy as np
import mlflow
from zenml import step
from typing import Dict


class SequenceQualityControl:
    """Class for sequence quality control and filtering"""
    
    def __init__(self, min_length=50, max_length=2000, min_gc=10, max_gc=90):
        self.min_length = min_length
        self.max_length = max_length
        self.min_gc = min_gc
        self.max_gc = max_gc
        
    def filter_sequences(self, df):
        """Apply quality filters to sequences"""
        initial_count = len(df)
        print(f"Initial sequence count: {initial_count}")
        
        # Length filtering
        df_filtered = df[
            (df['length'] >= self.min_length) & 
            (df['length'] <= self.max_length)
        ].copy()
        print(f"After length filtering ({self.min_length}-{self.max_length} bp): {len(df_filtered)}")
        
        # GC content filtering
        df_filtered = df_filtered[
            (df_filtered['gc_content'] >= self.min_gc) & 
            (df_filtered['gc_content'] <= self.max_gc)
        ].copy()
        print(f"After GC content filtering ({self.min_gc}-{self.max_gc}%): {len(df_filtered)}")
        
        # Remove sequences with ambiguous nucleotides (>5%)
        df_filtered['ambiguous_ratio'] = df_filtered['sequence'].apply(self._calculate_ambiguous_ratio)
        df_filtered = df_filtered[df_filtered['ambiguous_ratio'] <= 0.05].copy()
        print(f"After ambiguous nucleotide filtering (≤5%): {len(df_filtered)}")
        
        # Remove duplicates based on sequence
        df_filtered = df_filtered.drop_duplicates(subset=['sequence']).copy()
        print(f"After duplicate removal: {len(df_filtered)}")
        
        print(f"Total sequences removed: {initial_count - len(df_filtered)}")
        print(f"Retention rate: {len(df_filtered)/initial_count*100:.1f}%")
        
        return df_filtered
    
    def _calculate_ambiguous_ratio(self, sequence):
        """Calculate ratio of ambiguous nucleotides"""
        ambiguous = 'NRYSWKMBDHV'
        ambiguous_count = sum(sequence.upper().count(char) for char in ambiguous)
        return ambiguous_count / len(sequence) if sequence else 0
    
    def generate_quality_report(self, df):
        """Generate quality control report"""
        report = {
            'total_sequences': len(df),
            'length_stats': df['length'].describe().to_dict(),
            'gc_content_stats': df['gc_content'].describe().to_dict(),
            'database_distribution': df['database'].value_counts().to_dict(),
            'taxonomy_distribution': df['taxonomy'].apply(lambda x: x['kingdom']).value_counts().to_dict()
        }
        return report


@step
def preprocess_sequences(
    df_raw: pd.DataFrame,
    min_length: int = 100,
    max_length: int = 1500,
    min_gc: float = 10.0,
    max_gc: float = 90.0
) -> pd.DataFrame:
    """
    Preprocess and filter eDNA sequences
    
    Args:
        df_raw: Raw sequences from ingestion
        min_length: Minimum sequence length
        max_length: Maximum sequence length
        min_gc: Minimum GC content
        max_gc: Maximum GC content
        
    Returns:
        Filtered sequences DataFrame
    """
    with mlflow.start_run(run_name="preprocessing", nested=True):
        mlflow.log_param("min_length", min_length)
        mlflow.log_param("max_length", max_length)
        mlflow.log_param("min_gc", min_gc)
        mlflow.log_param("max_gc", max_gc)
        mlflow.log_param("initial_sequences", len(df_raw))
        
        # Apply quality control
        qc = SequenceQualityControl(
            min_length=min_length,
            max_length=max_length,
            min_gc=min_gc,
            max_gc=max_gc
        )
        
        df_filtered = qc.filter_sequences(df_raw)
        
        # Generate quality report
        quality_report = qc.generate_quality_report(df_filtered)
        
        # Log metrics
        mlflow.log_metric("filtered_sequences", len(df_filtered))
        mlflow.log_metric("sequences_removed", len(df_raw) - len(df_filtered))
        mlflow.log_metric("retention_rate", len(df_filtered)/len(df_raw))
        mlflow.log_metric("avg_length", quality_report['length_stats']['mean'])
        mlflow.log_metric("avg_gc_content", quality_report['gc_content_stats']['mean'])
        
        print("\n=== Quality Control Report ===")
        print(f"Total sequences: {quality_report['total_sequences']}")
        print(f"Length statistics: {quality_report['length_stats']}")
        print(f"GC content statistics: {quality_report['gc_content_stats']}")
        print(f"Database distribution: {quality_report['database_distribution']}")
        
        return df_filtered


if __name__ == "__main__":
    # Test preprocessing
    from ingestion import ingest_data_from_minio
    df_raw = ingest_data_from_minio(max_sequences_per_db=100, use_simulated=True)
    df_processed = preprocess_sequences(df_raw)
    print(f"\nProcessed {len(df_processed)} sequences")
    print(df_processed.head())
