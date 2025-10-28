# backend/steps/embedding.py

from typing import Tuple
from zenml import step
from sklearn.decomposition import PCA
import numpy as np

@step
def embedding_step(X_train: np.ndarray, X_test: np.ndarray, n_components: int = 2) -> Tuple[np.ndarray, np.ndarray]:
    """Create low-dimensional embeddings (PCA) for features."""
    print("[3/6] 🧠 Generating feature embeddings (PCA)...")
    if X_train.shape[1] < n_components:
        n_components = X_train.shape[1]
        print(f"[   ] Warning: requested n_components reduced to {n_components} (feature dim).")

    pca = PCA(n_components=n_components, random_state=42)
    X_train_emb = pca.fit_transform(X_train)
    X_test_emb = pca.transform(X_test)

    print(f"[✔] Embedding generation completed. Train shape: {X_train_emb.shape}")
    return X_train_emb, X_test_emb
