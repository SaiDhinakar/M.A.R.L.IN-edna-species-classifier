import axios from 'axios';

// Base API URL - adjust based on your backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL + API_PREFIX,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ===== Auth APIs =====
export const authAPI = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', {
      username,
      password,
    });
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};

// ===== Dataset APIs =====
export const datasetAPI = {
  // Get all datasets with pagination (approved for users, all for admin)
  getDatasets: async (params = {}) => {
    const response = await api.get('/dataset/list', { params });
    return response.data;
  },

  // Get current user's datasets only
  getUserDatasets: async (params = {}) => {
    const response = await api.get('/dataset/list', { 
      params: { ...params, user_only: true } 
    });
    return response.data;
  },

  // Get single dataset details
  getDataset: async (datasetId) => {
    const response = await api.get(`/dataset/${datasetId}`);
    return response.data;
  },

  // Upload new dataset
  uploadDataset: async (formData, onUploadProgress) => {
    const response = await api.post('/dataset/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return response.data;
  },

  // Delete dataset
  deleteDataset: async (datasetId) => {
    const response = await api.delete(`/dataset/${datasetId}`);
    return response.data;
  },

  // Download dataset
  downloadDataset: async (datasetId) => {
    const response = await api.get(`/dataset/${datasetId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Approve dataset (admin only)
  approveDataset: async (datasetId) => {
    const response = await api.post(`/admin/datasets/${datasetId}/approve`);
    return response.data;
  },
};

// ===== Inference APIs =====
export const inferenceAPI = {
  // Classify a single sequence
  classifySequence: async (sequence, topK = 5) => {
    const response = await api.post('/model/infer', {
      sequence,
      top_k: topK,
    });
    return response.data;
  },

  // Batch classify sequences
  batchClassify: async (sequences, topK = 5) => {
    const response = await api.post('/model/batch-infer', {
      sequences,
      top_k: topK,
    });
    return response.data;
  },

  // Get active model info
  getActiveModel: async () => {
    const response = await api.get('/model/active');
    return response.data;
  },
};

// ===== Search APIs =====
export const searchAPI = {
  // Search sequences
  search: async (query, searchType = 'taxonomy', limit = 20, offset = 0) => {
    const response = await api.post('/search/query', {
      query,
      search_type: searchType,
      limit,
      offset,
    });
    return response.data;
  },

  // Get clusters
  getClusters: async () => {
    const response = await api.get('/search/clusters');
    return response.data;
  },

  // Get taxonomies
  getTaxonomies: async () => {
    const response = await api.get('/search/taxonomies');
    return response.data;
  },

  // Get statistics (from visualize endpoint)
  getStatistics: async () => {
    const response = await api.get('/visualize/summary');
    return response.data;
  },
};

// ===== Admin APIs =====
export const adminAPI = {
  // Get pending datasets
  getPendingDatasets: async () => {
    const response = await api.get('/admin/datasets/pending');
    return response.data;
  },

  // Approve dataset
  approveDataset: async (datasetId) => {
    const response = await api.post(`/admin/datasets/${datasetId}/approve`);
    return response.data;
  },

  // Training related
  startTraining: async (datasetIds, config = {}) => {
    const response = await api.post('/admin/train', {
      dataset_ids: Array.isArray(datasetIds) ? datasetIds : [datasetIds],
      model_name: config.model_name || 'edna_classifier',
      hyperparameters: config.hyperparameters || {},
    });
    return response.data;
  },

  getTrainingRuns: async () => {
    const response = await api.get('/admin/training-runs');
    return response.data;
  },

  getTrainingStatus: async (runId) => {
    const response = await api.get(`/admin/training-runs/${runId}`);
    return response.data;
  },

  // Models
  getModels: async () => {
    const response = await api.get('/model/versions');
    return response.data;
  },

  getModelInfo: async () => {
    const response = await api.get('/model/info');
    return response.data;
  },

  loadModel: async (modelId) => {
    const response = await api.post(`/model/load/${modelId}`);
    return response.data;
  },
};

// ===== User Profile APIs =====
export const userAPI = {
  // Get current user profile
  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Get user's datasets
  getUserDatasets: async () => {
    const response = await api.get('/dataset/list');
    return response.data;
  },

  // Update user profile
  updateProfile: async (userData) => {
    const response = await api.put('/auth/me', userData);
    return response.data;
  },
};

// ===== Visualization APIs =====
export const visualizationAPI = {
  // Get biodiversity summary
  getSummary: async (datasetId) => {
    const response = await api.get('/visualize/summary', {
      params: { dataset_id: datasetId }
    });
    return response.data;
  },

  // Get cluster details
  getClusterDetails: async (clusterId) => {
    const response = await api.get(`/visualize/cluster/${clusterId}`);
    return response.data;
  },

  // Get dataset statistics
  getDatasetStats: async (datasetId) => {
    const response = await api.get(`/visualize/dataset/${datasetId}/stats`);
    return response.data;
  },
};

export default api;
