#!/usr/bin/env python3
"""
Diagnostic script to check cluster assignments in processed data.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import tempfile
import os
import pandas as pd
from app.services.minio_service import minio_service
from app.core.config import settings


def check_clusters():
    """Check cluster assignments in processed parquet files."""
    
    print("=" * 80)
    print("Cluster Diagnostics - Checking Processed Data")
    print("=" * 80)
    
    try:
        # List all processed files in MinIO
        files = list(minio_service.client.list_objects(
            settings.minio_bucket_processed, 
            prefix="processed/",
            recursive=True
        ))
        
        if not files:
            print("\n❌ No processed files found in MinIO!")
            print("   You need to run training first to generate processed data.")
            return
        
        print(f"\n✅ Found {len(files)} processed file(s):\n")
        
        for obj in files:
            if not obj.object_name.endswith('.parquet'):
                continue
                
            print(f"📊 Analyzing: {obj.object_name}")
            print("-" * 80)
            
            # Download and analyze
            with tempfile.TemporaryDirectory() as tmpdir:
                local_path = os.path.join(tmpdir, "temp.parquet")
                
                minio_service.download_file(
                    obj.object_name,
                    settings.minio_bucket_processed,
                    local_path
                )
                
                # Load parquet
                df = pd.read_parquet(local_path)
                
                print(f"\n📈 Dataset Statistics:")
                print(f"   Total sequences: {len(df)}")
                print(f"   Columns: {list(df.columns)}")
                
                if 'cluster_id' in df.columns:
                    cluster_counts = df['cluster_id'].value_counts().sort_index()
                    
                    n_noise = (df['cluster_id'] == -1).sum()
                    n_clustered = len(df) - n_noise
                    n_clusters = len(cluster_counts[cluster_counts.index != -1])
                    
                    print(f"\n🔬 Cluster Analysis:")
                    print(f"   Unique clusters: {n_clusters}")
                    print(f"   Clustered sequences: {n_clustered} ({n_clustered/len(df)*100:.1f}%)")
                    print(f"   Noise points (cluster -1): {n_noise} ({n_noise/len(df)*100:.1f}%)")
                    
                    print(f"\n📊 Cluster Distribution (top 10):")
                    for cluster_id, count in cluster_counts.head(10).items():
                        if cluster_id == -1:
                            print(f"   Cluster {cluster_id:3d} (NOISE): {count:5d} sequences")
                        else:
                            print(f"   Cluster {cluster_id:3d}:         {count:5d} sequences")
                    
                    if len(cluster_counts) > 10:
                        print(f"   ... and {len(cluster_counts) - 10} more clusters")
                    
                    # Sample some sequences from different clusters
                    print(f"\n🔍 Sample Sequences by Cluster:")
                    for cluster_id in cluster_counts.head(5).index:
                        cluster_samples = df[df['cluster_id'] == cluster_id].head(2)
                        
                        label = "NOISE" if cluster_id == -1 else f"Cluster {cluster_id}"
                        print(f"\n   {label}:")
                        for idx, row in cluster_samples.iterrows():
                            seq_id = row.get('sequence_id', 'unknown')
                            seq_len = row.get('sequence_length', len(row.get('sequence', '')))
                            print(f"      • {seq_id} (length: {seq_len})")
                else:
                    print("\n⚠️  WARNING: 'cluster_id' column not found!")
                    print("   The training pipeline may not have completed clustering.")
                
                print("\n" + "=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    check_clusters()
    
    print("\n💡 Interpretation:")
    print("   • If cluster_id = -1: HDBSCAN marked it as 'noise' (doesn't fit any cluster)")
    print("   • Noise points are expected for diverse datasets")
    print("   • High noise (>50%) suggests:")
    print("     - Dataset is very diverse (many unique species)")
    print("     - min_cluster_size is too large")
    print("     - Sequences are too dissimilar to cluster well")
    print("\n📝 Solution for high noise:")
    print("   • Retrain with lower min_cluster_size (default: 5, try: 2-3)")
    print("   • Use lower min_samples (default: 3, try: 1-2)")
    print("   • Or accept that prediction will use species_name instead of cluster_id")
    print()


if __name__ == "__main__":
    main()
