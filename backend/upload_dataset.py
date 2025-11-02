#!/usr/bin/env python3
"""
Upload a dataset file to the backend API.
"""

import requests
import sys
import os

API_BASE = "http://localhost:8000/api/v1"


def login(username: str = "admin", password: str = "admin123"):
    """Login and get access token."""
    print(f"🔐 Logging in as {username}...")
    
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={
            "username": username,
            "password": password
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful!")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        sys.exit(1)


def upload_dataset(token: str, file_path: str):
    """Upload a dataset file."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    print(f"\n📤 Uploading dataset...")
    print(f"   File: {file_name}")
    print(f"   Size: {file_size / (1024*1024):.2f} MB")
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f, 'application/gzip')}
        
        response = requests.post(
            f"{API_BASE}/dataset/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files
        )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print("\n✅ Upload successful!")
        print(f"   Dataset ID: {result.get('id', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Filename: {result.get('filename', 'N/A')}")
        return result
    else:
        print(f"\n❌ Upload failed!")
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)


def approve_dataset(token: str, dataset_id: int):
    """Approve a dataset."""
    print(f"\n✅ Approving dataset {dataset_id}...")
    
    response = requests.post(
        f"{API_BASE}/admin/datasets/{dataset_id}/approve",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        print("✅ Dataset approved!")
        return True
    else:
        print(f"⚠️  Approval failed: {response.text}")
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python upload_dataset.py <file_path>")
        print("\nExample:")
        print("  python upload_dataset.py data/archives/16S_ribosomal_RNA_sequences.tar.gz")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("=" * 75)
    print("🧬 M.A.R.L.IN Dataset Upload Script")
    print("=" * 75)
    
    # Login
    token = login()
    
    # Upload
    result = upload_dataset(token, file_path)
    
    # Approve
    dataset_id = result.get('id')
    if dataset_id:
        approve_dataset(token, dataset_id)
        
        print("\n" + "=" * 75)
        print("🎉 Dataset uploaded and approved!")
        print("=" * 75)
        print(f"\nDataset ID: {dataset_id}")
        print("\nTrigger training with:")
        print(f"  python trigger_training.py")
    else:
        print("\n⚠️  Dataset uploaded but couldn't retrieve ID")


if __name__ == "__main__":
    main()
