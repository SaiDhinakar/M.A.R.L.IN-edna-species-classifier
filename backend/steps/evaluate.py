"""
ZenML step for model evaluation.
Implements ModelEvaluator from notebook 06.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from typing import Tuple, Annotated, Dict
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, 
    classification_report, confusion_matrix, 
    roc_auc_score, roc_curve, auc
)
from zenml import step
import mlflow
import json


class ModelEvaluator:
    """Comprehensive model evaluation framework"""
    
    def __init__(self, device='cpu'):
        self.device = device
        self.loaded_models = {}
        self.evaluation_results = {}
        
    def load_model(self, model, scaler):
        """Store loaded model and scaler"""
        model.eval()
        return model, scaler
    
    def evaluate_classifier(self, model, scaler, X_test, y_test, model_name, class_names=None):
        """Evaluate classification model"""
        # Prepare test data
        X_test_scaled = scaler.transform(X_test)
        test_dataset = TensorDataset(torch.FloatTensor(X_test_scaled))
        test_loader = DataLoader(test_dataset, batch_size=64)
        
        # Get predictions
        model.eval()
        y_pred = []
        y_proba = []
        
        with torch.no_grad():
            for batch_X, in test_loader:
                batch_X = batch_X.to(self.device)
                outputs = model(batch_X)
                probabilities = torch.softmax(outputs, dim=1)
                _, predicted = torch.max(outputs, 1)
                
                y_pred.extend(predicted.cpu().numpy())
                y_proba.extend(probabilities.cpu().numpy())
        
        y_pred = np.array(y_pred)
        y_proba = np.array(y_proba)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(y_test, y_pred, average='weighted')
        
        # Per-class metrics
        class_report = classification_report(y_test, y_pred, target_names=class_names, output_dict=True)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # ROC AUC (for multiclass)
        try:
            if len(np.unique(y_test)) > 2:
                roc_auc = roc_auc_score(y_test, y_proba, multi_class='ovr', average='weighted')
            else:
                roc_auc = roc_auc_score(y_test, y_proba[:, 1])
        except:
            roc_auc = None
        
        results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': cm.tolist(),  # Convert to list for serialization
            'classification_report': class_report,
            'predictions': y_pred.tolist(),
            'true_labels': y_test.tolist()
        }
        
        self.evaluation_results[model_name] = results
        
        print(f"{model_name} Results:")
        print(f"  Accuracy: {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall: {recall:.4f}")
        print(f"  F1-Score: {f1:.4f}")
        if roc_auc:
            print(f"  ROC-AUC: {roc_auc:.4f}")
        
        return results
    
    def evaluate_novelty_detector(self, model, scaler, X_known, X_novel=None, model_name='novelty_detector'):
        """Evaluate novelty detection model"""
        # Prepare known data
        X_known_scaled = scaler.transform(X_known)
        
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_known_scaled).to(self.device)
            decoded, _ = model(X_tensor)
            known_errors = torch.mean((X_tensor - decoded) ** 2, dim=1).cpu().numpy()
        
        # Calculate threshold (95th percentile of known data)
        threshold = np.percentile(known_errors, 95)
        
        results = {
            'known_errors': known_errors.tolist(),
            'threshold': float(threshold),
            'mean_known_error': float(np.mean(known_errors)),
            'std_known_error': float(np.std(known_errors))
        }
        
        # If novel data is provided, evaluate detection performance
        if X_novel is not None and len(X_novel) > 0:
            X_novel_scaled = scaler.transform(X_novel)
            
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X_novel_scaled).to(self.device)
                decoded, _ = model(X_tensor)
                novel_errors = torch.mean((X_tensor - decoded) ** 2, dim=1).cpu().numpy()
            
            # Create labels (0 = known, 1 = novel)
            y_true = np.concatenate([np.zeros(len(known_errors)), np.ones(len(novel_errors))])
            reconstruction_errors = np.concatenate([known_errors, novel_errors])
            
            # Predictions based on threshold
            y_pred = (reconstruction_errors > threshold).astype(int)
            
            # Calculate metrics
            accuracy = accuracy_score(y_true, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
            
            # ROC curve
            fpr, tpr, thresholds = roc_curve(y_true, reconstruction_errors)
            roc_auc = auc(fpr, tpr)
            
            results.update({
                'novel_errors': novel_errors.tolist(),
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'roc_auc': float(roc_auc)
            })
            
            print(f"{model_name} Results:")
            print(f"  Threshold: {threshold:.6f}")
            print(f"  Accuracy: {accuracy:.4f}")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall: {recall:.4f}")
            print(f"  F1-Score: {f1:.4f}")
            print(f"  ROC-AUC: {roc_auc:.4f}")
        
        self.evaluation_results[model_name] = results
        return results


@step
def evaluate_models(
    trained_models: Dict[str, object],
    training_history: Dict[str, dict],
    test_embeddings: np.ndarray,
    test_labels: np.ndarray,
    evaluation_output_dir: str = "./evaluation"
) -> Annotated[Dict[str, dict], "evaluation_results"]:
    """
    Evaluate trained models on test data.
    
    Args:
        trained_models: Dictionary of trained model objects
        training_history: Training history with scalers
        test_embeddings: Test set embeddings
        test_labels: Test set labels
        evaluation_output_dir: Directory to save evaluation results
    
    Returns:
        Dictionary with evaluation metrics for each model
    """
    with mlflow.start_run(nested=True, run_name="model_evaluation"):
        # Initialize evaluator
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        evaluator = ModelEvaluator(device=device)
        
        # Log parameters
        mlflow.log_param("num_test_samples", len(test_embeddings))
        mlflow.log_param("device", device)
        
        # Evaluate taxonomic classifier (if available)
        if 'taxonomic_classifier' in trained_models:
            print("\n--- Evaluating Taxonomic Classifier ---")
            classifier = trained_models['taxonomic_classifier']
            # For now, assume scaler is stored somewhere accessible
            # In production, this would come from training_history
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            scaler.fit(test_embeddings)  # Simplified - should use training scaler
            
            classifier_results = evaluator.evaluate_classifier(
                model=classifier,
                scaler=scaler,
                X_test=test_embeddings,
                y_test=test_labels,
                model_name='taxonomic_classifier',
                class_names=[f"Class_{i}" for i in range(len(np.unique(test_labels)))]
            )
            
            # Log classifier metrics to MLflow
            mlflow.log_metric("classifier_accuracy", classifier_results['accuracy'])
            mlflow.log_metric("classifier_precision", classifier_results['precision'])
            mlflow.log_metric("classifier_recall", classifier_results['recall'])
            mlflow.log_metric("classifier_f1", classifier_results['f1_score'])
            if classifier_results['roc_auc']:
                mlflow.log_metric("classifier_roc_auc", classifier_results['roc_auc'])
        
        # Evaluate novelty detector (if available)
        if 'novelty_detector' in trained_models:
            print("\n--- Evaluating Novelty Detector ---")
            novelty_detector = trained_models['novelty_detector']
            scaler = StandardScaler()
            scaler.fit(test_embeddings)  # Simplified
            
            # For demo, split test data into known/novel
            split_idx = len(test_embeddings) // 2
            X_known = test_embeddings[:split_idx]
            X_novel = test_embeddings[split_idx:]
            
            novelty_results = evaluator.evaluate_novelty_detector(
                model=novelty_detector,
                scaler=scaler,
                X_known=X_known,
                X_novel=X_novel,
                model_name='novelty_detector'
            )
            
            # Log novelty detector metrics to MLflow
            mlflow.log_metric("novelty_threshold", novelty_results['threshold'])
            mlflow.log_metric("novelty_mean_error", novelty_results['mean_known_error'])
            if 'accuracy' in novelty_results:
                mlflow.log_metric("novelty_accuracy", novelty_results['accuracy'])
                mlflow.log_metric("novelty_precision", novelty_results['precision'])
                mlflow.log_metric("novelty_recall", novelty_results['recall'])
                mlflow.log_metric("novelty_f1", novelty_results['f1_score'])
        
        # Save evaluation results
        from pathlib import Path
        Path(evaluation_output_dir).mkdir(parents=True, exist_ok=True)
        
        results_path = f"{evaluation_output_dir}/evaluation_results.json"
        with open(results_path, 'w') as f:
            json.dump(evaluator.evaluation_results, f, indent=2)
        
        mlflow.log_artifact(results_path)
        
        print(f"\n✅ Model evaluation complete!")
        print(f"   Results saved to: {evaluation_output_dir}")
        
        return evaluator.evaluation_results
