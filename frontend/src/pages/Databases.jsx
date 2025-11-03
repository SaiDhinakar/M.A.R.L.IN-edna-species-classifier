import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { datasetAPI } from '../services/api';
import { Download, Database, User, Calendar, FileText, Trash2, CheckCircle, Clock, XCircle } from 'lucide-react';
import Loading from '../components/Loading';
import { useAuth } from '../contexts/AuthContext';

const Databases = () => {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { isAdmin } = useAuth();

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const data = await datasetAPI.getDatasets();
      // Backend now handles filtering: approved for users, all for admin
      setDatasets(data.datasets || []);
    } catch (err) {
      setError('Failed to load datasets');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (dataset) => {
    try {
      const blob = await datasetAPI.downloadDataset(dataset.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = dataset.original_filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download dataset');
      console.error(err);
    }
  };

  const handleDelete = async (datasetId) => {
    if (!window.confirm('Are you sure you want to delete this dataset?')) {
      return;
    }

    try {
      await datasetAPI.deleteDataset(datasetId);
      fetchDatasets();
    } catch (err) {
      alert('Failed to delete dataset');
      console.error(err);
    }
  };

  const handleApprove = async (datasetId) => {
    try {
      await datasetAPI.approveDataset(datasetId);
      fetchDatasets();
    } catch (err) {
      alert('Failed to approve dataset');
      console.error(err);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-blue-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <Layout>
        <Loading.LoadingOverlay message="Loading databases..." />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Databases</h1>
            <p className="text-gray-600 mt-1">
              Browse and manage uploaded datasets
            </p>
          </div>
          <div className="bg-white px-4 py-2 rounded-lg shadow-sm border border-gray-200">
            <p className="text-sm text-gray-600">Total Datasets</p>
            <p className="text-2xl font-bold text-blue-600">{datasets.length}</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {datasets.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Datasets Found</h3>
            <p className="text-gray-600">Upload a dataset to get started</p>
          </div>
        ) : (
          <div className="grid gap-6">
            {datasets.map((dataset) => (
              <div
                key={dataset.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    <div className="bg-blue-100 p-3 rounded-lg">
                      <Database className="w-6 h-6 text-blue-600" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {dataset.original_filename}
                      </h3>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                        <div className="flex items-center text-sm text-gray-600">
                          <User className="w-4 h-4 mr-2" />
                          <span className="truncate">{dataset.owner?.username || 'Unknown'}</span>
                        </div>
                        
                        <div className="flex items-center text-sm text-gray-600">
                          <FileText className="w-4 h-4 mr-2" />
                          <span>{formatFileSize(dataset.file_size)}</span>
                        </div>
                        
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar className="w-4 h-4 mr-2" />
                          <span>{formatDate(dataset.uploaded_at)}</span>
                        </div>
                        
                        <div className="flex items-center">
                          {getStatusIcon(dataset.status)}
                          <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(dataset.status)}`}>
                            {dataset.status}
                          </span>
                        </div>
                      </div>

                      {dataset.num_sequences && (
                        <div className="mt-3 text-sm text-gray-600">
                          <span className="font-medium">{dataset.num_sequences.toLocaleString()}</span> sequences
                        </div>
                      )}

                      {dataset.description && (
                        <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                          {dataset.description}
                        </p>
                      )}

                      {dataset.sample_location && (
                        <div className="mt-2 text-sm text-gray-500">
                          📍 {dataset.sample_location}
                          {dataset.sample_depth && ` • Depth: ${dataset.sample_depth}m`}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleDownload(dataset)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Download dataset"
                    >
                      <Download className="w-5 h-5" />
                    </button>
                    
                    {isAdmin && dataset.status === 'validated' && (
                      <button
                        onClick={() => handleApprove(dataset.id)}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                        title="Approve dataset"
                      >
                        <CheckCircle className="w-5 h-5" />
                      </button>
                    )}
                    
                    {isAdmin && (
                      <button
                        onClick={() => handleDelete(dataset.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete dataset"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Databases;
