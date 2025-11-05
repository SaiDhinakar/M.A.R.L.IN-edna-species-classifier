import { useState, useEffect } from 'react';
import Modal from './Modal';
import { modelAPI } from '../services/api';
import { LoadingOverlay } from './Loading';

const ModelMetricsModal = ({ isOpen, onClose, modelId, modelName }) => {
  const [activeTab, setActiveTab] = useState('metrics');
  const [metrics, setMetrics] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && modelId) {
      fetchData();
    }
  }, [isOpen, modelId]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [metricsData, evalData] = await Promise.all([
        modelAPI.getMetrics(modelId),
        modelAPI.getEvaluation(modelId),
      ]);
      setMetrics(metricsData);
      setEvaluation(evalData);
    } catch (err) {
      console.error('Error fetching model data:', err);
      setError(err.response?.data?.detail || 'Failed to load model data');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setMetrics(null);
    setEvaluation(null);
    setError(null);
    setActiveTab('metrics');
    onClose();
  };

  const getQualityColor = (score) => {
    if (!score) return 'gray';
    if (score >= 8) return 'green';
    if (score >= 6) return 'blue';
    if (score >= 4) return 'yellow';
    return 'red';
  };

  const getQualityLabel = (score) => {
    if (!score) return 'N/A';
    if (score >= 8) return 'Excellent';
    if (score >= 6) return 'Good';
    if (score >= 4) return 'Fair';
    return 'Poor';
  };

  const MetricCard = ({ label, value, unit = '', description = '' }) => (
    <div className="bg-gray-50 p-4 rounded-lg">
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">
        {value !== null && value !== undefined ? (
          <>
            {typeof value === 'number' ? value.toFixed(4) : value}
            {unit && <span className="text-sm text-gray-600 ml-1">{unit}</span>}
          </>
        ) : (
          'N/A'
        )}
      </p>
      {description && <p className="text-xs text-gray-500 mt-1">{description}</p>}
    </div>
  );

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="2xl">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Model Evaluation</h2>
          <p className="text-sm text-gray-600 mt-1">{modelName}</p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('metrics')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'metrics'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Key Metrics
          </button>
          <button
            onClick={() => setActiveTab('evaluation')}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'evaluation'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Detailed Evaluation
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="py-12">
            <LoadingOverlay message="Loading model data..." />
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        ) : (
          <>
            {activeTab === 'metrics' && metrics && (
              <div className="space-y-6">
                {/* Overall Quality Score */}
                {metrics.summary?.overall_quality_score !== undefined && (
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-100 p-6 rounded-lg border border-blue-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600 mb-1">Overall Quality Score</p>
                        <p className="text-4xl font-bold text-gray-900">
                          {metrics.summary.overall_quality_score.toFixed(2)}
                          <span className="text-lg text-gray-600">/10</span>
                        </p>
                        <p className="text-sm text-gray-700 mt-2">
                          {getQualityLabel(metrics.summary.overall_quality_score)} clustering quality
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Basic Stats */}
                {metrics.summary && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Basic Statistics</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <MetricCard
                        label="Total Sequences"
                        value={metrics.summary.num_sequences}
                      />
                      <MetricCard
                        label="Embedding Dim"
                        value={metrics.sequence_stats?.embedding_dim}
                      />
                      <MetricCard
                        label="Clusters"
                        value={metrics.summary.num_clusters}
                      />
                      <MetricCard
                        label="Noise Points"
                        value={metrics.summary.num_noise_points}
                      />
                    </div>
                  </div>
                )}

                {/* Clustering Quality */}
                {metrics.clustering_quality && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Clustering Quality</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <MetricCard
                        label="Silhouette Score"
                        value={metrics.clustering_quality.silhouette_score}
                        description="Higher is better (cohesion)"
                      />
                      <MetricCard
                        label="Davies-Bouldin Index"
                        value={metrics.clustering_quality.davies_bouldin_index}
                        description="Lower is better (separation)"
                      />
                      <MetricCard
                        label="Calinski-Harabasz"
                        value={metrics.clustering_quality.calinski_harabasz_score}
                        description="Higher is better (density)"
                      />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                      <MetricCard
                        label="Noise Ratio"
                        value={metrics.clustering_quality.noise_ratio != null ? (metrics.clustering_quality.noise_ratio * 100).toFixed(2) : null}
                        unit="%"
                        description="Percentage of noise points"
                      />
                      <MetricCard
                        label="Clustered Ratio"
                        value={metrics.clustering_quality.clustered_ratio != null ? (metrics.clustering_quality.clustered_ratio * 100).toFixed(2) : null}
                        unit="%"
                        description="Percentage clustered"
                      />
                    </div>
                  </div>
                )}

                {/* Diversity Metrics */}
                {metrics.diversity && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Diversity Metrics</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <MetricCard
                        label="Shannon Diversity"
                        value={metrics.diversity.shannon_diversity}
                        description="Species richness & evenness"
                      />
                      <MetricCard
                        label="Simpson Diversity"
                        value={metrics.diversity.simpson_diversity}
                        description="Probability of difference"
                      />
                      <MetricCard
                        label="Effective Clusters"
                        value={metrics.diversity.effective_n_clusters}
                        description="Equivalent uniform clusters"
                      />
                    </div>
                  </div>
                )}

                {/* Cluster Size Statistics */}
                {metrics.cluster_stats && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Cluster Sizes</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <MetricCard
                        label="Min Size"
                        value={metrics.cluster_stats.min_cluster_size}
                      />
                      <MetricCard label="Max Size" value={metrics.cluster_stats.max_cluster_size} />
                      <MetricCard
                        label="Average Size"
                        value={metrics.cluster_stats.avg_cluster_size}
                      />
                      <MetricCard
                        label="Median Size"
                        value={metrics.cluster_stats.median_cluster_size}
                      />
                    </div>
                  </div>
                )}

                {/* Sequence Statistics */}
                {metrics.sequence_stats && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Sequence Statistics</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <MetricCard
                        label="Avg Length"
                        value={metrics.sequence_stats.avg_length}
                        unit="bp"
                      />
                      <MetricCard
                        label="Min Length"
                        value={metrics.sequence_stats.min_length}
                        unit="bp"
                      />
                      <MetricCard
                        label="Max Length"
                        value={metrics.sequence_stats.max_length}
                        unit="bp"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'evaluation' && evaluation && (
              <div className="space-y-6">
                {/* Overall Assessment */}
                {evaluation.overall_assessment && (
                  <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-gray-900">
                          {evaluation.overall_assessment.quality_level}
                        </h3>
                        <p className="text-3xl font-bold text-blue-600 mt-1">
                          {evaluation.overall_assessment.quality_score?.toFixed(2) || 'N/A'}/10
                        </p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700">
                      {evaluation.overall_assessment.description}
                    </p>
                  </div>
                )}

                {/* Key Metrics Summary */}
                {evaluation.key_metrics && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Key Metrics Summary
                    </h3>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                      {Object.entries(evaluation.key_metrics).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">{key}</span>
                          <span className="text-sm font-medium text-gray-900">
                            {value !== null && value !== undefined ? value : 'N/A'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Interpretation */}
                {evaluation.interpretation && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Interpretation
                    </h3>
                    <div className="space-y-3">
                      {evaluation.interpretation.clustering_quality && (
                        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                          <p className="text-sm font-medium text-purple-900 mb-1">
                            Clustering Quality
                          </p>
                          <p className="text-sm text-purple-800">
                            {evaluation.interpretation.clustering_quality}
                          </p>
                        </div>
                      )}
                      {evaluation.interpretation.diversity && (
                        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                          <p className="text-sm font-medium text-green-900 mb-1">
                            Diversity
                          </p>
                          <p className="text-sm text-green-800">
                            {evaluation.interpretation.diversity}
                          </p>
                        </div>
                      )}
                      {evaluation.interpretation.noise && (
                        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                          <p className="text-sm font-medium text-yellow-900 mb-1">
                            Noise Analysis
                          </p>
                          <p className="text-sm text-yellow-800">
                            {evaluation.interpretation.noise}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {evaluation.recommendations && evaluation.recommendations.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Recommendations
                    </h3>
                    <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                      <ul className="space-y-2">
                        {evaluation.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm text-orange-800 flex gap-2">
                            <span className="text-orange-600 font-bold">{idx + 1}.</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Metrics Guide */}
                {evaluation.metrics_guide && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Metrics Guide
                    </h3>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                      {Object.entries(evaluation.metrics_guide).map(([key, value]) => (
                        <div key={key} className="border-b border-gray-200 pb-2 last:border-0">
                          <p className="text-sm font-medium text-gray-900">{key}</p>
                          <p className="text-xs text-gray-600 mt-1">{value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default ModelMetricsModal;
