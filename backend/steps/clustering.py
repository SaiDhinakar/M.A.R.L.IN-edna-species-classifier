"""
ZenML step for sequence clustering.
Implements multiple clustering algorithms from notebook 03.
"""

import numpy as np
import pandas as pd
import hdbscan
from typing import Tuple, Annotated, Dict
from sklearn.cluster import DBSCAN, KMeans, GaussianMixture
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from zenml import step
import mlflow


class SequenceClusterer:
    """Comprehensive sequence clustering with multiple algorithms"""
    
    def __init__(self, embeddings, sequences_df):
        self.embeddings = embeddings
        self.sequences_df = sequences_df
        self.clusterers = {}
        self.cluster_results = {}
        self.cluster_metrics = {}
        
    def optimize_dbscan_parameters(self, sample_size=1000):
        """Optimize DBSCAN parameters using k-distance plot"""
        print("Optimizing DBSCAN parameters...")
        
        # Sample data for parameter optimization
        if len(self.embeddings) > sample_size:
            indices = np.random.choice(len(self.embeddings), sample_size, replace=False)
            sample_embeddings = self.embeddings[indices]
        else:
            sample_embeddings = self.embeddings
        
        # Calculate k-distance plot for different k values
        k_values = [3, 5, 10, 15, 20]
        eps_candidates = []
        
        for k in k_values:
            neighbors = NearestNeighbors(n_neighbors=k)
            neighbors_fit = neighbors.fit(sample_embeddings)
            distances, indices = neighbors_fit.kneighbors(sample_embeddings)
            
            # Sort distances and find elbow point
            k_distances = np.sort(distances[:, k-1], axis=0)
            
            # Simple elbow detection (find point with max curvature)
            if len(k_distances) > 10:
                # Calculate second derivative
                second_derivative = np.diff(k_distances, n=2)
                elbow_idx = np.argmax(second_derivative) + 2
                eps_candidate = k_distances[elbow_idx]
                eps_candidates.append(eps_candidate)
        
        # Use median of candidates as optimal eps
        optimal_eps = np.median(eps_candidates) if eps_candidates else 0.5
        
        print(f"Optimal eps estimated: {optimal_eps:.4f}")
        return optimal_eps
    
    def apply_dbscan(self, eps=None, min_samples=5):
        """Apply DBSCAN clustering"""
        print(f"Applying DBSCAN clustering...")
        
        if eps is None:
            eps = self.optimize_dbscan_parameters()
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(self.embeddings)
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
        cluster_labels = dbscan.fit_predict(embeddings_scaled)
        
        self.clusterers['dbscan'] = dbscan
        self.cluster_results['dbscan'] = cluster_labels
        
        # Calculate metrics
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        metrics = {
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'noise_ratio': n_noise / len(cluster_labels),
            'eps': eps,
            'min_samples': min_samples
        }
        
        if n_clusters > 1:
            # Calculate silhouette score (excluding noise points)
            non_noise_mask = cluster_labels != -1
            if np.sum(non_noise_mask) > 1:
                metrics['silhouette_score'] = silhouette_score(
                    embeddings_scaled[non_noise_mask], 
                    cluster_labels[non_noise_mask]
                )
        
        self.cluster_metrics['dbscan'] = metrics
        
        print(f"DBSCAN results: {n_clusters} clusters, {n_noise} noise points")
        print(f"Noise ratio: {metrics['noise_ratio']:.3f}")
        
        return cluster_labels
    
    def apply_hdbscan(self, min_cluster_size=10, min_samples=5):
        """Apply HDBSCAN clustering"""
        print(f"Applying HDBSCAN clustering...")
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(self.embeddings)
        
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            cluster_selection_epsilon=0.0
        )
        cluster_labels = clusterer.fit_predict(embeddings_scaled)
        
        self.clusterers['hdbscan'] = clusterer
        self.cluster_results['hdbscan'] = cluster_labels
        
        # Calculate metrics
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        metrics = {
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'noise_ratio': n_noise / len(cluster_labels),
            'min_cluster_size': min_cluster_size,
            'min_samples': min_samples
        }
        
        if n_clusters > 1:
            non_noise_mask = cluster_labels != -1
            if np.sum(non_noise_mask) > 1:
                metrics['silhouette_score'] = silhouette_score(
                    embeddings_scaled[non_noise_mask], 
                    cluster_labels[non_noise_mask]
                )
        
        self.cluster_metrics['hdbscan'] = metrics
        
        print(f"HDBSCAN results: {n_clusters} clusters, {n_noise} noise points")
        print(f"Noise ratio: {metrics['noise_ratio']:.3f}")
        
        return cluster_labels
    
    def apply_kmeans(self, n_clusters_range=(5, 50)):
        """Apply K-means with optimal cluster number selection"""
        print(f"Applying K-means clustering...")
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(self.embeddings)
        
        # Find optimal number of clusters using elbow method and silhouette score
        k_range = range(max(2, n_clusters_range[0]), 
                       min(len(self.embeddings)//2, n_clusters_range[1]))
        
        silhouette_scores = []
        inertias = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings_scaled)
            
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(embeddings_scaled, cluster_labels))
        
        # Find optimal k (max silhouette score)
        optimal_k = k_range[np.argmax(silhouette_scores)]
        
        # Apply K-means with optimal k
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings_scaled)
        
        self.clusterers['kmeans'] = kmeans
        self.cluster_results['kmeans'] = cluster_labels
        
        metrics = {
            'n_clusters': optimal_k,
            'silhouette_score': max(silhouette_scores),
            'inertia': kmeans.inertia_,
            'calinski_harabasz_score': calinski_harabasz_score(embeddings_scaled, cluster_labels),
            'davies_bouldin_score': davies_bouldin_score(embeddings_scaled, cluster_labels)
        }
        
        self.cluster_metrics['kmeans'] = metrics
        
        print(f"K-means results: {optimal_k} clusters")
        print(f"Silhouette score: {metrics['silhouette_score']:.3f}")
        
        return cluster_labels
    
    def apply_gaussian_mixture(self, n_components_range=(5, 30)):
        """Apply Gaussian Mixture Models"""
        print(f"Applying Gaussian Mixture Models...")
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(self.embeddings)
        
        # Find optimal number of components using BIC/AIC
        n_range = range(max(2, n_components_range[0]), 
                       min(len(self.embeddings)//3, n_components_range[1]))
        
        bic_scores = []
        aic_scores = []
        
        for n in n_range:
            gmm = GaussianMixture(n_components=n, random_state=42)
            gmm.fit(embeddings_scaled)
            bic_scores.append(gmm.bic(embeddings_scaled))
            aic_scores.append(gmm.aic(embeddings_scaled))
        
        # Find optimal n (min BIC)
        optimal_n = n_range[np.argmin(bic_scores)]
        
        # Apply GMM with optimal n
        gmm = GaussianMixture(n_components=optimal_n, random_state=42)
        cluster_labels = gmm.fit_predict(embeddings_scaled)
        
        self.clusterers['gmm'] = gmm
        self.cluster_results['gmm'] = cluster_labels
        
        metrics = {
            'n_clusters': optimal_n,
            'bic_score': min(bic_scores),
            'aic_score': min(aic_scores),
            'silhouette_score': silhouette_score(embeddings_scaled, cluster_labels)
        }
        
        self.cluster_metrics['gmm'] = metrics
        
        print(f"GMM results: {optimal_n} clusters")
        print(f"BIC score: {metrics['bic_score']:.3f}")
        
        return cluster_labels


@step
def cluster_sequences(
    embeddings: np.ndarray,
    sequences_df: pd.DataFrame,
    clustering_methods: list = ['hdbscan', 'dbscan', 'kmeans', 'gmm']
) -> Tuple[
    Annotated[Dict[str, np.ndarray], "cluster_labels"],
    Annotated[Dict[str, dict], "cluster_metrics"]
]:
    """
    Cluster sequences using multiple algorithms.
    
    Args:
        embeddings: Sequence embeddings array
        sequences_df: DataFrame with sequence metadata
        clustering_methods: List of methods to apply
    
    Returns:
        Tuple of (cluster_labels_dict, metrics_dict)
    """
    with mlflow.start_run(nested=True, run_name="clustering"):
        # Log parameters
        mlflow.log_param("clustering_methods", clustering_methods)
        mlflow.log_param("num_sequences", len(sequences_df))
        mlflow.log_param("embedding_dim", embeddings.shape[1])
        
        # Initialize clusterer
        clusterer = SequenceClusterer(embeddings, sequences_df)
        
        # Apply requested clustering methods
        cluster_labels = {}
        
        for method in clustering_methods:
            if method == 'hdbscan':
                labels = clusterer.apply_hdbscan()
                cluster_labels['hdbscan'] = labels
                
            elif method == 'dbscan':
                labels = clusterer.apply_dbscan()
                cluster_labels['dbscan'] = labels
                
            elif method == 'kmeans':
                labels = clusterer.apply_kmeans()
                cluster_labels['kmeans'] = labels
                
            elif method == 'gmm':
                labels = clusterer.apply_gaussian_mixture()
                cluster_labels['gmm'] = labels
        
        # Log metrics for each method
        for method, metrics in clusterer.cluster_metrics.items():
            for metric_name, metric_value in metrics.items():
                mlflow.log_metric(f"{method}_{metric_name}", metric_value)
        
        print(f"✅ Clustering complete with methods: {clustering_methods}")
        
        return cluster_labels, clusterer.cluster_metrics
