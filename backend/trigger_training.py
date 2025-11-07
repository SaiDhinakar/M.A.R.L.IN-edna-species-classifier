#!/usr/bin/env python3
"""
Script to trigger training on a dataset.
"""

import requests
import json
import sys

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


def list_datasets(token: str):
    """List all datasets."""
    print("\n📋 Fetching datasets...")
    
    response = requests.get(
        f"{API_BASE}/admin/datasets/pending",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n{'ID':<5} {'Filename':<40} {'Status':<15} {'Sequences':<10}")
        print("-" * 75)
        
        for dataset in data["datasets"]:
            print(f"{dataset['id']:<5} {dataset['original_filename']:<40} {dataset['status']:<15} {dataset.get('num_sequences', 'N/A'):<10}")
        
        return data["datasets"]
    else:
        print(f"❌ Failed to fetch datasets: {response.text}")
        return []


def trigger_training(token: str, dataset_id: int, model_name: str = "edna_classifier_v1"):
    """Trigger training on a dataset."""
    print(f"\n🚀 Triggering training on dataset {dataset_id}...")
    
    payload = {
        "dataset_ids": [dataset_id],
        "model_name": model_name,
        "hyperparameters": {
            "min_length": 100,
            "max_length": 10000,
            "min_cluster_size": 5,
            "min_samples": 3,
            "embedding_batch_size": 32
        }
    }
    
    print(f"📦 Request payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{API_BASE}/admin/train",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 202:
        result = response.json()
        print("\n✅ Training initiated successfully!")
        print(f"   Training Run ID: {result['id']}")
        print(f"   Status: {result['status']}")
        print(f"   Started at: {result['started_at']}")
        return result
    else:
        print(f"\n❌ Training failed!")
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def check_training_status(token: str, training_run_id: int):
    """Check training run status."""
    print(f"\n🔍 Checking training run {training_run_id}...")
    
    response = requests.get(
        f"{API_BASE}/admin/training-runs/{training_run_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        run = response.json()
        print(f"\n📊 Training Run Status:")
        print(f"   ID: {run['id']}")
        print(f"   Status: {run['status']}")
        print(f"   Dataset ID: {run['dataset_id']}")
        print(f"   Pipeline: {run['pipeline_name']}")
        
        if run.get('num_sequences_processed'):
            print(f"   Sequences Processed: {run['num_sequences_processed']}")
        
        if run.get('num_clusters_found'):
            print(f"   Clusters Found: {run['num_clusters_found']}")
        
        if run.get('metrics'):
            print(f"   Metrics: {json.dumps(run['metrics'], indent=6)}")
        
        if run.get('error_log'):
            print(f"   ⚠️  Error: {run['error_log']}")
        
        return run
    else:
        print(f"❌ Failed to fetch training run: {response.text}")
        return None


def main():
    """Main function."""
    print("=" * 75)
    print("🧬 M.A.R.L.IN Training Trigger Script")
    print("=" * 75)
    
    # Login
    token = login()
    
    # For now, directly use dataset ID 2 (the latest uploaded FASTA dataset)
    # TODO: Add endpoint to list all datasets regardless of status
    dataset_id = 2
    
    print(f"\n📌 Using dataset ID: {dataset_id}")
    print("   (Assuming dataset exists and is approved)")
    
    # Trigger training
    result = trigger_training(token, dataset_id)
    
    if result:
        print("\n" + "=" * 75)
        print("🎉 Training has been initiated!")
        print("=" * 75)
        print("\nMonitor progress with:")
        print(f"   python trigger_training.py --check {result['id']}")
        print("\nOr via API:")
        print(f"   curl http://localhost:8000/api/v1/admin/training-runs/{result['id']} \\")
        print(f"     -H 'Authorization: Bearer {token}'")
    else:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        if len(sys.argv) < 3:
            print("Usage: python trigger_training.py --check <training_run_id>")
            sys.exit(1)
        
        token = login()
        training_run_id = int(sys.argv[2])
        check_training_status(token, training_run_id)
    else:
        main()
