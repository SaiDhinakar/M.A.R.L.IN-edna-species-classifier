import { useState, useEffect } from 'react';
import { systemAPI } from '../services/api';
import { LoadingOverlay } from './Loading';

const StorageMonitoringCard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [storage, setStorage] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchStorage = async () => {
    try {
      setError(null);
      const data = await systemAPI.getStorage();
      setStorage(data);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch storage metrics:', err);
      setError(err.response?.data?.detail || 'Failed to fetch storage metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStorage();
    // Refresh every 5 minutes (storage operations are expensive)
    const interval = setInterval(fetchStorage, 300000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <LoadingOverlay message="Loading storage metrics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-4">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchStorage}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!storage || storage.status !== 'connected') {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-8">
          <svg
            className="w-16 h-16 mx-auto text-gray-400 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
          <p className="text-gray-600">MinIO storage not available</p>
          <button
            onClick={fetchStorage}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-xl font-semibold">Storage (MinIO)</h3>
          <p className="text-sm text-gray-500 mt-1">
            Object storage usage across all buckets
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdate && (
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchStorage}
            className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded transition"
            disabled={loading}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Total Storage Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="border rounded-lg p-4 bg-gradient-to-br from-blue-50 to-blue-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Storage</p>
              <p className="text-2xl font-bold text-blue-700">
                {storage.total_size_gb.toFixed(2)} GB
              </p>
            </div>
            <svg
              className="w-12 h-12 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"
              />
            </svg>
          </div>
        </div>

        <div className="border rounded-lg p-4 bg-gradient-to-br from-green-50 to-green-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Objects</p>
              <p className="text-2xl font-bold text-green-700">
                {formatNumber(storage.total_objects)}
              </p>
            </div>
            <svg
              className="w-12 h-12 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
        </div>

        <div className="border rounded-lg p-4 bg-gradient-to-br from-purple-50 to-purple-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Buckets</p>
              <p className="text-2xl font-bold text-purple-700">
                {storage.buckets.length}
              </p>
            </div>
            <svg
              className="w-12 h-12 text-purple-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Bucket Details */}
      <div>
        <h4 className="text-lg font-semibold mb-4">Bucket Details</h4>
        {storage.buckets.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No buckets found</p>
          </div>
        ) : (
          <div className="space-y-3">
            {storage.buckets.map((bucket, idx) => {
              const sizePercent = (bucket.size_gb / storage.total_size_gb) * 100;
              const objectPercent = (bucket.object_count / storage.total_objects) * 100;

              return (
                <div key={idx} className="border rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                        <svg
                          className="w-6 h-6 text-blue-600"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                          />
                        </svg>
                      </div>
                      <div>
                        <h5 className="font-semibold text-gray-800">{bucket.name}</h5>
                        <p className="text-sm text-gray-500">
                          {formatNumber(bucket.object_count)} objects
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-800">
                        {bucket.size_gb.toFixed(2)} GB
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatBytes(bucket.size_bytes)}
                      </p>
                    </div>
                  </div>

                  {/* Size visualization */}
                  <div className="mb-2">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Storage: {sizePercent.toFixed(1)}% of total</span>
                      <span>{bucket.size_mb.toFixed(2)} MB</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(sizePercent, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Object count visualization */}
                  <div>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Objects: {objectPercent.toFixed(1)}% of total</span>
                      <span>{formatNumber(bucket.object_count)} files</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(objectPercent, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default StorageMonitoringCard;
