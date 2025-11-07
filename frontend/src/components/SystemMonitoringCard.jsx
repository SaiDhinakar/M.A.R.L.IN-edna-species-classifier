import { useState, useEffect } from 'react';
import { systemAPI } from '../services/api';
import { LoadingOverlay } from './Loading';

const SystemMonitoringCard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchMetrics = async () => {
    try {
      setError(null);
      const data = await systemAPI.getAll();
      setMetrics(data);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch system metrics:', err);
      setError(err.response?.data?.detail || 'Failed to fetch system metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    // Refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const getUsageColor = (percent, type = 'default') => {
    const thresholds = {
      cpu: { warning: 75, critical: 90 },
      ram: { warning: 80, critical: 90 },
      disk: { warning: 85, critical: 90 },
      default: { warning: 80, critical: 90 },
    };

    const threshold = thresholds[type] || thresholds.default;

    if (percent >= threshold.critical) return 'text-red-600 bg-red-100';
    if (percent >= threshold.warning) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getProgressBarColor = (percent, type = 'default') => {
    const thresholds = {
      cpu: { warning: 75, critical: 90 },
      ram: { warning: 80, critical: 90 },
      disk: { warning: 85, critical: 90 },
      default: { warning: 80, critical: 90 },
    };

    const threshold = thresholds[type] || thresholds.default;

    if (percent >= threshold.critical) return 'bg-red-500';
    if (percent >= threshold.warning) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <LoadingOverlay message="Loading system metrics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-4">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchMetrics}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-semibold">System Resources</h3>
        <div className="flex items-center gap-4">
          {lastUpdate && (
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchMetrics}
            className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded transition"
            disabled={loading}
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* CPU Usage */}
        {metrics?.cpu && (
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-700">CPU</h4>
              <span
                className={`px-2 py-1 rounded text-sm font-medium ${getUsageColor(
                  metrics.cpu.usage_percent,
                  'cpu'
                )}`}
              >
                {metrics.cpu.usage_percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${getProgressBarColor(
                  metrics.cpu.usage_percent,
                  'cpu'
                )}`}
                style={{ width: `${Math.min(metrics.cpu.usage_percent, 100)}%` }}
              />
            </div>
            <div className="text-xs text-gray-600 space-y-1">
              <div className="flex justify-between">
                <span>Cores:</span>
                <span className="font-medium">
                  {metrics.cpu.physical_cores} physical / {metrics.cpu.logical_cores} logical
                </span>
              </div>
              {metrics.cpu.frequency && (
                <div className="flex justify-between">
                  <span>Frequency:</span>
                  <span className="font-medium">
                    {(metrics.cpu.frequency.current / 1000).toFixed(2)} GHz
                  </span>
                </div>
              )}
              {metrics.cpu.load_average && metrics.cpu.load_average.length > 0 && (
                <div className="flex justify-between">
                  <span>Load (1m):</span>
                  <span className="font-medium">{metrics.cpu.load_average[0].toFixed(2)}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* RAM Usage */}
        {metrics?.ram && (
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-700">RAM</h4>
              <span
                className={`px-2 py-1 rounded text-sm font-medium ${getUsageColor(
                  metrics.ram.usage_percent,
                  'ram'
                )}`}
              >
                {metrics.ram.usage_percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${getProgressBarColor(
                  metrics.ram.usage_percent,
                  'ram'
                )}`}
                style={{ width: `${Math.min(metrics.ram.usage_percent, 100)}%` }}
              />
            </div>
            <div className="text-xs text-gray-600 space-y-1">
              <div className="flex justify-between">
                <span>Used:</span>
                <span className="font-medium">{metrics.ram.used_gb.toFixed(2)} GB</span>
              </div>
              <div className="flex justify-between">
                <span>Total:</span>
                <span className="font-medium">{metrics.ram.total_gb.toFixed(2)} GB</span>
              </div>
              <div className="flex justify-between">
                <span>Available:</span>
                <span className="font-medium">{metrics.ram.available_gb.toFixed(2)} GB</span>
              </div>
            </div>
          </div>
        )}

        {/* GPU Usage */}
        {metrics?.gpu && !metrics.gpu.error && metrics.gpu.gpus && metrics.gpu.gpus.length > 0 ? (
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-700">GPU</h4>
              <span
                className={`px-2 py-1 rounded text-sm font-medium ${getUsageColor(
                  metrics.gpu.gpus[0].load
                )}`}
              >
                {metrics.gpu.gpus[0].load.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${getProgressBarColor(
                  metrics.gpu.gpus[0].load
                )}`}
                style={{ width: `${Math.min(metrics.gpu.gpus[0].load, 100)}%` }}
              />
            </div>
            <div className="text-xs text-gray-600 space-y-1">
              <div className="flex justify-between">
                <span>Memory:</span>
                <span className="font-medium">
                  {metrics.gpu.gpus[0].memory_used.toFixed(1)} /{' '}
                  {metrics.gpu.gpus[0].memory_total.toFixed(1)} MB
                </span>
              </div>
              <div className="flex justify-between">
                <span>Temp:</span>
                <span className="font-medium">{metrics.gpu.gpus[0].temperature}°C</span>
              </div>
              <div className="flex justify-between">
                <span>GPU ID:</span>
                <span className="font-medium">{metrics.gpu.gpus[0].id}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-700">GPU</h4>
              <span className="px-2 py-1 rounded text-sm font-medium text-gray-600 bg-gray-100">
                N/A
              </span>
            </div>
            <div className="text-xs text-gray-500 text-center py-6">
              {metrics?.gpu?.message || 'No GPU detected'}
            </div>
          </div>
        )}

        {/* Disk Usage - Show primary partition */}
        {metrics?.disk && metrics.disk.partitions && metrics.disk.partitions.length > 0 && (
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-700">Disk</h4>
              <span
                className={`px-2 py-1 rounded text-sm font-medium ${getUsageColor(
                  metrics.disk.partitions[0].usage_percent,
                  'disk'
                )}`}
              >
                {metrics.disk.partitions[0].usage_percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${getProgressBarColor(
                  metrics.disk.partitions[0].usage_percent,
                  'disk'
                )}`}
                style={{
                  width: `${Math.min(metrics.disk.partitions[0].usage_percent, 100)}%`,
                }}
              />
            </div>
            <div className="text-xs text-gray-600 space-y-1">
              <div className="flex justify-between">
                <span>Mount:</span>
                <span className="font-medium truncate ml-2">
                  {metrics.disk.partitions[0].mountpoint}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Used:</span>
                <span className="font-medium">{metrics.disk.partitions[0].used_gb.toFixed(1)} GB</span>
              </div>
              <div className="flex justify-between">
                <span>Total:</span>
                <span className="font-medium">
                  {metrics.disk.partitions[0].total_gb.toFixed(1)} GB
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Additional disk partitions */}
      {metrics?.disk && metrics.disk.partitions && metrics.disk.partitions.length > 1 && (
        <div className="mt-4 pt-4 border-t">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Additional Partitions</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {metrics.disk.partitions.slice(1).map((partition, idx) => (
              <div key={idx} className="border rounded p-3 text-sm">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-gray-700 truncate mr-2">
                    {partition.mountpoint}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${getUsageColor(
                      partition.usage_percent,
                      'disk'
                    )}`}
                  >
                    {partition.usage_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${getProgressBarColor(
                      partition.usage_percent,
                      'disk'
                    )}`}
                    style={{ width: `${Math.min(partition.usage_percent, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between mt-1 text-xs text-gray-600">
                  <span>
                    {partition.used_gb.toFixed(1)} / {partition.total_gb.toFixed(1)} GB
                  </span>
                  <span>{partition.free_gb.toFixed(1)} GB free</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemMonitoringCard;
