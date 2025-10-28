# backend/steps/evaluate.py

from zenml import step
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

@step
def evaluate_step(model, X_test_emb: np.ndarray, y_test):
    """Evaluate the trained model and print metrics."""
    print("[6/6] 🧪 Evaluating model...")
    if X_test_emb.shape[0] == 0:
        raise ValueError("No test samples provided for evaluation.")

    preds = model.predict(X_test_emb)
    acc = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds, zero_division=0)

    print(f"[✔] Evaluation completed. Accuracy: {acc:.4f}")
    print("Classification report:\n", report)
    return {"accuracy": float(acc), "report": report}
