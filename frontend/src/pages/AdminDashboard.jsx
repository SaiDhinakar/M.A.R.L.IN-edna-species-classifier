import { useState, useEffect } from 'react';
import { adminAPI, datasetAPI, modelAPI } from '../services/api';
import Layout from '../components/Layout';
import Card from '../components/Card';
import Loading from '../components/Loading';
import Badge from '../components/Badge';
import Modal from '../components/Modal';
import ModelInferenceModal from '../components/ModelInferenceModal';
import ModelMetricsModal from '../components/ModelMetricsModal';
import SystemMonitoringCard from '../components/SystemMonitoringCard';
import StorageMonitoringCard from '../components/StorageMonitoringCard';
import ExternalServicesCard from '../components/ExternalServicesCard';
import { ToastContainer } from '../components/Toast';
import { formatDistanceToNow } from 'date-fns';

// Helper function to safely format dates
const safeFormatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    return formatDistanceToNow(date, { addSuffix: true });
  } catch (error) {
    return 'N/A';
  }
};

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('approvals');
  const [pendingDatasets, setPendingDatasets] = useState([]);
  const [approvedDatasets, setApprovedDatasets] = useState([]);
  const [selectedDatasets, setSelectedDatasets] = useState([]);
  const [trainingRuns, setTrainingRuns] = useState([]);
  const [modelVersions, setModelVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [loadingTrainingRuns, setLoadingTrainingRuns] = useState(false);
  const [showTrainModal, setShowTrainModal] = useState(false);
  const [showInferenceModal, setShowInferenceModal] = useState(false);
  const [showMetricsModal, setShowMetricsModal] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [trainingParams, setTrainingParams] = useState({
    model_name: 'edna_classifier',
    epochs: 100,
    batch_size: 32,
    learning_rate: 0.001,
  });

  // Toast helper functions
  const addToast = (message, type = 'info', duration = 4000) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type, duration }]);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  useEffect(() => {
    if (activeTab === 'approvals') {
      fetchPendingDatasets();
    } else if (activeTab === 'training') {
      fetchApprovedDatasets();
      fetchTrainingRuns();
    } else if (activeTab === 'models') {
      fetchModelVersions();
    }
  }, [activeTab]);

  const fetchPendingDatasets = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getPendingDatasets();
      setPendingDatasets(Array.isArray(data) ? data : data.datasets || []);
    } catch (error) {
      console.error('Error fetching pending datasets:', error);
      setPendingDatasets([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchApprovedDatasets = async () => {
    try {
      setLoadingDatasets(true);
      const data = await datasetAPI.getDatasets();
      const approved = (data.datasets || []).filter(ds => ds.status === 'approved' || ds.status === 'completed');
      setApprovedDatasets(approved);
    } catch (error) {
      console.error('Error fetching approved datasets:', error);
      setApprovedDatasets([]);
    } finally {
      setLoadingDatasets(false);
    }
  };

  const fetchTrainingRuns = async () => {
    try {
      setLoadingTrainingRuns(true);
      const data = await adminAPI.getTrainingRuns();
      setTrainingRuns(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching training runs:', error);
      setTrainingRuns([]);
    } finally {
      setLoadingTrainingRuns(false);
    }
  };

  const fetchModelVersions = async () => {
    try {
      setLoading(true);
      const [modelsData, infoData] = await Promise.all([
        adminAPI.getModels(),
        modelAPI.getInfo().catch(() => null),
      ]);
      setModelVersions(Array.isArray(modelsData) ? modelsData : modelsData.models || []);
      setModelInfo(infoData);
    } catch (error) {
      console.error('Error fetching model versions:', error);
      setModelVersions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (datasetId) => {
    try {
      await adminAPI.approveDataset(datasetId);
      alert('Dataset approved successfully!');
      fetchPendingDatasets();
    } catch (error) {
      console.error('Error approving dataset:', error);
      alert('Failed to approve dataset. Please try again.');
    }
  };

  const handleReject = async (datasetId) => {
    if (!confirm('Are you sure you want to reject this dataset?')) return;
    try {
      await datasetAPI.deleteDataset(datasetId);
      alert('Dataset rejected and deleted.');
      fetchPendingDatasets();
    } catch (error) {
      console.error('Error rejecting dataset:', error);
      alert('Failed to reject dataset. Please try again.');
    }
  };

  const handleStartTraining = async () => {
    try {
      // Check if any datasets are selected
      if (selectedDatasets.length === 0) {
        addToast('Please select at least one dataset for training', 'warning');
        return;
      }
      
      // Call training endpoint with selected datasets
      const trainingPayload = {
        dataset_ids: selectedDatasets,
        model_name: trainingParams.model_name,
        hyperparameters: {
          batch_size: trainingParams.batch_size,
          learning_rate: trainingParams.learning_rate,
          epochs: trainingParams.epochs,
        }
      };
      console.log('Training payload:', JSON.stringify(trainingPayload, null, 2));
      
      await adminAPI.startTraining(selectedDatasets, {
        model_name: trainingParams.model_name,
        hyperparameters: {
          batch_size: trainingParams.batch_size,
          learning_rate: trainingParams.learning_rate,
          epochs: trainingParams.epochs,
        }
      });
      
      setShowTrainModal(false);
      setSelectedDatasets([]); // Clear selection
      addToast(
        `Training started successfully with ${selectedDatasets.length} dataset(s)! Check the Training History section for progress.`,
        'success',
        5000
      );
      fetchTrainingRuns(); // Refresh training runs
    } catch (error) {
      console.error('Error starting training:', error);
      addToast(
        `Failed to start training: ${error.response?.data?.detail || error.message}`,
        'error',
        6000
      );
    }
  };

  const handleDatasetSelection = (datasetId) => {
    setSelectedDatasets(prev => {
      if (prev.includes(datasetId)) {
        return prev.filter(id => id !== datasetId);
      } else {
        return [...prev, datasetId];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedDatasets.length === approvedDatasets.length) {
      setSelectedDatasets([]);
    } else {
      setSelectedDatasets(approvedDatasets.map(ds => ds.id));
    }
  };

  const handleLoadModel = async (modelId) => {
    if (!confirm('Load this model version into memory for inference?')) return;
    try {
      const result = await modelAPI.loadModel(modelId);
      addToast(result.message || 'Model loaded successfully!', 'success');
      fetchModelVersions();
    } catch (error) {
      console.error('Error loading model:', error);
      addToast(error.response?.data?.detail || 'Failed to load model', 'error');
    }
  };

  const handleActivateModel = async (modelId) => {
    if (!confirm('Mark this model as the active model?')) return;
    try {
      const result = await modelAPI.activateModel(modelId);
      addToast(result.message || 'Model activated successfully!', 'success');
      fetchModelVersions();
    } catch (error) {
      console.error('Error activating model:', error);
      addToast(error.response?.data?.detail || 'Failed to activate model', 'error');
    }
  };

  const handleOpenInference = () => {
    setShowInferenceModal(true);
  };

  const handleOpenMetrics = (model) => {
    setSelectedModel(model);
    setShowMetricsModal(true);
  };

  const handleCloseMetrics = () => {
    setSelectedModel(null);
    setShowMetricsModal(false);
  };

  const handleDownload = async (datasetId, filename) => {
    try {
      const blob = await datasetAPI.downloadDataset(datasetId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading dataset:', error);
      alert('Failed to download dataset.');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      pending: { color: 'yellow', label: 'Pending' },
      running: { color: 'blue', label: 'Running' },
      completed: { color: 'green', label: 'Completed' },
      failed: { color: 'red', label: 'Failed' },
      active: { color: 'green', label: 'Active' },
      approved: { color: 'green', label: 'Approved' },
    };
    const { color, label } = statusMap[status] || { color: 'gray', label: status };
    return <Badge color={color}>{label}</Badge>;
  };

  // Component to display approved datasets
  const ApprovedDatasetsTable = () => {
    if (approvedDatasets.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <p>No approved datasets available for training yet.</p>
          <p className="text-sm mt-2">Approve datasets from the "Dataset Approvals" tab first.</p>
        </div>
      );
    }

    return (
      <div className="overflow-x-auto">
        <div className="mb-4 flex items-center justify-between">
          <button
            onClick={handleSelectAll}
            className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors"
          >
            {selectedDatasets.length === approvedDatasets.length ? '✓ Deselect All' : '☐ Select All'}
          </button>
          <div className="text-sm text-gray-600">
            <span className="font-semibold text-blue-600">{selectedDatasets.length}</span> of {approvedDatasets.length} datasets selected
          </div>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                <input
                  id="select-all-datasets"
                  name="select-all-datasets"
                  type="checkbox"
                  checked={selectedDatasets.length === approvedDatasets.length && approvedDatasets.length > 0}
                  onChange={handleSelectAll}
                  className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                  aria-label="Select all datasets"
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Dataset Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Sequences
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Uploaded By
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Approved
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {approvedDatasets.map((dataset) => (
              <tr 
                key={dataset.id} 
                className={`hover:bg-gray-50 cursor-pointer ${
                  selectedDatasets.includes(dataset.id) ? 'bg-blue-50' : ''
                }`}
                onClick={() => handleDatasetSelection(dataset.id)}
              >
                <td className="px-6 py-4">
                  <input
                    id={`dataset-checkbox-${dataset.id}`}
                    name={`dataset-checkbox-${dataset.id}`}
                    type="checkbox"
                    checked={selectedDatasets.includes(dataset.id)}
                    onChange={() => handleDatasetSelection(dataset.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                    aria-label={`Select dataset ${dataset.name}`}
                  />
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-gray-900">
                    {dataset.name}
                  </div>
                  {dataset.description && (
                    <div className="text-sm text-gray-500">
                      {dataset.description.substring(0, 80)}
                      {dataset.description.length > 80 ? '...' : ''}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4">
                  <Badge color="blue">{dataset.dataset_type}</Badge>
                </td>
                <td className="px-6 py-4">
                  {getStatusBadge(dataset.status)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  {dataset.num_sequences || dataset.sequence_count || 'N/A'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {dataset.uploaded_by?.username || 'Unknown'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {dataset.approved_at
                    ? safeFormatDate(dataset.approved_at)
                    : dataset.created_at
                    ? safeFormatDate(dataset.created_at)
                    : 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {selectedDatasets.length === 0 && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <span className="font-semibold">⚠️ No datasets selected.</span> Please select at least one dataset to start training.
            </p>
          </div>
        )}
        {selectedDatasets.length > 0 && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              <span className="font-semibold">✓ {selectedDatasets.length} dataset(s) selected</span> and ready for training.
              Click "Start Training" button to begin the training process.
            </p>
          </div>
        )}
      </div>
    );
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('approvals')}
              className={`py-4 px-1 border-b-2 font-medium text-sm relative ${
                activeTab === 'approvals'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Dataset Approvals
              {pendingDatasets.length > 0 && (
                <span className="ml-2 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 inline-flex items-center justify-center">
                  {pendingDatasets.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('training')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'training'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Training Management
            </button>
            <button
              onClick={() => setActiveTab('models')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'models'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Model Versions
            </button>
            <button
              onClick={() => setActiveTab('metrics')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'metrics'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              System Metrics
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {/* Approvals Tab */}
          {activeTab === 'approvals' && (
            <Card title="Pending Dataset Approvals">
              {loading ? (
                <Loading.LoadingSpinner />
              ) : pendingDatasets.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No pending datasets for approval.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Dataset Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Uploader
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Uploaded
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Size
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {pendingDatasets.map((dataset) => (
                        <tr key={dataset.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <div className="text-sm font-medium text-gray-900">
                              {dataset.name}
                            </div>
                            {dataset.description && (
                              <div className="text-sm text-gray-500">
                                {dataset.description.substring(0, 100)}
                                {dataset.description.length > 100 ? '...' : ''}
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {dataset.uploaded_by?.username || 'Unknown'}
                          </td>
                          <td className="px-6 py-4">
                            <Badge color="blue">{dataset.dataset_type}</Badge>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {dataset.created_at
                              ? formatDistanceToNow(new Date(dataset.created_at), {
                                  addSuffix: true,
                                })
                              : 'N/A'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {dataset.file_size
                              ? `${(dataset.file_size / 1024 / 1024).toFixed(2)} MB`
                              : 'N/A'}
                          </td>
                          <td className="px-6 py-4 text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleDownload(dataset.id, dataset.filename)}
                                className="px-3 py-1.5 text-blue-600 hover:text-blue-900 hover:bg-blue-50 rounded-lg border border-blue-200 hover:border-blue-300 transition-all"
                              >
                                Review
                              </button>
                              <button
                                onClick={() => handleApprove(dataset.id)}
                                className="px-3 py-1.5 bg-green-600 text-white hover:bg-green-700 rounded-lg shadow-sm hover:shadow-md transition-all font-medium"
                              >
                                ✓ Approve
                              </button>
                              <button
                                onClick={() => handleReject(dataset.id)}
                                className="px-3 py-1.5 bg-red-600 text-white hover:bg-red-700 rounded-lg shadow-sm hover:shadow-md transition-all font-medium"
                              >
                                ✗ Reject
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          )}

          {/* Training Tab */}
          {activeTab === 'training' && (
            <div className="space-y-6">
              {/* Approved Datasets for Training */}
              <Card title="Approved Datasets Available for Training">
                {loadingDatasets ? (
                  <Loading.LoadingSpinner />
                ) : (
                  <ApprovedDatasetsTable />
                )}
              </Card>

              <Card title="Training Controls">
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
                  <div>
                    <p className="text-gray-900 font-medium mb-1">
                      Start New Training Run
                    </p>
                    <p className="text-gray-600 text-sm">
                      {selectedDatasets.length > 0 
                        ? `Train the model with ${selectedDatasets.length} selected dataset(s)` 
                        : 'Select datasets from the table above to start training'}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      console.log('Start Training button clicked!');
                      console.log('Selected datasets:', selectedDatasets);
                      setShowTrainModal(true);
                    }}
                    disabled={selectedDatasets.length === 0}
                    className={`px-8 py-3 rounded-lg transition-all shadow-lg font-semibold flex items-center space-x-2 ${
                      selectedDatasets.length === 0
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 hover:shadow-xl'
                    }`}
                  >
                    <span>🚀</span>
                    <span>Start Training{selectedDatasets.length > 0 ? ` (${selectedDatasets.length})` : ''}</span>
                  </button>
                </div>
              </Card>

              <Card title="Training History">
                {loadingTrainingRuns ? (
                  <Loading.LoadingSpinner />
                ) : trainingRuns.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>No training runs yet.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Run ID
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Started
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Duration
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Accuracy
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {trainingRuns.map((run) => (
                          <tr key={run.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 text-sm font-mono text-gray-900">
                              #{run.id}
                            </td>
                            <td className="px-6 py-4">
                              {getStatusBadge(run.status)}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500">
                              {run.started_at
                                ? formatDistanceToNow(new Date(run.started_at), {
                                    addSuffix: true,
                                  })
                                : 'N/A'}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500">
                              {run.completed_at
                                ? `${Math.round(
                                    (new Date(run.completed_at) -
                                      new Date(run.started_at)) /
                                      60000
                                  )} min`
                                : 'In progress...'}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-900">
                              {run.metrics?.accuracy
                                ? `${(run.metrics.accuracy * 100).toFixed(2)}%`
                                : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </div>
          )}

          {/* Models Tab */}
          {activeTab === 'models' && (
            <div className="space-y-6">
              {/* Model Info Card */}
              {modelInfo && modelInfo.status !== 'no_model_loaded' && (
                <Card title="Currently Loaded Model">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-green-50 rounded-lg">
                      <p className="text-xs text-green-600 font-medium">Status</p>
                      <p className="text-lg font-bold text-green-900 mt-1 capitalize">
                        {modelInfo.status}
                      </p>
                    </div>
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <p className="text-xs text-blue-600 font-medium">Version</p>
                      <p className="text-lg font-bold text-blue-900 mt-1">
                        {modelInfo.version || 'N/A'}
                      </p>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <p className="text-xs text-purple-600 font-medium">Total Vectors</p>
                      <p className="text-lg font-bold text-purple-900 mt-1">
                        {modelInfo.index_stats?.total_vectors?.toLocaleString() || 'N/A'}
                      </p>
                    </div>
                    <div className="p-4 bg-indigo-50 rounded-lg">
                      <p className="text-xs text-indigo-600 font-medium">Species</p>
                      <p className="text-lg font-bold text-indigo-900 mt-1">
                        {modelInfo.species_mapping_count?.toLocaleString() || 'N/A'}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4">
                    <button
                      onClick={handleOpenInference}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                      Test Inference
                    </button>
                  </div>
                </Card>
              )}

              {/* Model Versions */}
              <Card title="Model Versions">
                {loading ? (
                  <Loading.LoadingSpinner />
                ) : modelVersions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>No model versions available.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Name / Version
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Quality Score
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Clusters
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Created
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {modelVersions.map((model) => {
                          const isLoaded = modelInfo?.version === model.version;
                          const qualityScore = model.metrics?.overall_quality_score;
                          
                          return (
                            <tr key={model.id} className={`hover:bg-gray-50 ${isLoaded ? 'bg-green-50' : ''}`}>
                              <td className="px-6 py-4">
                                <div className="text-sm font-medium text-gray-900">
                                  {model.name}
                                </div>
                                <div className="text-xs text-gray-500">
                                  v{model.version}
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <div className="flex flex-col gap-1">
                                  {model.is_active && (
                                    <Badge variant="success">Active</Badge>
                                  )}
                                  {isLoaded && (
                                    <Badge variant="info">Loaded</Badge>
                                  )}
                                  {!model.is_active && !isLoaded && (
                                    <Badge variant="secondary">Inactive</Badge>
                                  )}
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                {qualityScore ? (
                                  <div>
                                    <div className="text-lg font-bold text-gray-900">
                                      {qualityScore.toFixed(2)}
                                      <span className="text-xs text-gray-500">/10</span>
                                    </div>
                                    <div className="text-xs text-gray-500">
                                      {qualityScore >= 8 ? 'Excellent' :
                                       qualityScore >= 6 ? 'Good' :
                                       qualityScore >= 4 ? 'Fair' : 'Poor'}
                                    </div>
                                  </div>
                                ) : (
                                  <span className="text-sm text-gray-500">N/A</span>
                                )}
                              </td>
                              <td className="px-6 py-4 text-sm text-gray-900">
                                {model.metrics?.num_clusters || 'N/A'}
                              </td>
                              <td className="px-6 py-4 text-sm text-gray-500">
                                {model.created_at
                                  ? safeFormatDate(model.created_at)
                                  : 'N/A'}
                              </td>
                              <td className="px-6 py-4">
                                <div className="flex flex-col gap-2">
                                  {!model.is_active && (
                                    <button
                                      onClick={() => handleActivateModel(model.id)}
                                      className="text-xs text-blue-600 hover:text-blue-900 font-medium text-left"
                                    >
                                      Activate
                                    </button>
                                  )}
                                  {!isLoaded && (
                                    <button
                                      onClick={() => handleLoadModel(model.id)}
                                      className="text-xs text-green-600 hover:text-green-900 font-medium text-left"
                                    >
                                      Load
                                    </button>
                                  )}
                                  <button
                                    onClick={() => handleOpenMetrics(model)}
                                    className="text-xs text-purple-600 hover:text-purple-900 font-medium text-left"
                                  >
                                    View Metrics
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </div>
          )}
          {/* Metrics Tab */}
          {activeTab === 'metrics' && (
            <div className="space-y-6">
              {/* System Resources (CPU, RAM, GPU, Disk) */}
              <SystemMonitoringCard />

              {/* Storage Monitoring (MinIO) */}
              <StorageMonitoringCard />

              {/* External Services Health (MinIO, MLflow, PostgreSQL, Redis) */}
              <ExternalServicesCard />
            </div>
          )}
        </div>
      </div>

      {/* Training Modal */}
      {showTrainModal && (
        <Modal
          isOpen={showTrainModal}
          onClose={() => {
            console.log('Modal closing...');
            setShowTrainModal(false);
          }}
          title="Start Training Run"
          size="xl"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              console.log('Form submitted!');
              handleStartTraining();
            }}
            className="space-y-4"
          >
            {/* Selected Datasets Summary */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">
                Selected Datasets ({selectedDatasets.length})
              </h4>
              <ul className="space-y-1 text-sm text-blue-800">
                {approvedDatasets
                  .filter((dataset) => selectedDatasets.includes(dataset.id))
                  .map((dataset) => (
                    <li key={dataset.id} className="flex justify-between">
                      <span>• {dataset.name}</span>
                      <span className="text-blue-600">
                        {dataset.num_sequences || dataset.sequence_count || 0} sequences
                      </span>
                    </li>
                  ))}
              </ul>
              <div className="mt-2 pt-2 border-t border-blue-300 text-sm font-semibold text-blue-900">
                Total Sequences: {approvedDatasets
                  .filter((dataset) => selectedDatasets.includes(dataset.id))
                  .reduce((sum, dataset) => sum + (dataset.num_sequences || dataset.sequence_count || 0), 0)}
              </div>
            </div>

            <div>
              <label htmlFor="model_name" className="block text-sm font-medium text-gray-700 mb-1">
                Model Name
              </label>
              <input
                id="model_name"
                name="model_name"
                type="text"
                value={trainingParams.model_name}
                onChange={(e) =>
                  setTrainingParams({
                    ...trainingParams,
                    model_name: e.target.value,
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="edna_classifier"
                required
              />
            </div>
            <div>
              <label htmlFor="epochs" className="block text-sm font-medium text-gray-700 mb-1">
                Epochs
              </label>
              <input
                id="epochs"
                name="epochs"
                type="number"
                value={trainingParams.epochs}
                onChange={(e) =>
                  setTrainingParams({
                    ...trainingParams,
                    epochs: parseInt(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min="1"
                required
              />
            </div>
            <div>
              <label htmlFor="batch_size" className="block text-sm font-medium text-gray-700 mb-1">
                Batch Size
              </label>
              <input
                id="batch_size"
                name="batch_size"
                type="number"
                value={trainingParams.batch_size}
                onChange={(e) =>
                  setTrainingParams({
                    ...trainingParams,
                    batch_size: parseInt(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min="1"
                required
              />
            </div>
            <div>
              <label htmlFor="learning_rate" className="block text-sm font-medium text-gray-700 mb-1">
                Learning Rate
              </label>
              <input
                id="learning_rate"
                name="learning_rate"
                type="number"
                step="0.0001"
                value={trainingParams.learning_rate}
                onChange={(e) =>
                  setTrainingParams({
                    ...trainingParams,
                    learning_rate: parseFloat(e.target.value),
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                min="0.0001"
                max="1"
                required
              />
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                onClick={() => setShowTrainModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Start Training
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Model Inference Modal */}
      <ModelInferenceModal
        isOpen={showInferenceModal}
        onClose={() => setShowInferenceModal(false)}
      />

      {/* Model Metrics Modal */}
      {selectedModel && (
        <ModelMetricsModal
          isOpen={showMetricsModal}
          onClose={handleCloseMetrics}
          modelId={selectedModel.id}
          modelName={`${selectedModel.name} v${selectedModel.version}`}
        />
      )}
      
      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </Layout>
  );
};

export default AdminDashboard;
