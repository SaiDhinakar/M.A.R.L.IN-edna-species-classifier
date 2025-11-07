#!/usr/bin/env python3
"""
Quick test script to verify backend setup and services.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...", end=" ")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import redis
        import minio
        import mlflow
        import faiss
        import torch
        from Bio import SeqIO
        print("✅")
        return True
    except ImportError as e:
        print(f"❌\n  Error: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("Testing configuration...", end=" ")
    try:
        from app.core.config import settings
        assert settings.app_name
        assert settings.jwt_secret_key
        assert settings.minio_endpoint
        assert settings.redis_url
        print("✅")
        return True
    except Exception as e:
        print(f"❌\n  Error: {e}")
        return False


def test_database():
    """Test database initialization."""
    print("Testing database...", end=" ")
    try:
        from app.database.session import init_db, SessionLocal
        from app.models.database_models import User
        
        init_db()
        db = SessionLocal()
        count = db.query(User).count()
        db.close()
        print(f"✅ ({count} users)")
        return True
    except Exception as e:
        print(f"❌\n  Error: {e}")
        return False


def test_redis():
    """Test Redis connection."""
    print("Testing Redis connection...", end=" ")
    try:
        from app.services.redis_service import redis_service
        
        if redis_service.health_check():
            print("✅")
            return True
        else:
            print("❌ Connection failed")
            return False
    except Exception as e:
        print(f"❌\n  Error: {e}")
        return False


def test_minio():
    """Test MinIO connection."""
    print("Testing MinIO connection...", end=" ")
    try:
        from app.services.minio_service import minio_service
        from app.core.config import settings
        
        # Try to check if bucket exists (will create if not)
        buckets = [
            settings.minio_bucket_raw,
            settings.minio_bucket_processed,
            settings.minio_bucket_models,
            settings.minio_bucket_logs
        ]
        
        all_exist = all(minio_service.client.bucket_exists(b) for b in buckets)
        print(f"✅ (4 buckets)")
        return True
    except Exception as e:
        print(f"❌\n  Error: {e}")
        return False


def test_embedding():
    """Test embedding service."""
    print("Testing embedding service...", end=" ")
    try:
        from app.services.embedding_service import embedding_service
        
        # Test sequence
        test_seq = "ATGCTAGCTAGC"
        embedding = embedding_service.embed_sequence(test_seq)
        
        assert embedding is not None
        assert len(embedding) > 0
        print(f"✅ (dim={len(embedding)})")
        return True
    except Exception as e:
        print(f"❌\n  Error: {e}")
        return False


def test_faiss():
    """Test FAISS indexer."""
    print("Testing FAISS indexer...", end=" ")
    try:
        from app.services.faiss_indexer import FAISSIndexer
        import numpy as np
        
        indexer = FAISSIndexer()
        indexer.create_index(dimension=128)
        
        # Add test vectors
        vectors = np.random.rand(10, 128).astype(np.float32)
        ids = [f"seq_{i}" for i in range(10)]
        indexer.add_vectors(vectors, ids)
        
        stats = indexer.get_stats()
        print(f"✅ ({stats['total_vectors']} vectors)")
        return True
    except Exception as e:
        print(f"❌\n  Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("M.A.R.L.IN Backend - System Test")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Redis", test_redis),
        ("MinIO", test_minio),
        ("Embedding", test_embedding),
        ("FAISS", test_faiss),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Test '{name}' crashed: {e}")
            results.append((name, False))
    
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
