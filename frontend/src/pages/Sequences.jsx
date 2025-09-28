import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, Download, Star, Copy } from 'lucide-react';
import Layout from '../components/Layout';
import Table from '../components/Table';
import { FilterBar } from '../components/FormInputs';
import Badge, { QualityBadge, NoveltyBadge } from '../components/Badge';
import { LoadingOverlay } from '../components/Loading';
import { useSequences } from '../hooks/useData';

const Sequences = () => {
  const [searchValue, setSearchValue] = useState('');
  const [filters, setFilters] = useState({
    cluster: '',
    taxa: '',
    minQuality: ''
  });

  const { sequences, loading, error } = useSequences({
    search: searchValue,
    ...filters
  });

  const handleSearchChange = (e) => {
    setSearchValue(e.target.value);
  };

  const handleFilterChange = (key) => (e) => {
    setFilters(prev => ({
      ...prev,
      [key]: e.target.value
    }));
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
      key: 'cluster',
      label: 'Cluster',
      render: (value) => (
        <Link 
          to={`/cluster/${value}`}
          className="font-mono text-gray-700 hover:text-primary-600 hover:underline"
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
      label: 'Quality Score',
      render: (value) => <QualityBadge score={value} />
    },
    {
      key: 'taxa',
      label: 'Taxonomic Assignment',
      render: (value) => (
        <Badge variant={value === 'Novel' ? 'novel' : 'known'}>
          {value}
        </Badge>
      )
    },
    {
      key: 'novelty_score',
      label: 'Novelty Score',
      render: (value) => <NoveltyBadge score={value} />
    },
    {
      key: 'sample_date',
      label: 'Sample Date',
      render: (value) => new Date(value).toLocaleDateString()
    },
    {
      key: 'location',
      label: 'Location',
      render: (value) => (
        <span className="text-sm text-gray-600 truncate" title={value}>
          {value}
        </span>
      )
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
        onClick={() => {/* Handle download */}}
        className="text-green-600 hover:text-green-700 p-1 rounded"
        title="Download FASTA"
      >
        <Download className="h-4 w-4" />
      </button>
      <button
        onClick={() => {/* Handle mark for review */}}
        className="text-amber-600 hover:text-amber-700 p-1 rounded"
        title="Mark for review"
      >
        <Star className="h-4 w-4" />
      </button>
    </div>
  );

  // Get unique values for filter options
  const uniqueClusters = [...new Set(sequences.map(seq => seq.cluster))].map(cluster => ({
    value: cluster,
    label: cluster
  }));

  const uniqueTaxa = [...new Set(sequences.map(seq => seq.taxa))].map(taxa => ({
    value: taxa,
    label: taxa
  }));

  const qualityRanges = [
    { value: '', label: 'All Quality Scores' },
    { value: '95', label: '95% and above' },
    { value: '90', label: '90% and above' },
    { value: '85', label: '85% and above' },
    { value: '80', label: '80% and above' }
  ];

  const filterOptions = [
    {
      key: 'cluster',
      placeholder: 'Filter by cluster',
      options: [{ value: '', label: 'All Clusters' }, ...uniqueClusters],
      value: filters.cluster,
      onChange: handleFilterChange('cluster')
    },
    {
      key: 'taxa',
      placeholder: 'Filter by taxa',
      options: [{ value: '', label: 'All Taxa' }, ...uniqueTaxa],
      value: filters.taxa,
      onChange: handleFilterChange('taxa')
    },
    {
      key: 'minQuality',
      placeholder: 'Quality threshold',
      options: qualityRanges,
      value: filters.minQuality,
      onChange: handleFilterChange('minQuality')
    }
  ];

  if (error) {
    return (
      <Layout title="Sequences">
        <div className="text-center py-12">
          <p className="text-red-600">Error loading sequences: {error}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Sequences">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Sequence Analysis</h2>
            <p className="mt-1 text-sm text-gray-600">
              Browse and analyze eDNA sequences from your samples
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
              <Download className="h-4 w-4 mr-2" />
              Export All
            </button>
          </div>
        </div>

        {/* Filters */}
        <FilterBar
          searchValue={searchValue}
          onSearchChange={handleSearchChange}
          filters={filterOptions}
        />

        {/* Results Count */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-700">
            Showing <span className="font-medium">{sequences.length}</span> sequences
          </p>
        </div>

        {/* Table */}
        {loading ? (
          <LoadingOverlay message="Loading sequences..." />
        ) : (
          <Table
            columns={columns}
            data={sequences}
            actions={actions}
            sortable={true}
            pagination={true}
            pageSize={10}
          />
        )}
      </div>
    </Layout>
  );
};

export default Sequences;