"""
Model evaluation utilities for clustering and classification metrics.

Provides comprehensive evaluation metrics for trained models:
- Clustering quality metrics
- Classification accuracy (if ground truth available)
- Diversity metrics
- Cluster statistics
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_rand_score,
    normalized_mutual_info_score,
    homogeneity_score,
    completeness_score,
    v_measure_score
)
from collections import Counter
import logging

from app.utils.logger import get_logger

logger = get_logger(__name__, log_file="logs/evaluation.log")


class ModelEvaluator:
    """Calculate comprehensive evaluation metrics for trained models."""
    
    @staticmethod
    def evaluate_clustering(
        embeddings: np.ndarray,
        cluster_labels: np.ndarray,
        min_cluster_size: int = 5
    ) -> Dict[str, Any]:
        """
        Evaluate clustering quality using multiple metrics.
        
        Args:
            embeddings: Array of embeddings (n_samples, n_features)
            cluster_labels: Cluster assignments (n_samples,)
            min_cluster_size: Minimum cluster size used in clustering
            
        Returns:
            Dictionary of clustering metrics
        """
        logger.info(f"Evaluating clustering: {len(embeddings)} samples, {len(np.unique(cluster_labels))} unique clusters")
        
        metrics = {}
        
        # Basic cluster statistics
        unique_clusters = np.unique(cluster_labels)
        n_clusters = len(unique_clusters[unique_clusters >= 0])  # Exclude noise (-1)
        n_noise = np.sum(cluster_labels == -1)
        n_clustered = len(cluster_labels) - n_noise
        
        metrics['n_clusters'] = int(n_clusters)
        metrics['n_noise_points'] = int(n_noise)
        metrics['n_clustered'] = int(n_clustered)
        metrics['noise_ratio'] = float(n_noise / len(cluster_labels))
        metrics['clustered_ratio'] = float(n_clustered / len(cluster_labels))
        
        # Cluster size statistics
        cluster_sizes = Counter(cluster_labels[cluster_labels >= 0])
        if cluster_sizes:
            sizes = list(cluster_sizes.values())
            metrics['min_cluster_size_actual'] = int(min(sizes))
            metrics['max_cluster_size'] = int(max(sizes))
            metrics['avg_cluster_size'] = float(np.mean(sizes))
            metrics['median_cluster_size'] = float(np.median(sizes))
            metrics['std_cluster_size'] = float(np.std(sizes))
        
        # Only calculate quality metrics if we have valid clusters
        if n_clustered > 0 and n_clusters > 1:
            try:
                # Silhouette Score (-1 to 1, higher is better)
                # Measures how similar objects are to their own cluster vs other clusters
                silhouette = silhouette_score(
                    embeddings[cluster_labels >= 0],
                    cluster_labels[cluster_labels >= 0]
                )
                metrics['silhouette_score'] = float(silhouette)
                logger.info(f"Silhouette Score: {silhouette:.4f}")
            except Exception as e:
                logger.warning(f"Could not calculate silhouette score: {e}")
                metrics['silhouette_score'] = None
            
            try:
                # Davies-Bouldin Index (0 to inf, lower is better)
                # Ratio of within-cluster to between-cluster distances
                davies_bouldin = davies_bouldin_score(
                    embeddings[cluster_labels >= 0],
                    cluster_labels[cluster_labels >= 0]
                )
                metrics['davies_bouldin_index'] = float(davies_bouldin)
                logger.info(f"Davies-Bouldin Index: {davies_bouldin:.4f}")
            except Exception as e:
                logger.warning(f"Could not calculate Davies-Bouldin index: {e}")
                metrics['davies_bouldin_index'] = None
            
            try:
                # Calinski-Harabasz Score (0 to inf, higher is better)
                # Ratio of between-cluster to within-cluster dispersion
                calinski = calinski_harabasz_score(
                    embeddings[cluster_labels >= 0],
                    cluster_labels[cluster_labels >= 0]
                )
                metrics['calinski_harabasz_score'] = float(calinski)
                logger.info(f"Calinski-Harabasz Score: {calinski:.4f}")
            except Exception as e:
                logger.warning(f"Could not calculate Calinski-Harabasz score: {e}")
                metrics['calinski_harabasz_score'] = None
        
        # Cluster distribution (top 10 largest clusters)
        if cluster_sizes:
            top_clusters = sorted(
                cluster_sizes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            metrics['top_clusters'] = [
                {"cluster_id": int(cid), "size": int(size)}
                for cid, size in top_clusters
            ]
        
        return metrics
    
    @staticmethod
    def evaluate_classification(
        cluster_labels: np.ndarray,
        true_labels: Optional[np.ndarray] = None,
        sequence_ids: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Evaluate classification quality if ground truth is available.
        
        Args:
            cluster_labels: Predicted cluster labels
            true_labels: True class labels (optional)
            sequence_ids: Sequence IDs for taxonomy extraction (optional)
            
        Returns:
            Dictionary of classification metrics
        """
        metrics = {}
        
        if true_labels is None:
            logger.info("No ground truth labels provided, skipping classification metrics")
            return metrics
        
        # Filter out noise points (-1) for classification metrics
        valid_mask = (cluster_labels >= 0) & (true_labels >= 0)
        
        if valid_mask.sum() == 0:
            logger.warning("No valid samples for classification evaluation")
            return metrics
        
        pred_filtered = cluster_labels[valid_mask]
        true_filtered = true_labels[valid_mask]
        
        try:
            # Adjusted Rand Index (-1 to 1, higher is better)
            # Measures similarity between clusterings, adjusted for chance
            ari = adjusted_rand_score(true_filtered, pred_filtered)
            metrics['adjusted_rand_index'] = float(ari)
            logger.info(f"Adjusted Rand Index: {ari:.4f}")
        except Exception as e:
            logger.warning(f"Could not calculate ARI: {e}")
        
        try:
            # Normalized Mutual Information (0 to 1, higher is better)
            # Measures mutual dependence between clusterings
            nmi = normalized_mutual_info_score(true_filtered, pred_filtered)
            metrics['normalized_mutual_info'] = float(nmi)
            logger.info(f"Normalized Mutual Info: {nmi:.4f}")
        except Exception as e:
            logger.warning(f"Could not calculate NMI: {e}")
        
        try:
            # Homogeneity (0 to 1, higher is better)
            # Each cluster contains only members of a single class
            homogeneity = homogeneity_score(true_filtered, pred_filtered)
            metrics['homogeneity'] = float(homogeneity)
            logger.info(f"Homogeneity: {homogeneity:.4f}")
        except Exception as e:
            logger.warning(f"Could not calculate homogeneity: {e}")
        
        try:
            # Completeness (0 to 1, higher is better)
            # All members of a class are in the same cluster
            completeness = completeness_score(true_filtered, pred_filtered)
            metrics['completeness'] = float(completeness)
            logger.info(f"Completeness: {completeness:.4f}")
        except Exception as e:
            logger.warning(f"Could not calculate completeness: {e}")
        
        try:
            # V-Measure (0 to 1, higher is better)
            # Harmonic mean of homogeneity and completeness
            v_measure = v_measure_score(true_filtered, pred_filtered)
            metrics['v_measure'] = float(v_measure)
            logger.info(f"V-Measure: {v_measure:.4f}")
        except Exception as e:
            logger.warning(f"Could not calculate V-measure: {e}")
        
        return metrics
    
    @staticmethod
    def calculate_diversity_metrics(
        cluster_labels: np.ndarray,
        sequence_lengths: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Calculate diversity and distributional metrics.
        
        Args:
            cluster_labels: Cluster assignments
            sequence_lengths: Length of each sequence (optional)
            
        Returns:
            Dictionary of diversity metrics
        """
        metrics = {}
        
        # Shannon diversity index
        cluster_counts = Counter(cluster_labels[cluster_labels >= 0])
        if cluster_counts:
            total = sum(cluster_counts.values())
            proportions = np.array([count / total for count in cluster_counts.values()])
            shannon = -np.sum(proportions * np.log(proportions))
            metrics['shannon_diversity'] = float(shannon)
            
            # Simpson diversity index
            simpson = 1 - np.sum(proportions ** 2)
            metrics['simpson_diversity'] = float(simpson)
            
            # Effective number of clusters (exp(Shannon))
            metrics['effective_n_clusters'] = float(np.exp(shannon))
        
        # Sequence length statistics (if available)
        if sequence_lengths is not None:
            metrics['avg_sequence_length'] = float(np.mean(sequence_lengths))
            metrics['min_sequence_length'] = int(np.min(sequence_lengths))
            metrics['max_sequence_length'] = int(np.max(sequence_lengths))
            metrics['std_sequence_length'] = float(np.std(sequence_lengths))
        
        return metrics
    
    @staticmethod
    def evaluate_model(
        embeddings: np.ndarray,
        cluster_labels: np.ndarray,
        sequence_lengths: Optional[np.ndarray] = None,
        true_labels: Optional[np.ndarray] = None,
        min_cluster_size: int = 5
    ) -> Dict[str, Any]:
        """
        Comprehensive model evaluation combining all metrics.
        
        Args:
            embeddings: Sequence embeddings
            cluster_labels: Cluster assignments
            sequence_lengths: Sequence lengths (optional)
            true_labels: Ground truth labels for supervised evaluation (optional)
            min_cluster_size: Minimum cluster size parameter
            
        Returns:
            Complete evaluation metrics dictionary
        """
        logger.info("=" * 80)
        logger.info("Starting comprehensive model evaluation")
        logger.info("=" * 80)
        
        evaluation = {
            'evaluation_timestamp': pd.Timestamp.now().isoformat(),
            'n_samples': int(len(embeddings)),
            'embedding_dim': int(embeddings.shape[1])
        }
        
        # Clustering metrics
        logger.info("\n1. Evaluating clustering quality...")
        clustering_metrics = ModelEvaluator.evaluate_clustering(
            embeddings,
            cluster_labels,
            min_cluster_size
        )
        evaluation['clustering'] = clustering_metrics
        
        # Diversity metrics
        logger.info("\n2. Calculating diversity metrics...")
        diversity_metrics = ModelEvaluator.calculate_diversity_metrics(
            cluster_labels,
            sequence_lengths
        )
        evaluation['diversity'] = diversity_metrics
        
        # Classification metrics (if ground truth available)
        if true_labels is not None:
            logger.info("\n3. Evaluating classification performance...")
            classification_metrics = ModelEvaluator.evaluate_classification(
                cluster_labels,
                true_labels
            )
            evaluation['classification'] = classification_metrics
        else:
            logger.info("\n3. Skipping classification evaluation (no ground truth)")
        
        # Overall quality score (simple heuristic)
        quality_score = ModelEvaluator._calculate_quality_score(evaluation)
        evaluation['overall_quality_score'] = quality_score
        
        logger.info("=" * 80)
        logger.info(f"Evaluation complete! Overall quality score: {quality_score:.3f}/10")
        logger.info("=" * 80)
        
        return evaluation
    
    @staticmethod
    def _calculate_quality_score(evaluation: Dict[str, Any]) -> float:
        """
        Calculate overall quality score (0-10 scale).
        
        Combines multiple metrics into a single score for quick assessment.
        """
        score = 0.0
        max_score = 10.0
        
        clustering = evaluation.get('clustering', {})
        
        # Penalize high noise ratio
        noise_ratio = clustering.get('noise_ratio', 1.0)
        score += (1 - noise_ratio) * 3.0  # Max 3 points
        
        # Reward good silhouette score (if available)
        silhouette = clustering.get('silhouette_score')
        if silhouette is not None:
            # Silhouette ranges from -1 to 1, normalize to 0-3
            score += (silhouette + 1) / 2 * 3.0  # Max 3 points
        
        # Reward low Davies-Bouldin index (if available)
        davies_bouldin = clustering.get('davies_bouldin_index')
        if davies_bouldin is not None:
            # Lower is better, typical range 0-3, cap at 2
            db_score = max(0, 1 - davies_bouldin / 2)
            score += db_score * 2.0  # Max 2 points
        
        # Reward diversity
        diversity = evaluation.get('diversity', {})
        shannon = diversity.get('shannon_diversity', 0)
        # Normalize Shannon (typical range 0-5)
        score += min(shannon / 5, 1.0) * 2.0  # Max 2 points
        
        return min(score, max_score)


# Convenience function
def evaluate_model(
    embeddings: np.ndarray,
    cluster_labels: np.ndarray,
    sequence_lengths: Optional[np.ndarray] = None,
    true_labels: Optional[np.ndarray] = None,
    min_cluster_size: int = 5
) -> Dict[str, Any]:
    """Convenience function for model evaluation."""
    return ModelEvaluator.evaluate_model(
        embeddings,
        cluster_labels,
        sequence_lengths,
        true_labels,
        min_cluster_size
    )
