import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Copy, Download, Eye, GitBranch, MapPin } from 'lucide-react';
import Layout from '../components/Layout';
import Card from '../components/Card';
import Table from '../components/Table';
import Badge, { QualityBadge, NoveltyBadge } from '../components/Badge';
import { LoadingOverlay } from '../components/Loading';
import { useCluster, useSequences } from '../hooks/useData';

const ClusterDetail = () => {
  const { id } = useParams();
  const { cluster, loading, error } = useCluster(id);
  const { sequences: allSequences } = useSequences();
  
  // Get member sequences for this cluster
  const memberSequences = allSequences.filter(seq => seq.cluster === id);

  const copyConsensus = () => {
    navigator.clipboard.writeText(cluster.consensus_sequence);
  };

  const downloadClusterData = () => {
    const data = {
      cluster_id: cluster.id,
      consensus_sequence: cluster.consensus_sequence,
      sequence_count: cluster.sequence_count,
      novelty_score: cluster.novelty_score,
      dominant_taxa: cluster.dominant_taxa,
      avg_quality: cluster.avg_quality,
      member_sequences: memberSequences.map(seq => ({
        id: seq.id,
        length: seq.length,
        quality: seq.quality,
        taxa: seq.taxa,
        novelty_score: seq.novelty_score
      }))
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${cluster.id}_cluster_data.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const columns = [
    {
      key: 'id',
      label: 'Sequence ID',
      render: (value) => (
        <Link 
          to={`/sequence/${value}`}
          className="font-mono text-primary-600 hover:text-primary-700 hover:underline"
        >
          {value}
        </Link>
      )
    },
    {
      key: 'length',
      label: 'Length (bp)',
      render: (value) => value.toLocaleString()
    },
    {
      key: 'quality',
      label: 'Quality',
      render: (value) => <QualityBadge score={value} />
    },
    {
      key: 'taxa',
      label: 'Taxa',
      render: (value) => (
        <Badge variant={value === 'Novel' ? 'novel' : 'known'}>
          {value}
        </Badge>
      )
    },
    {
      key: 'novelty_score',
      label: 'Novelty',
      render: (value) => <NoveltyBadge score={value} />
    },
    {
      key: 'sample_date',
      label: 'Date',
      render: (value) => new Date(value).toLocaleDateString()
    }
  ];

  const actions = (row) => (
    <div className="flex space-x-2">
      <Link
        to={`/sequence/${row.id}`}
        className="text-primary-600 hover:text-primary-700 p-1 rounded"
        title="View details"
      >
        <Eye className="h-4 w-4" />
      </Link>
      <button
        onClick={() => navigator.clipboard.writeText(row.sequence)}
        className="text-gray-500 hover:text-gray-700 p-1 rounded"
        title="Copy sequence"
      >
        <Copy className="h-4 w-4" />
      </button>
      <button
        className="text-green-600 hover:text-green-700 p-1 rounded"
        title="Download FASTA"
      >
        <Download className="h-4 w-4" />
      </button>
    </div>
  );

  if (loading) {
    return (
      <Layout title="Cluster Details">
        <LoadingOverlay message="Loading cluster details..." />
      </Layout>
    );
  }

  if (error || !cluster) {
    return (
      <Layout title="Cluster Details">
        <div className="text-center py-12">
          <p className="text-red-600">Error loading cluster: {error || 'Cluster not found'}</p>
          <Link 
            to="/clusters" 
            className="mt-4 inline-flex items-center text-primary-600 hover:text-primary-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Clusters
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Cluster ${cluster.id}`}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link 
              to="/clusters"
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div className="flex items-center space-x-3">
              <div className="h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center">
                <GitBranch className="h-6 w-6 text-primary-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{cluster.id}</h1>
                <p className="text-sm text-gray-600">
                  {cluster.sequence_count} sequences • {cluster.dominant_taxa}
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={copyConsensus}
              className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <Copy className="h-4 w-4 mr-2" />
              Copy Consensus
            </button>
            <button
              onClick={downloadClusterData}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
            >
              <Download className="h-4 w-4 mr-2" />
              Download Data
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Cluster Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <div className="text-center">
                  <p className="text-2xl font-bold text-primary-600">{cluster.sequence_count}</p>
                  <p className="text-sm text-gray-600">Total Sequences</p>
                </div>
              </Card>
              <Card>
                <div className="text-center">
                  <div className="flex justify-center mb-2">
                    <QualityBadge score={cluster.avg_quality} />
                  </div>
                  <p className="text-sm text-gray-600">Average Quality</p>
                </div>
              </Card>
              <Card>
                <div className="text-center">
                  <div className="flex justify-center mb-2">
                    <NoveltyBadge score={cluster.novelty_score} />
                  </div>
                  <p className="text-sm text-gray-600">Novelty Score</p>
                </div>
              </Card>
            </div>

            {/* Consensus Sequence */}
            <Card 
              title="Consensus Sequence"
              subtitle="Representative sequence for this cluster"
              action={
                <button
                  onClick={copyConsensus}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  Copy Sequence
                </button>
              }
            >
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <pre className="text-green-400 font-mono text-sm leading-relaxed whitespace-pre-wrap break-all">
                  {cluster.consensus_sequence}
                </pre>
              </div>
              <div className="mt-3 text-xs text-gray-500">
                Consensus sequence length: {cluster.consensus_sequence.length} base pairs
              </div>
            </Card>

            {/* Member Sequences Table */}
            <Card title={`Member Sequences (${memberSequences.length})`}>
              <Table
                columns={columns}
                data={memberSequences}
                actions={actions}
                pagination={true}
                pageSize={10}
              />
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Cluster Statistics */}
            <Card title="Cluster Statistics">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Cluster ID</span>
                  <span className="font-mono text-sm font-medium">{cluster.id}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Sequence Count</span>
                  <span className="text-sm font-medium">{cluster.sequence_count}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Dominant Taxa</span>
                  <Badge variant={cluster.dominant_taxa === 'Novel' ? 'novel' : 'known'}>
                    {cluster.dominant_taxa}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Novelty Score</span>
                  <span className="text-sm font-medium">{cluster.novelty_score.toFixed(3)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Average Quality</span>
                  <span className="text-sm font-medium">{cluster.avg_quality}%</span>
                </div>
              </div>
            </Card>

            {/* Locations */}
            <Card title="Sample Locations">
              <div className="space-y-3">
                {cluster.locations.map((location, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <MapPin className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-700">{location}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Quality Distribution */}
            <Card title="Quality Distribution">
              <div className="space-y-3">
                {(() => {
                  const qualityRanges = [
                    { range: '95-100%', count: memberSequences.filter(s => s.quality >= 95).length, color: 'bg-green-500' },
                    { range: '90-94%', count: memberSequences.filter(s => s.quality >= 90 && s.quality < 95).length, color: 'bg-blue-500' },
                    { range: '85-89%', count: memberSequences.filter(s => s.quality >= 85 && s.quality < 90).length, color: 'bg-yellow-500' },
                    { range: '80-84%', count: memberSequences.filter(s => s.quality >= 80 && s.quality < 85).length, color: 'bg-orange-500' },
                    { range: '<80%', count: memberSequences.filter(s => s.quality < 80).length, color: 'bg-red-500' }
                  ];
                  
                  return qualityRanges.map((range, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className={`h-3 w-3 rounded ${range.color}`}></div>
                        <span className="text-sm text-gray-600">{range.range}</span>
                      </div>
                      <span className="text-sm font-medium">{range.count}</span>
                    </div>
                  ));
                })()}
              </div>
            </Card>

            {/* Taxa Distribution */}
            <Card title="Taxa Distribution">
              <div className="space-y-3">
                {(() => {
                  const taxaCounts = memberSequences.reduce((acc, seq) => {
                    acc[seq.taxa] = (acc[seq.taxa] || 0) + 1;
                    return acc;
                  }, {});
                  
                  return Object.entries(taxaCounts).map(([taxa, count]) => (
                    <div key={taxa} className="flex items-center justify-between">
                      <Badge variant={taxa === 'Novel' ? 'novel' : 'known'} size="sm">
                        {taxa}
                      </Badge>
                      <span className="text-sm font-medium">{count}</span>
                    </div>
                  ));
                })()}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default ClusterDetail;