import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChevronDown, ChevronRight, GitBranch, Copy, Eye, Download } from 'lucide-react';
import Layout from '../components/Layout';
import Card from '../components/Card';
import { FilterBar } from '../components/FormInputs';
import Badge, { NoveltyBadge, QualityBadge } from '../components/Badge';
import { LoadingOverlay } from '../components/Loading';
import { useClusters, useClusterSizes } from '../hooks/useData';

const Clusters = () => {
  const [searchValue, setSearchValue] = useState('');
  const [expandedCluster, setExpandedCluster] = useState(null);
  const [filters, setFilters] = useState({
    minSize: '',
    minNovelty: ''
  });

  const { clusters, loading, error } = useClusters({
    search: searchValue,
    ...filters
  });
  const { clusterSizes, loading: sizesLoading } = useClusterSizes();

  const handleSearchChange = (e) => {
    setSearchValue(e.target.value);
  };

  const handleFilterChange = (key) => (e) => {
    setFilters(prev => ({
      ...prev,
      [key]: e.target.value
    }));
  };

  const toggleExpanded = (clusterId) => {
    setExpandedCluster(expandedCluster === clusterId ? null : clusterId);
  };

  const sizeRanges = [
    { value: '', label: 'All Sizes' },
    { value: '100', label: '100+ sequences' },
    { value: '50', label: '50+ sequences' },
    { value: '20', label: '20+ sequences' },
    { value: '10', label: '10+ sequences' }
  ];

  const noveltyRanges = [
    { value: '', label: 'All Novelty Scores' },
    { value: '0.8', label: '0.8+ (Highly Novel)' },
    { value: '0.6', label: '0.6+ (Moderately Novel)' },
    { value: '0.4', label: '0.4+ (Partially Novel)' },
    { value: '0.2', label: '0.2+ (Low Novelty)' }
  ];

  const filterOptions = [
    {
      key: 'minSize',
      placeholder: 'Filter by size',
      options: sizeRanges,
      value: filters.minSize,
      onChange: handleFilterChange('minSize')
    },
    {
      key: 'minNovelty',
      placeholder: 'Filter by novelty',
      options: noveltyRanges,
      value: filters.minNovelty,
      onChange: handleFilterChange('minNovelty')
    }
  ];

  if (error) {
    return (
      <Layout title="Clusters">
        <div className="text-center py-12">
          <p className="text-red-600">Error loading clusters: {error}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Clusters">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Sequence Clusters</h2>
            <p className="mt-1 text-sm text-gray-600">
              Explore clustered sequences and their consensus information
            </p>
          </div>
        </div>

        {/* Cluster Size Distribution Chart */}
        <Card title="Cluster Size Distribution" subtitle="Number of sequences per cluster">
          {sizesLoading ? (
            <LoadingOverlay message="Loading cluster sizes..." />
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={clusterSizes.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="cluster" />
                  <YAxis />
                  <Tooltip />
                  <Bar 
                    dataKey="size" 
                    fill="#3b82f6"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        {/* Filters */}
        <FilterBar
          searchValue={searchValue}
          onSearchChange={handleSearchChange}
          filters={filterOptions}
        />

        {/* Results Count */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-700">
            Showing <span className="font-medium">{clusters.length}</span> clusters
          </p>
        </div>

        {/* Cluster Cards */}
        {loading ? (
          <LoadingOverlay message="Loading clusters..." />
        ) : (
          <div className="space-y-4">
            {clusters.map((cluster) => (
              <Card key={cluster.id} className="overflow-hidden">
                <div className="p-6">
                  {/* Cluster Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center">
                        <GitBranch className="h-6 w-6 text-primary-600" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <Link
                            to={`/cluster/${cluster.id}`}
                            className="text-xl font-bold text-primary-600 hover:text-primary-700 hover:underline"
                          >
                            {cluster.id}
                          </Link>
                          <NoveltyBadge score={cluster.novelty_score} />
                        </div>
                        <p className="text-sm text-gray-600">
                          {cluster.sequence_count} sequences • {cluster.dominant_taxa}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Avg Quality</p>
                        <QualityBadge score={cluster.avg_quality} />
                      </div>
                      <button
                        onClick={() => toggleExpanded(cluster.id)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                      >
                        {expandedCluster === cluster.id ? 
                          <ChevronDown className="h-5 w-5" /> : 
                          <ChevronRight className="h-5 w-5" />
                        }
                      </button>
                    </div>
                  </div>

                  {/* Consensus Sequence Preview */}
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-gray-700">Consensus Sequence</p>
                      <button
                        onClick={() => navigator.clipboard.writeText(cluster.consensus_sequence)}
                        className="text-gray-500 hover:text-gray-700 p-1 rounded"
                        title="Copy sequence"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                    <p className="font-mono text-sm text-gray-800 break-all">
                      {cluster.consensus_sequence.slice(0, 60)}...
                    </p>
                  </div>

                  {/* Locations */}
                  <div className="mt-3 flex flex-wrap gap-2">
                    {cluster.locations.map((location, index) => (
                      <Badge key={index} variant="info" size="sm">
                        {location}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedCluster === cluster.id && (
                  <div className="border-t border-gray-200 bg-gray-50 p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Cluster Statistics */}
                      <div>
                        <h4 className="font-medium text-gray-900 mb-3">Cluster Statistics</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Total Sequences:</span>
                            <span className="font-medium">{cluster.sequence_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Novelty Score:</span>
                            <span className="font-medium">{cluster.novelty_score.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Average Quality:</span>
                            <span className="font-medium">{cluster.avg_quality}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Dominant Taxa:</span>
                            <span className="font-medium">{cluster.dominant_taxa}</span>
                          </div>
                        </div>
                      </div>

                      {/* Member Sequences */}
                      <div>
                        <h4 className="font-medium text-gray-900 mb-3">Member Sequences</h4>
                        <div className="space-y-2">
                          {cluster.sequences.map((seqId) => (
                            <div key={seqId} className="flex items-center justify-between">
                              <Link
                                to={`/sequence/${seqId}`}
                                className="font-mono text-sm text-primary-600 hover:text-primary-700 hover:underline"
                              >
                                {seqId}
                              </Link>
                              <div className="flex space-x-1">
                                <Link
                                  to={`/sequence/${seqId}`}
                                  className="text-gray-500 hover:text-gray-700 p-1 rounded"
                                  title="View details"
                                >
                                  <Eye className="h-3 w-3" />
                                </Link>
                                <button
                                  className="text-gray-500 hover:text-gray-700 p-1 rounded"
                                  title="Download FASTA"
                                >
                                  <Download className="h-3 w-3" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="mt-6 flex space-x-3">
                      <Link
                        to={`/cluster/${cluster.id}`}
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </Link>
                      <button className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </button>
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Clusters;