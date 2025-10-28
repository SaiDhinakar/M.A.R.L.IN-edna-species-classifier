# backend/steps/clustering.py

from typing import Any
from zenml import step
from sklearn.cluster import KMeans
import numpy as np

@step
def clustering_step(X_train_emb: np.ndarray, n_clusters: int = 3) -> Any:
    """Perform KMeans clustering on embeddings and return fitted KMeans object."""
    print("[4/6] 🔍 Performing clustering...")
    if X_train_emb.shape[0] < n_clusters:
        n_clusters = max(1, X_train_emb.shape[0])
        print(f"[   ] Adjusted n_clusters to {n_clusters} due to small sample size.")

    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(X_train_emb)

    print(f"[✔] Clustering completed. Found {n_clusters} clusters.")
    return kmeans
