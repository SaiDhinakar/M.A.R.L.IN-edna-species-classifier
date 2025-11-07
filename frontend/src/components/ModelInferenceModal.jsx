import { useState } from 'react';
import Modal from './Modal';
import { modelAPI } from '../services/api';

const ModelInferenceModal = ({ isOpen, onClose }) => {
  const [sequence, setSequence] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleInfer = async () => {
    if (!sequence.trim()) {
      setError('Please enter a DNA sequence');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await modelAPI.inferSequence(sequence, topK);
      setResult(data);
    } catch (err) {
      console.error('Inference error:', err);
      setError(err.response?.data?.detail || 'Failed to perform inference');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSequence('');
    setTopK(5);
    setResult(null);
    setError(null);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="xl">
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Sequence Inference</h2>
        
        {/* Input Section */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              DNA Sequence
            </label>
            <textarea
              value={sequence}
              onChange={(e) => setSequence(e.target.value)}
              placeholder="Enter DNA sequence (ATGC characters)..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              rows={6}
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              Minimum 10 bases. Only A, T, G, C, N characters allowed.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Top K Results
            </label>
            <input
              type="number"
              value={topK}
              onChange={(e) => setTopK(Math.max(1, Math.min(20, parseInt(e.target.value) || 5)))}
              min="1"
              max="20"
              className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          <button
            onClick={handleInfer}
            disabled={loading || !sequence.trim()}
            className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
              loading || !sequence.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {loading ? 'Analyzing...' : 'Run Inference'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <div className="space-y-4 border-t pt-4">
            <h3 className="text-lg font-semibold text-gray-900">Results</h3>
            
            {/* Main Prediction */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-600 mb-1">Predicted Species</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {result.predicted_species || 'Unknown'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 mb-1">Taxonomy</p>
                  <p className="text-sm text-gray-700">
                    {result.predicted_taxonomy || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 mb-1">Cluster ID</p>
                  <p className="text-sm font-mono text-gray-900">
                    {result.cluster_id ?? 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 mb-1">Confidence</p>
                  <p className="text-sm font-semibold text-gray-900">
                    {result.confidence ? `${(result.confidence * 100).toFixed(2)}%` : 'N/A'}
                  </p>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-blue-200">
                <p className="text-xs text-gray-600 mb-1">Sequence Hash</p>
                <p className="text-xs font-mono text-gray-700 break-all">
                  {result.sequence_hash}
                </p>
              </div>
              {result.processing_time && (
                <div className="mt-2">
                  <p className="text-xs text-gray-500">
                    Processing time: {result.processing_time.toFixed(3)}s
                  </p>
                </div>
              )}
            </div>

            {/* Similar Sequences */}
            {result.similar_sequences && result.similar_sequences.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-3">
                  Top {result.similar_sequences.length} Similar Sequences
                </h4>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {result.similar_sequences.map((seq, idx) => (
                    <div
                      key={idx}
                      className="bg-gray-50 p-3 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-semibold text-gray-500">
                              #{idx + 1}
                            </span>
                            <span className="text-sm font-medium text-gray-900">
                              {seq.species_name || 'Unknown'}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 mb-1">
                            {seq.taxonomy || 'No taxonomy'}
                          </p>
                          <div className="flex items-center gap-3 text-xs text-gray-500">
                            <span>ID: {seq.sequence_id}</span>
                            <span>Cluster: {seq.cluster_id}</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-blue-600">
                            {(seq.similarity * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-gray-500">similarity</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer Actions */}
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

export default ModelInferenceModal;
