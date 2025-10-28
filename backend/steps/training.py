# backend/steps/training.py

from zenml import step
from sklearn.ensemble import RandomForestClassifier
import numpy as np

@step
def training_step(X_train_emb: np.ndarray, y_train, n_estimators: int = 100, random_state: int = 42):
    """Train a RandomForest classifier on the provided embedded training data."""
    print("[5/6] 🏋️‍♂️ Training model...")
    if X_train_emb.shape[0] == 0:
        raise ValueError("No training samples provided for training.")

    model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
    model.fit(X_train_emb, y_train)

    print("[✔] Model training completed.")
    return model
