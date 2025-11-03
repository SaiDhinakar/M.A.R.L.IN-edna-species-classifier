import React, { useState } from 'react';
import { 
  Search, 
  Dna, 
  Loader,
  AlertCircle,
  CheckCircle,
  Copy,
  ChevronRight,
  Database
} from 'lucide-react';
import Layout from '../components/Layout';
import { inferenceAPI, searchAPI } from '../services/api';

const SearchData = () => {
  const [activeTab, setActiveTab] = useState('classify'); // classify or search
  const [sequence, setSequence] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('taxonomy');
  const [loading, setLoading] = useState(false);
  const [classifyResult, setClassifyResult] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [error, setError] = useState('');

  const handleClassify = async () => {
    if (!sequence.trim()) {
      setError('Please enter a DNA sequence');
      return;
    }

    setLoading(true);
    setError('');
    setClassifyResult(null);

    try {
      const result = await inferenceAPI.classifySequence(sequence.trim(), 5);
      setClassifyResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to classify sequence');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');
    setSearchResults(null);

    try {
      const result = await searchAPI.search(searchQuery.trim(), searchType, 20, 0);
      setSearchResults(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const formatSequence = (seq, maxLength = 100) => {
    if (seq.length <= maxLength) return seq;
    return seq.substring(0, maxLength) + '...';
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Sequence Analysis</h1>
          <p className="text-gray-600 mt-1">
            Classify DNA sequences or search existing data
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('classify')}
              className={`${
                activeTab === 'classify'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm flex items-center`}
            >
              <Dna className="w-5 h-5 mr-2" />
              Classify Sequence
            </button>
            <button
              onClick={() => setActiveTab('search')}
              className={`${
                activeTab === 'search'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm flex items-center`}
            >
              <Search className="w-5 h-5 mr-2" />
              Search Database
            </button>
          </nav>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}

        {/* Classify Tab */}
        {activeTab === 'classify' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter DNA Sequence
              </label>
              <textarea
                value={sequence}
                onChange={(e) => setSequence(e.target.value)}
                className="w-full h-40 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                placeholder="ATCGATCGATCG..."
              />
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-gray-600">
                  {sequence.length} characters
                </p>
                <button
                  onClick={handleClassify}
                  disabled={loading || !sequence.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center"
                >
                  {loading ? (
                    <>
                      <Loader className="w-5 h-5 mr-2 animate-spin" />
                      Classifying...
                    </>
                  ) : (
                    <>
                      <Dna className="w-5 h-5 mr-2" />
                      Classify Sequence
                    </>
                  )}
                </button>
              </div>
            </div>

            {classifyResult && (
              <div className="space-y-4">
                {/* Main Result */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center mb-4">
                    <CheckCircle className="w-6 h-6 text-green-500 mr-2" />
                    <h3 className="text-lg font-semibold text-gray-900">Classification Result</h3>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Cluster ID</p>
                      <p className="text-xl font-bold text-blue-600">
                        {classifyResult.cluster_id !== null ? classifyResult.cluster_id : 'N/A'}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Confidence</p>
                      <p className="text-xl font-bold text-green-600">
                        {classifyResult.confidence 
                          ? `${(classifyResult.confidence * 100).toFixed(1)}%`
                          : 'N/A'
                        }
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Predicted Species</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {classifyResult.predicted_species || 'Unknown'}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Taxonomy</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {classifyResult.predicted_taxonomy || 'N/A'}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 text-sm text-gray-600">
                    Processing time: {(classifyResult.processing_time * 1000).toFixed(2)}ms
                  </div>
                </div>

                {/* Similar Sequences */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Similar Sequences ({classifyResult.similar_sequences.length})
                  </h3>
                  
                  <div className="space-y-3">
                    {classifyResult.similar_sequences.map((seq, index) => (
                      <div
                        key={index}
                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center">
                            <span className="text-sm font-mono font-semibold text-gray-900 mr-3">
                              {seq.sequence_id}
                            </span>
                            <button
                              onClick={() => copyToClipboard(seq.sequence_id)}
                              className="p-1 text-gray-400 hover:text-gray-600"
                            >
                              <Copy className="w-4 h-4" />
                            </button>
                          </div>
                          <span className="text-sm font-semibold text-blue-600">
                            Similarity: {(seq.similarity * 100).toFixed(2)}%
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">Species:</span>
                            <span className="ml-2 font-medium text-gray-900">
                              {seq.species_name || 'Unknown'}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Cluster:</span>
                            <span className="ml-2 font-medium text-gray-900">
                              {seq.cluster_id !== null ? seq.cluster_id : 'N/A'}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Taxonomy:</span>
                            <span className="ml-2 font-medium text-gray-900">
                              {seq.taxonomy || 'N/A'}
                            </span>
                          </div>
                          {seq.dataset_name && (
                            <div>
                              <span className="text-gray-600">Source:</span>
                              <span className="ml-2 font-medium text-blue-600 flex items-center">
                                <Database className="w-3 h-3 mr-1" />
                                {seq.dataset_name}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search Query
                  </label>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter taxonomy, cluster ID, or sequence ID..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search Type
                  </label>
                  <select
                    value={searchType}
                    onChange={(e) => setSearchType(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="taxonomy">Taxonomy</option>
                    <option value="cluster">Cluster ID</option>
                    <option value="sequence_id">Sequence ID</option>
                  </select>
                </div>

                <button
                  onClick={handleSearch}
                  disabled={loading || !searchQuery.trim()}
                  className="w-full px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {loading ? (
                    <>
                      <Loader className="w-5 h-5 mr-2 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5 mr-2" />
                      Search
                    </>
                  )}
                </button>
              </div>
            </div>

            {searchResults && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Search Results
                  </h3>
                  <span className="text-sm text-gray-600">
                    {searchResults.total} results found
                  </span>
                </div>

                {searchResults.results.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Database className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                    <p>No results found</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {searchResults.results.map((result) => (
                      <div
                        key={result.id}
                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-mono font-semibold text-gray-900">
                            {result.sequence_id}
                          </span>
                          <button
                            onClick={() => copyToClipboard(result.sequence_id)}
                            className="p-1 text-gray-400 hover:text-gray-600"
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-2">
                          <div>
                            <span className="text-gray-600">Length:</span>
                            <span className="ml-2 font-medium text-gray-900">
                              {result.length} bp
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Cluster:</span>
                            <span className="ml-2 font-medium text-gray-900">
                              {result.cluster_id !== null ? result.cluster_id : 'N/A'}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Taxonomy:</span>
                            <span className="ml-2 font-medium text-gray-900">
                              {result.taxonomy || 'N/A'}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600">Confidence:</span>
                            <span className="ml-2 font-medium text-gray-900">
                              {result.confidence 
                                ? `${(result.confidence * 100).toFixed(1)}%`
                                : 'N/A'
                              }
                            </span>
                          </div>
                        </div>
                        {result.dataset_name && (
                          <div className="text-sm pt-2 border-t border-gray-100 flex items-center">
                            <span className="text-gray-600">Database Source:</span>
                            <span className="ml-2 font-medium text-blue-600 flex items-center">
                              <Database className="w-3 h-3 mr-1" />
                              {result.dataset_name}
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default SearchData;
