#!/usr/bin/env python3
"""
Test Script for eDNA Species Classifier Model

This script demonstrates how to:
1. Load a trained FAISS index from MinIO
2. Generate embeddings for test sequences
3. Perform similarity search
4. Display results with detailed information

Usage:
    python test_model.py
    python test_model.py --index-name model_edna_classifier_1
    python test_model.py --sequence "ATGCGATCGATCG..."
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from app.services.embedding_service import embedding_service
from app.services.faiss_indexer import FAISSIndexer
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test sequences (common bacterial 16S rRNA sequences)
TEST_SEQUENCES = {
    "E.coli_16S_V4": {
        "sequence": "TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGTAGAATTCCAGGTGTAGCGGTGAAATGCGTAGAGATCTGGAGGAATACCGGTGGCGAAGGCGGCCCCCTGGACGAAGACTGACGCTCAGGTGCGAAAGCGTGGGGAGCAAACAGG",
        "species": "Escherichia coli",
        "region": "16S rRNA V4 region",
        "length": 253
    },
    "Staphylococcus_16S_V4": {
        "sequence": "TACGTATGTCGCAAGCGTTATCCGGATTTATTGGGCGTAAAGCGAGCGCAGGCGGTTTTTTAAGTCTGATGTGAAAGCCTTCGGCTCAACCGAAGAAGTGCATCGGAAACTGGGAAACTTGAGTGCAGAAGAGGACAGTGGAACTCCATGTGTAGCGGTGAAATGCGTAGATATATGGAAGAACACCAGTGGCGAAGGCGGCTGTCTGGTCTGTAACTGACGCTGAGGCTCGAAAGTATGGGTAGCAAACAGG",
        "species": "Staphylococcus aureus",
        "region": "16S rRNA V4 region",
        "length": 253
    },
    "Pseudomonas_16S_V4": {
        "sequence": "TACGGGTGGCAGCAGTGGGGAATTTTGGACAATGGGCGCAAGCCTGATCCAGCCATGCCGCGTGTGTGAAGAAGGCCTTCGGGTTGTAAAGCACTTTCAGCGAGGAGGAAAGGTTAGTAGCCTAATACGTCGGGGGGATGACGGTACCGGAAGAATAAGCACCGGCTAACTACGTGCCAGCAGCCGCGGTAATACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTTGTTAAGACCGATGTGAAATCCCCGGGCTCAACCTGGGAACT",
        "species": "Pseudomonas aeruginosa",
        "region": "16S rRNA V4 region",
        "length": 300
    },
    "Bacillus_16S_V4": {
        "sequence": "TACGTATGTCGCAAGCGTTATCCGGATTTATTGGGCGTAAAGCGAGCGCAGGCGGTTAGATAAGTCTGAAGTTAAAGGCTGTGGCTTAACCATAGTAGGCTTTGGAAACTGTTTAACTTGAGTGCAAGAGGGGAGAGTGGAATTCCATGTGTAGCGGTGAAATGCGTAGATATATGGAGGAACACCGGTGGCGAAAGCGGCTCTCTGGCTTGTAACTGACGCTGAGGCTCGAAAGCGTGGGGAGCGAACAGG",
        "species": "Bacillus subtilis",
        "region": "16S rRNA V4 region",
        "length": 253
    },
    "Lactobacillus_16S_V4": {
        "sequence": "TACGTAGGTGGCAAGCGTTATCCGGATTTATTGGGCGTAAAGAGCTCGTAGGCGGTTAATCGCGTCTGCCGTGAAAACCCGGGGCTTAACTCCGGGAGTGCGGTGGGTACGGGCAGACTAGAGTACTGTAGGGGAGACTGGAATTCCTGGTGTAGCGGTGGAATGCGCAGATATCAGGAGGAACACCGATGGCGAAGGCAGGTCTCTGGGCTGTAACTGACGCTGAGGAGCGAAAGCATGGGGAGCGAACAGG",
        "species": "Lactobacillus plantarum",
        "region": "16S rRNA V4 region",
        "length": 253
    }
}


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80)


def load_model(index_name: str) -> FAISSIndexer:
    """
    Load a trained FAISS index from MinIO.
    
    Args:
        index_name: Name of the index to load (e.g., "model_edna_classifier_1")
    
    Returns:
        FAISSIndexer instance with loaded index
    """
    print_section("Loading Model")
    print(f"Index name: {index_name}")
    
    indexer = FAISSIndexer()
    
    try:
        indexer.load_index(index_name)
        
        stats = indexer.get_stats()
        print(f"✅ Model loaded successfully!")
        print(f"   Total vectors: {stats['total_vectors']:,}")
        print(f"   Dimension: {stats['dimension']}")
        print(f"   Is trained: {stats['is_trained']}")
        
        return indexer
    
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        print(f"❌ Failed to load model: {e}")
        print("\nTroubleshooting:")
        print("1. Check if the index exists in MinIO")
        print("2. Verify MinIO connection settings")
        print("3. Run training first to create an index")
        sys.exit(1)


def generate_embedding(sequence: str) -> np.ndarray:
    """
    Generate embedding for a DNA sequence.
    
    Args:
        sequence: DNA sequence string (ATGC)
    
    Returns:
        NumPy array of embedding
    """
    print_section("Generating Embedding")
    print(f"Sequence length: {len(sequence)} bp")
    print(f"First 50 bp: {sequence[:50]}...")
    
    try:
        embedding = embedding_service.embed_sequence(sequence)
        print(f"✅ Embedding generated")
        print(f"   Shape: {embedding.shape}")
        print(f"   Type: {embedding.dtype}")
        print(f"   Range: [{embedding.min():.4f}, {embedding.max():.4f}]")
        
        return embedding
    
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        print(f"❌ Failed to generate embedding: {e}")
        sys.exit(1)


def search_similar_sequences(
    indexer: FAISSIndexer,
    query_embedding: np.ndarray,
    k: int = 5
) -> tuple[List[str], List[float]]:
    """
    Search for similar sequences in the index.
    
    Args:
        indexer: FAISSIndexer with loaded index
        query_embedding: Query embedding vector
        k: Number of results to return
    
    Returns:
        Tuple of (sequence_ids, similarities)
    """
    print_section("Searching Similar Sequences")
    print(f"Searching for top {k} matches...")
    
    try:
        sequence_ids, similarities = indexer.search(query_embedding, k=k)
        
        print(f"✅ Search completed")
        print(f"   Found {len(sequence_ids)} results")
        
        return sequence_ids, similarities
    
    except Exception as e:
        logger.error(f"Search failed: {e}")
        print(f"❌ Search failed: {e}")
        return [], []


def display_results(
    query_info: Dict[str, Any],
    sequence_ids: List[str],
    similarities: List[float]
):
    """
    Display search results in a formatted table.
    
    Args:
        query_info: Dictionary with query sequence information
        sequence_ids: List of matching sequence IDs
        similarities: List of similarity scores
    """
    print_section("Results")
    
    # Query information
    print("\n🔬 Query Sequence:")
    if "species" in query_info:
        print(f"   Species: {query_info['species']}")
    if "region" in query_info:
        print(f"   Region: {query_info['region']}")
    print(f"   Length: {query_info['length']} bp")
    
    # Results
    print(f"\n🎯 Top {len(sequence_ids)} Matches:\n")
    
    if not sequence_ids:
        print("   No matches found.")
        return
    
    # Table header
    print(f"{'Rank':<6} {'Sequence ID':<30} {'Similarity':<12} {'Match':<10}")
    print("-" * 80)
    
    # Table rows
    for i, (seq_id, similarity) in enumerate(zip(sequence_ids, similarities), 1):
        # Determine match quality
        if similarity >= 0.95:
            match = "Excellent"
        elif similarity >= 0.90:
            match = "Very Good"
        elif similarity >= 0.80:
            match = "Good"
        elif similarity >= 0.70:
            match = "Fair"
        else:
            match = "Poor"
        
        # Format similarity as percentage
        sim_pct = f"{similarity * 100:.2f}%"
        
        print(f"{i:<6} {seq_id:<30} {sim_pct:<12} {match:<10}")
    
    # Interpretation
    print("\n💡 Interpretation:")
    if similarities[0] >= 0.97:
        print("   ✅ Very high confidence match - likely same species")
    elif similarities[0] >= 0.95:
        print("   ✅ High confidence match - same species or very close relative")
    elif similarities[0] >= 0.90:
        print("   ⚠️  Moderate confidence - same genus or closely related")
    elif similarities[0] >= 0.80:
        print("   ⚠️  Low confidence - same family or distant relative")
    else:
        print("   ❌ Very low confidence - possibly different family or novel sequence")


def test_single_sequence(
    indexer: FAISSIndexer,
    sequence: str,
    metadata: Dict[str, Any] = None,
    k: int = 5
):
    """
    Test model with a single sequence.
    
    Args:
        indexer: Loaded FAISS indexer
        sequence: DNA sequence to test
        metadata: Optional metadata about the sequence
        k: Number of results to return
    """
    # Generate embedding
    embedding = generate_embedding(sequence)
    
    # Search for similar sequences
    sequence_ids, similarities = search_similar_sequences(indexer, embedding, k=k)
    
    # Display results
    query_info = metadata or {}
    query_info["length"] = len(sequence)
    display_results(query_info, sequence_ids, similarities)


def test_multiple_sequences(indexer: FAISSIndexer, k: int = 5):
    """
    Test model with multiple predefined test sequences.
    
    Args:
        indexer: Loaded FAISS indexer
        k: Number of results per query
    """
    print_header("Testing Multiple Sequences")
    
    for i, (name, info) in enumerate(TEST_SEQUENCES.items(), 1):
        print(f"\n\n{'#' * 80}")
        print(f"  Test {i}/{len(TEST_SEQUENCES)}: {name}")
        print(f"{'#' * 80}")
        
        test_single_sequence(
            indexer,
            info["sequence"],
            metadata={
                "species": info["species"],
                "region": info["region"],
                "length": info["length"]
            },
            k=k
        )


def calculate_embedding_statistics(sequences: List[str]):
    """
    Calculate and display embedding statistics for multiple sequences.
    
    Args:
        sequences: List of DNA sequences
    """
    print_section("Embedding Statistics")
    
    embeddings = []
    for seq in sequences:
        emb = embedding_service.embed_sequence(seq)
        embeddings.append(emb)
    
    embeddings = np.array(embeddings)
    
    print(f"Number of sequences: {len(sequences)}")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Mean: {embeddings.mean():.4f}")
    print(f"Std: {embeddings.std():.4f}")
    print(f"Min: {embeddings.min():.4f}")
    print(f"Max: {embeddings.max():.4f}")
    
    # Pairwise similarities
    print("\n📊 Pairwise Similarities:")
    seq_names = list(TEST_SEQUENCES.keys())
    
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = embedding_service.compute_similarity(embeddings[i], embeddings[j])
            print(f"   {seq_names[i]:<25} <-> {seq_names[j]:<25}: {sim:.4f}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test eDNA Species Classifier Model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default index and predefined sequences
  python test_model.py
  
  # Test with specific index
  python test_model.py --index-name model_edna_classifier_2
  
  # Test with custom sequence
  python test_model.py --sequence "ATGCGATCGATCG..."
  
  # Show embedding statistics only
  python test_model.py --stats-only
        """
    )
    
    parser.add_argument(
        "--index-name",
        type=str,
        default="model_edna_classifier_1",
        help="Name of the FAISS index to load (default: model_edna_classifier_1)"
    )
    
    parser.add_argument(
        "--sequence",
        type=str,
        help="Custom DNA sequence to test"
    )
    
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of similar sequences to return (default: 5)"
    )
    
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show embedding statistics without loading index"
    )
    
    args = parser.parse_args()
    
    # Print welcome message
    print_header("eDNA Species Classifier - Model Testing")
    print(f"Embedding dimension: {settings.model_embedding_dim}")
    print(f"MinIO endpoint: {settings.minio_endpoint}")
    
    # Stats only mode
    if args.stats_only:
        sequences = [info["sequence"] for info in TEST_SEQUENCES.values()]
        calculate_embedding_statistics(sequences)
        return
    
    # Load model
    indexer = load_model(args.index_name)
    
    # Test custom sequence
    if args.sequence:
        print_header("Testing Custom Sequence")
        test_single_sequence(indexer, args.sequence, k=args.k)
    else:
        # Test with predefined sequences
        test_multiple_sequences(indexer, k=args.k)
    
    # Summary
    print("\n" + "=" * 80)
    print("  Testing Complete!")
    print("=" * 80)
    print("\n💡 Tips:")
    print("   - Similarity ≥ 97%: Same species")
    print("   - Similarity 95-97%: Same species or very close relative")
    print("   - Similarity 90-95%: Same genus")
    print("   - Similarity 80-90%: Same family")
    print("   - Similarity < 80%: Distant or unrelated")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
