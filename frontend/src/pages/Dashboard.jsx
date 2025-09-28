import React from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Dna, GitBranch, Sparkles, BarChart3, Eye, Download, Star } from 'lucide-react';
import Layout from '../components/Layout';
import { MetricCard } from '../components/Card';
import Card from '../components/Card';
import { LoadingOverlay, CardSkeleton } from '../components/Loading';
import { useMetrics, useTaxonomicDistribution, useClusters } from '../hooks/useData';

const COLORS = ['#1e40af', '#3b82f6', '#60a5fa', '#93c5fd', '#dbeafe', '#f3f4f6'];

const Dashboard = () => {
  const { metrics, loading: metricsLoading, error: metricsError } = useMetrics();
  const { distribution, loading: distributionLoading } = useTaxonomicDistribution();
  const { clusters, loading: clustersLoading } = useClusters({});

  if (metricsError) {
    return (
      <Layout title="Dashboard">
        <div className="text-center py-12">
          <p className="text-red-600">Error loading dashboard data: {metricsError}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard">
      <div className="space-y-6">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metricsLoading ? (
            <>
              {[...Array(4)].map((_, i) => <CardSkeleton key={i} />)}
            </>
          ) : (
            <>
              <MetricCard
                title="Total Sequences"
                value={metrics?.total_sequences?.toLocaleString() || '0'}
                change="+12% from last week"
                changeType="positive"
                icon={Dna}
                color="blue"
              />
              <MetricCard
                title="Total Clusters"
                value={metrics?.total_clusters?.toLocaleString() || '0'}
                change="+8% from last week"
                changeType="positive"
                icon={GitBranch}
                color="green"
              />
              <MetricCard
                title="Novel Taxa"
                value={metrics?.novel_taxa_count?.toLocaleString() || '0'}
                change="+15% from last week"
                changeType="positive"
                icon={Sparkles}
                color="amber"
              />
              <MetricCard
                title="Shannon Index"
                value={metrics?.shannon_index?.toFixed(2) || '0.00'}
                change="Stable"
                changeType="neutral"
                icon={BarChart3}
                color="blue"
              />
            </>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Taxonomic Distribution Chart */}
          <Card
            title="Taxonomic Distribution"
            subtitle="Distribution of sequences across taxonomic groups"
            action={
              <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                View Details
              </button>
            }
          >
            {distributionLoading ? (
              <LoadingOverlay message="Loading taxonomic distribution..." />
            ) : distribution && distribution.length > 0 ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={distribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value, name) => [`${value}%`, name]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-80 flex items-center justify-center text-gray-500">
                <p>No taxonomic data available</p>
              </div>
            )}
          </Card>

          {/* Top Clusters */}
          <Card
            title="Top Clusters"
            subtitle="Largest clusters by sequence count"
            action={
              <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                View All
              </button>
            }
          >
            {clustersLoading ? (
              <LoadingOverlay message="Loading clusters..." />
            ) : clusters && clusters.length > 0 ? (
              <div className="space-y-4">
                {clusters.slice(0, 5).map((cluster) => (
                  <div key={cluster.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="flex items-center space-x-3">
                      <div className="h-10 w-10 bg-primary-100 rounded-lg flex items-center justify-center">
                        <GitBranch className="h-5 w-5 text-primary-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{cluster.id}</p>
                        <p className="text-sm text-gray-600">{cluster.dominant_taxa}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">{cluster.sequence_count}</p>
                      <p className="text-sm text-gray-600">sequences</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>No clusters available</p>
              </div>
            )}
          </Card>
        </div>

        {/* Quick Actions & Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Actions */}
          <Card title="Quick Actions" className="lg:col-span-1">
            <div className="space-y-3">
              <button className="w-full flex items-center space-x-3 p-3 text-left bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors">
                <Eye className="h-5 w-5 text-primary-600" />
                <span className="font-medium text-primary-700">View All Sequences</span>
              </button>
              <button className="w-full flex items-center space-x-3 p-3 text-left bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
                <Download className="h-5 w-5 text-green-600" />
                <span className="font-medium text-green-700">Export Data</span>
              </button>
              <button className="w-full flex items-center space-x-3 p-3 text-left bg-amber-50 hover:bg-amber-100 rounded-lg transition-colors">
                <Star className="h-5 w-5 text-amber-600" />
                <span className="font-medium text-amber-700">Mark for Review</span>
              </button>
            </div>
          </Card>

          {/* Key Statistics */}
          <Card title="Key Statistics" className="lg:col-span-2">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-primary-600">
                  {metrics?.known_taxa_percent || 0}%
                </p>
                <p className="text-sm text-gray-600">Known Taxa</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-amber-600">
                  {metrics?.novel_taxa_percent || 0}%
                </p>
                <p className="text-sm text-gray-600">Novel Taxa</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {metrics?.quality_score_avg?.toFixed(1) || 0}%
                </p>
                <p className="text-sm text-gray-600">Avg Quality</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {metrics?.richness || 0}
                </p>
                <p className="text-sm text-gray-600">Species Richness</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;