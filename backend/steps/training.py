"""
ZenML step for model training.
Implements TaxonomicClassifier and NoveltyDetector from notebook 05.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from typing import Tuple, Annotated, Dict
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from pathlib import Path
from zenml import step
import mlflow
import mlflow.pytorch


class TaxonomicClassifier(nn.Module):
    """Neural network for taxonomic classification"""
    
    def __init__(self, input_dim, num_classes, hidden_dims=[256, 128, 64], dropout_rate=0.3):
        super(TaxonomicClassifier, self).__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ])
            prev_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(prev_dim, num_classes))
        
        self.network = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.network(x)


class NoveltyDetector(nn.Module):
    """Autoencoder for novelty detection"""
    
    def __init__(self, input_dim, encoding_dims=[128, 64, 32], dropout_rate=0.2):
        super(NoveltyDetector, self).__init__()
        
        # Encoder
        encoder_layers = []
        prev_dim = input_dim
        
        for encoding_dim in encoding_dims:
            encoder_layers.extend([
                nn.Linear(prev_dim, encoding_dim),
                nn.BatchNorm1d(encoding_dim),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ])
            prev_dim = encoding_dim
        
        self.encoder = nn.Sequential(*encoder_layers)
        
        # Decoder
        decoder_layers = []
        decoding_dims = list(reversed(encoding_dims[:-1])) + [input_dim]
        
        for i, decoding_dim in enumerate(decoding_dims):
            if i == len(decoding_dims) - 1:  # Last layer
                decoder_layers.append(nn.Linear(prev_dim, decoding_dim))
            else:
                decoder_layers.extend([
                    nn.Linear(prev_dim, decoding_dim),
                    nn.BatchNorm1d(decoding_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout_rate)
                ])
            prev_dim = decoding_dim
        
        self.decoder = nn.Sequential(*decoder_layers)
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded, encoded
    
    def get_reconstruction_error(self, x):
        with torch.no_grad():
            decoded, _ = self.forward(x)
            mse = torch.mean((x - decoded) ** 2, dim=1)
            return mse.cpu().numpy()


class ModelTrainer:
    """Comprehensive model trainer for eDNA classification"""
    
    def __init__(self, device='cpu'):
        self.device = device
        self.models = {}
        self.scalers = {}
        self.training_history = {}
        
    def prepare_data(self, X, y, test_size=0.2, val_size=0.2):
        """Prepare train/validation/test splits"""
        # First split: separate test set
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Second split: separate train and validation
        val_size_adjusted = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size_adjusted, random_state=42, stratify=y_temp
        )
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def scale_features(self, X_train, X_val, X_test, scaler_name):
        """Scale features and store scaler"""
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        X_test_scaled = scaler.transform(X_test)
        
        self.scalers[scaler_name] = scaler
        
        return X_train_scaled, X_val_scaled, X_test_scaled
    
    def train_classifier(self, X_train, X_val, X_test, y_train, y_val, y_test, 
                        model_name, num_epochs=100, lr=0.001, batch_size=32):
        """Train taxonomic classifier"""
        print(f"Training {model_name} classifier...")
        
        # Scale features
        X_train_scaled, X_val_scaled, X_test_scaled = self.scale_features(
            X_train, X_val, X_test, f"{model_name}_scaler"
        )
        
        # Prepare data loaders
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train_scaled), 
            torch.LongTensor(y_train)
        )
        val_dataset = TensorDataset(
            torch.FloatTensor(X_val_scaled), 
            torch.LongTensor(y_val)
        )
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Initialize model
        num_classes = len(np.unique(np.concatenate([y_train, y_val, y_test])))
        model = TaxonomicClassifier(
            input_dim=X_train_scaled.shape[1],
            num_classes=num_classes
        ).to(self.device)
        
        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
        
        # Training loop
        train_losses = []
        val_losses = []
        val_accuracies = []
        best_val_acc = 0
        patience_counter = 0
        
        for epoch in range(num_epochs):
            # Training
            model.train()
            train_loss = 0
            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            # Validation
            model.eval()
            val_loss = 0
            correct = 0
            total = 0
            
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                    outputs = model(batch_X)
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()
                    
                    _, predicted = torch.max(outputs.data, 1)
                    total += batch_y.size(0)
                    correct += (predicted == batch_y).sum().item()
            
            train_loss /= len(train_loader)
            val_loss /= len(val_loader)
            val_acc = correct / total
            
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            val_accuracies.append(val_acc)
            
            scheduler.step(val_loss)
            
            # Early stopping
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save(model.state_dict(), f"{model_name}_best.pth")
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= 20:
                    print(f"Early stopping at epoch {epoch}")
                    break
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
        
        # Load best model
        model.load_state_dict(torch.load(f"{model_name}_best.pth"))
        
        # Evaluate on test set
        test_dataset = TensorDataset(torch.FloatTensor(X_test_scaled), torch.LongTensor(y_test))
        test_loader = DataLoader(test_dataset, batch_size=batch_size)
        
        model.eval()
        y_pred = []
        y_true = []
        
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                batch_X = batch_X.to(self.device)
                outputs = model(batch_X)
                _, predicted = torch.max(outputs.data, 1)
                y_pred.extend(predicted.cpu().numpy())
                y_true.extend(batch_y.numpy())
        
        test_acc = accuracy_score(y_true, y_pred)
        print(f"Test Accuracy: {test_acc:.4f}")
        
        # Store model and results
        self.models[model_name] = model
        self.training_history[model_name] = {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'val_accuracies': val_accuracies,
            'test_accuracy': test_acc,
            'y_true': y_true,
            'y_pred': y_pred
        }
        
        return model, test_acc
    
    def train_novelty_detector(self, X_train, X_val, X_test, model_name, 
                              num_epochs=100, lr=0.001, batch_size=32):
        """Train autoencoder for novelty detection"""
        print(f"Training {model_name} novelty detector...")
        
        # Scale features
        X_train_scaled, X_val_scaled, X_test_scaled = self.scale_features(
            X_train, X_val, X_test, f"{model_name}_scaler"
        )
        
        # Prepare data loaders (autoencoder uses input as target)
        train_dataset = TensorDataset(torch.FloatTensor(X_train_scaled), torch.FloatTensor(X_train_scaled))
        val_dataset = TensorDataset(torch.FloatTensor(X_val_scaled), torch.FloatTensor(X_val_scaled))
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Initialize model
        model = NoveltyDetector(input_dim=X_train_scaled.shape[1]).to(self.device)
        
        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
        
        # Training loop
        train_losses = []
        val_losses = []
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(num_epochs):
            # Training
            model.train()
            train_loss = 0
            for batch_X, batch_y in train_loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                
                optimizer.zero_grad()
                decoded, _ = model(batch_X)
                loss = criterion(decoded, batch_y)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            # Validation
            model.eval()
            val_loss = 0
            
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                    decoded, _ = model(batch_X)
                    loss = criterion(decoded, batch_y)
                    val_loss += loss.item()
            
            train_loss /= len(train_loader)
            val_loss /= len(val_loader)
            
            train_losses.append(train_loss)
            val_losses.append(val_loss)
            
            scheduler.step(val_loss)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), f"{model_name}_best.pth")
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= 20:
                    print(f"Early stopping at epoch {epoch}")
                    break
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch}: Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
        
        # Load best model
        model.load_state_dict(torch.load(f"{model_name}_best.pth"))
        
        # Store model and results
        self.models[model_name] = model
        self.training_history[model_name] = {
            'train_losses': train_losses,
            'val_losses': val_losses,
            'best_val_loss': best_val_loss
        }
        
        return model


@step
def train_models(
    embeddings: np.ndarray,
    labels: np.ndarray,
    model_output_dir: str = "./model",
    num_epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001
) -> Tuple[
    Annotated[Dict[str, object], "trained_models"],
    Annotated[Dict[str, dict], "training_history"]
]:
    """
    Train taxonomic classifier and novelty detector models.
    
    Args:
        embeddings: Input feature embeddings
        labels: Target labels for classification
        model_output_dir: Directory to save model checkpoints
        num_epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate for optimization
    
    Returns:
        Tuple of (trained_models_dict, training_history_dict)
    """
    with mlflow.start_run(nested=True, run_name="model_training"):
        # Log parameters
        mlflow.log_param("num_epochs", num_epochs)
        mlflow.log_param("batch_size", batch_size)
        mlflow.log_param("learning_rate", learning_rate)
        mlflow.log_param("embedding_dim", embeddings.shape[1])
        mlflow.log_param("num_samples", len(embeddings))
        
        # Initialize trainer
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        mlflow.log_param("device", device)
        
        trainer = ModelTrainer(device=device)
        
        # Prepare data splits
        X_train, X_val, X_test, y_train, y_val, y_test = trainer.prepare_data(embeddings, labels)
        
        # Train taxonomic classifier
        classifier, test_accuracy = trainer.train_classifier(
            X_train, X_val, X_test, y_train, y_val, y_test,
            model_name="taxonomic_classifier",
            num_epochs=num_epochs,
            lr=learning_rate,
            batch_size=batch_size
        )
        
        # Log classifier metrics
        mlflow.log_metric("classifier_test_accuracy", test_accuracy)
        mlflow.log_metric("classifier_train_loss_final", trainer.training_history["taxonomic_classifier"]["train_losses"][-1])
        mlflow.log_metric("classifier_val_loss_final", trainer.training_history["taxonomic_classifier"]["val_losses"][-1])
        
        # Train novelty detector (autoencoder)
        novelty_detector = trainer.train_novelty_detector(
            X_train, X_val, X_test,
            model_name="novelty_detector",
            num_epochs=num_epochs,
            lr=learning_rate,
            batch_size=batch_size
        )
        
        # Log novelty detector metrics
        mlflow.log_metric("novelty_train_loss_final", trainer.training_history["novelty_detector"]["train_losses"][-1])
        mlflow.log_metric("novelty_val_loss_final", trainer.training_history["novelty_detector"]["val_losses"][-1])
        
        # Log models to MLflow
        mlflow.pytorch.log_model(classifier, "taxonomic_classifier")
        mlflow.pytorch.log_model(novelty_detector, "novelty_detector")
        
        # Save models locally
        Path(model_output_dir).mkdir(parents=True, exist_ok=True)
        torch.save(classifier.state_dict(), f"{model_output_dir}/taxonomic_classifier.pth")
        torch.save(novelty_detector.state_dict(), f"{model_output_dir}/novelty_detector.pth")
        
        print(f"✅ Model training complete:")
        print(f"   Classifier test accuracy: {test_accuracy:.4f}")
        print(f"   Models saved to: {model_output_dir}")
        
        return trainer.models, trainer.training_history
