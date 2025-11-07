#!/usr/bin/env python3
"""Check MinIO buckets for model files."""

import sys
sys.path.insert(0, '/run/media/spidey/35f48b83-0fe4-4b1f-ba92-81ad5e6b81f61/M.A.R.L.IN-edna-species-classifier/backend')

from app.services.minio_service import minio_service
from app.core.config import settings

print("=" * 60)
print("MinIO Model Files (FAISS Indexes)")
print("=" * 60)

try:
    files = list(minio_service.client.list_objects(settings.minio_bucket_models, recursive=True))
    
    if files:
        print(f"\nFound {len(files)} file(s) in '{settings.minio_bucket_models}' bucket:\n")
        for obj in files:
            size_mb = obj.size / (1024 * 1024)
            print(f"  📁 {obj.object_name}")
            print(f"     Size: {size_mb:.2f} MB ({obj.size} bytes)")
            print(f"     Modified: {obj.last_modified}")
            print()
    else:
        print(f"\n⚠️  No files found in '{settings.minio_bucket_models}' bucket")
        print("   This means FAISS indexes were not saved during training.")
        
except Exception as e:
    print(f"\n❌ Error listing files: {e}")

print("\n" + "=" * 60)
print("MinIO Processed Data Files")
print("=" * 60)

try:
    files = list(minio_service.client.list_objects(settings.minio_bucket_processed, recursive=True))
    
    if files:
        print(f"\nFound {len(files)} file(s) in '{settings.minio_bucket_processed}' bucket:\n")
        for obj in files:
            size_mb = obj.size / (1024 * 1024)
            print(f"  📁 {obj.object_name}")
            print(f"     Size: {size_mb:.2f} MB ({obj.size} bytes)")
            print(f"     Modified: {obj.last_modified}")
            print()
    else:
        print(f"\n⚠️  No files found in '{settings.minio_bucket_processed}' bucket")
        
except Exception as e:
    print(f"\n❌ Error listing files: {e}")
