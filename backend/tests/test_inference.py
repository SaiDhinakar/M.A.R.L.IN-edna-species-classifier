#!/usr/bin/env python3
"""
Test the inference API with a sample DNA sequence.
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def login(username: str = "admin", password: str = "admin123"):
    """Login and get access token."""
    print("🔐 Logging in...")
    
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful!\n")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None


def test_inference(token: str, sequence: str):
    """Test model inference."""
    print(f"🧬 Testing inference...")
    print(f"   Sequence length: {len(sequence)} bp")
    print(f"   First 50 bp: {sequence[:50]}...\n")
    
    payload = {
        "sequence": sequence,
        "top_k": 5
    }
    
    response = requests.post(
        f"{API_BASE}/model/infer",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Inference successful!\n")
        print("📊 Results:")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Inference failed!")
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def main():
    print("=" * 60)
    print("🧬 M.A.R.L.IN Model Inference Test")
    print("=" * 60)
    print()
    
    # Login
    token = login()
    if not token:
        return
    
    # Sample 16S rRNA sequence (from E. coli)
    test_sequence = """
    AGAGTTTGATCCTGGCTCAGATTGAACGCTGGCGGCAGGCCTAACACATGCAAGTCGAACGGTAACAGGAAGAAGCTTGCTTCTTTGCT
    GACGAGTGGCGGACGGGTGAGTAATGTCTGGGAAACTGCCTGATGGAGGGGGATAACTACTGGAAACGGTAGCTAATACCGCATAACGTC
    GCAAGACCAAAGAGGGGGACCTTCGGGCCTCTTGCCATCGGATGTGCCCAGATGGGATTAGCTAGTAGGTGGGGTAACGGCTCACCTAGG
    CGACGATCCCTAGCTGGTCTGAGAGGATGACCAGCCACACTGGAACTGAGACACGGTCCAGACTCCTACGGGAGGCAGCAGTGGGGAATA
    TTGCACAATGGGCGCAAGCCTGATGCAGCCATGCCGCGTGTATGAAGAAGGCCTTCGGGTTGTAAAGTACTTTCAGCGGGGAGGAAGGG
    """.replace('\n', '').replace(' ', '').strip()
    
    # Test inference
    result = test_inference(token, test_sequence)
    
    if result:
        print("\n" + "=" * 60)
        print("🎉 Test completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Test failed")
        print("=" * 60)


if __name__ == "__main__":
    main()
