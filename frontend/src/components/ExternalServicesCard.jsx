import { useState, useEffect } from 'react';
import { systemAPI } from '../services/api';
import { LoadingOverlay } from './Loading';

const ExternalServicesCard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [services, setServices] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchServices = async () => {
    try {
      setError(null);
      const data = await systemAPI.getServices();
      setServices(data);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch services status:', err);
      setError(err.response?.data?.detail || 'Failed to fetch services status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
    // Refresh every 60 seconds
    const interval = setInterval(fetchServices, 60000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status) => {
    const statusConfig = {
      healthy: {
        bg: 'bg-green-100',
        text: 'text-green-800',
        icon: '✓',
        label: 'Healthy',
      },
      unhealthy: {
        bg: 'bg-red-100',
        text: 'text-red-800',
        icon: '✗',
        label: 'Unhealthy',
      },
      not_configured: {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        icon: '○',
        label: 'Not Configured',
      },
    };

    const config = statusConfig[status] || statusConfig.unhealthy;

    return (
      <span
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}
      >
        <span className="mr-1">{config.icon}</span>
        {config.label}
      </span>
    );
  };

  const getServiceIcon = (serviceName) => {
    const icons = {
      minio: (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18L19.82 8 12 11.82 4.18 8 12 4.18zM4 9.68l7 3.5v7.64l-7-3.5V9.68zm9 11.14v-7.64l7-3.5v7.64l-7 3.5z" />
        </svg>
      ),
      postgresql: (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35-.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01M12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
        </svg>
      ),
      redis: (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10.5 2.661l1.5.667 1.5-.667L12 2l-1.5.661M12 4.661l-1.5-.667-1.5.667-1.5-.667-1.5.667-1.5-.667L3 4.661v2.678l1.5-.667 1.5.667 1.5-.667 1.5.667 1.5-.667 1.5.667 1.5-.667 1.5.667 1.5-.667 1.5.667V4.661l-1.5.667-1.5-.667-1.5.667-1.5-.667zM3 9.661v2.678l1.5-.667 1.5.667 1.5-.667 1.5.667 1.5-.667 1.5.667 1.5-.667 1.5.667 1.5-.667 1.5.667v-2.678l-1.5.667-1.5-.667-1.5.667-1.5-.667-1.5.667-1.5-.667-1.5.667-1.5-.667-1.5.667L3 9.661M3 14.661v2.678l1.5-.667 1.5.667 1.5-.667 1.5.667 1.5-.667 1.5.667 1.5-.667 1.5.667 1.5-.667 1.5.667v-2.678l-1.5.667-1.5-.667-1.5.667-1.5-.667-1.5.667-1.5-.667-1.5.667-1.5-.667-1.5.667L3 14.661z" />
        </svg>
      ),
      mlflow: (
        <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L1 12h3v9h6v-6h4v6h6v-9h3L12 2zm0 2.83L19 12h-2v7h-2v-6H9v6H7v-7H5l7-7.17z" />
        </svg>
      ),
    };

    return icons[serviceName] || icons.minio;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <LoadingOverlay message="Checking external services..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-4">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchServices}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const servicesList = services?.services || {};
  const overallStatus = services?.overall_status || 'unknown';

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-xl font-semibold">External Services</h3>
          <p className="text-sm text-gray-500 mt-1">
            Health status of external dependencies
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdate && (
            <span className="text-sm text-gray-500">
              Last checked: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchServices}
            className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded transition"
            disabled={loading}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Overall Status Banner */}
      <div
        className={`mb-6 p-4 rounded-lg ${
          overallStatus === 'healthy'
            ? 'bg-green-50 border border-green-200'
            : 'bg-red-50 border border-red-200'
        }`}
      >
        <div className="flex items-center">
          <div
            className={`w-3 h-3 rounded-full mr-3 ${
              overallStatus === 'healthy' ? 'bg-green-500' : 'bg-red-500'
            } animate-pulse`}
          />
          <p
            className={`font-semibold ${
              overallStatus === 'healthy' ? 'text-green-800' : 'text-red-800'
            }`}
          >
            {overallStatus === 'healthy'
              ? 'All critical services are operational'
              : 'Some services are experiencing issues'}
          </p>
        </div>
      </div>

      {/* Service Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* MinIO */}
        {servicesList.minio && (
          <div className="border rounded-lg p-4 hover:shadow-md transition">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    servicesList.minio.status === 'healthy'
                      ? 'bg-blue-100 text-blue-600'
                      : 'bg-red-100 text-red-600'
                  }`}
                >
                  {getServiceIcon('minio')}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800">MinIO</h4>
                  <p className="text-xs text-gray-500">Object Storage</p>
                </div>
              </div>
              {getStatusBadge(servicesList.minio.status)}
            </div>
            <div className="mt-3 pt-3 border-t text-sm">
              <div className="flex justify-between text-gray-600 mb-1">
                <span>Endpoint:</span>
                <span className="font-mono text-xs">{servicesList.minio.endpoint}</span>
              </div>
              <div className="text-gray-600">
                <span>Message: </span>
                <span
                  className={
                    servicesList.minio.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                  }
                >
                  {servicesList.minio.message}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* PostgreSQL */}
        {servicesList.postgresql && (
          <div className="border rounded-lg p-4 hover:shadow-md transition">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    servicesList.postgresql.status === 'healthy'
                      ? 'bg-blue-100 text-blue-600'
                      : 'bg-red-100 text-red-600'
                  }`}
                >
                  {getServiceIcon('postgresql')}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800">PostgreSQL</h4>
                  <p className="text-xs text-gray-500">Database</p>
                </div>
              </div>
              {getStatusBadge(servicesList.postgresql.status)}
            </div>
            <div className="mt-3 pt-3 border-t text-sm">
              <div className="flex justify-between text-gray-600 mb-1">
                <span>Database:</span>
                <span className="font-mono text-xs">{servicesList.postgresql.database}</span>
              </div>
              <div className="text-gray-600">
                <span>Message: </span>
                <span
                  className={
                    servicesList.postgresql.status === 'healthy'
                      ? 'text-green-600'
                      : 'text-red-600'
                  }
                >
                  {servicesList.postgresql.message}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Redis */}
        {servicesList.redis && (
          <div className="border rounded-lg p-4 hover:shadow-md transition">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    servicesList.redis.status === 'healthy'
                      ? 'bg-red-100 text-red-600'
                      : servicesList.redis.status === 'not_configured'
                      ? 'bg-gray-100 text-gray-600'
                      : 'bg-red-100 text-red-600'
                  }`}
                >
                  {getServiceIcon('redis')}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800">Redis</h4>
                  <p className="text-xs text-gray-500">Cache & Queue</p>
                </div>
              </div>
              {getStatusBadge(servicesList.redis.status)}
            </div>
            <div className="mt-3 pt-3 border-t text-sm">
              {servicesList.redis.host ? (
                <>
                  <div className="flex justify-between text-gray-600 mb-1">
                    <span>Host:</span>
                    <span className="font-mono text-xs">{servicesList.redis.host}</span>
                  </div>
                  <div className="text-gray-600">
                    <span>Message: </span>
                    <span
                      className={
                        servicesList.redis.status === 'healthy'
                          ? 'text-green-600'
                          : 'text-red-600'
                      }
                    >
                      {servicesList.redis.message}
                    </span>
                  </div>
                </>
              ) : (
                <div className="text-gray-500 text-center py-2">
                  {servicesList.redis.message}
                </div>
              )}
            </div>
          </div>
        )}

        {/* MLflow */}
        {servicesList.mlflow && (
          <div className="border rounded-lg p-4 hover:shadow-md transition">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    servicesList.mlflow.status === 'healthy'
                      ? 'bg-purple-100 text-purple-600'
                      : servicesList.mlflow.status === 'not_configured'
                      ? 'bg-gray-100 text-gray-600'
                      : 'bg-red-100 text-red-600'
                  }`}
                >
                  {getServiceIcon('mlflow')}
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800">MLflow</h4>
                  <p className="text-xs text-gray-500">ML Tracking</p>
                </div>
              </div>
              {getStatusBadge(servicesList.mlflow.status)}
            </div>
            <div className="mt-3 pt-3 border-t text-sm">
              {servicesList.mlflow.tracking_uri ? (
                <>
                  <div className="flex justify-between text-gray-600 mb-1">
                    <span>URI:</span>
                    <span className="font-mono text-xs truncate ml-2">
                      {servicesList.mlflow.tracking_uri}
                    </span>
                  </div>
                  <div className="text-gray-600">
                    <span>Message: </span>
                    <span
                      className={
                        servicesList.mlflow.status === 'healthy'
                          ? 'text-green-600'
                          : 'text-red-600'
                      }
                    >
                      {servicesList.mlflow.message}
                    </span>
                  </div>
                </>
              ) : (
                <div className="text-gray-500 text-center py-2">
                  {servicesList.mlflow.message}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-6 border-t">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Service Status Guide</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            <span className="text-gray-600">
              <span className="font-medium">Healthy:</span> Service is operational
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-red-500 rounded-full"></span>
            <span className="text-gray-600">
              <span className="font-medium">Unhealthy:</span> Service has issues
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-gray-400 rounded-full"></span>
            <span className="text-gray-600">
              <span className="font-medium">Not Configured:</span> Service is optional
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExternalServicesCard;
