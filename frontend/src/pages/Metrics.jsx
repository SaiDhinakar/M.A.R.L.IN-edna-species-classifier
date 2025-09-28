import React from 'react';
import {
  LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar
} from 'recharts';
import { TrendingUp, Target, BarChart3, PieChart as PieChartIcon, Download } from 'lucide-react';
import Layout from '../components/Layout';
import { MetricCard } from '../components/Card';
import Card from '../components/Card';
import { LoadingOverlay, CardSkeleton } from '../components/Loading';
import { useMetrics, useDiversityOverTime, useTaxonomicDistribution } from '../hooks/useData';

const COLORS = ['#1e40af', '#3b82f6', '#60a5fa', '#93c5fd', '#dbeafe', '#f3f4f6'];

const Metrics = () => {
  const { metrics, loading: metricsLoading, error } = useMetrics();
  const { diversityData, loading: diversityLoading } = useDiversityOverTime();
  const { distribution, loading: distributionLoading } = useTaxonomicDistribution();

  // Calculate known vs novel taxa for comparison chart
  const knownVsNovelData = metrics ? [
    { name: 'Known Taxa', value: metrics.known_taxa_percent, count: Math.round(metrics.total_sequences * metrics.known_taxa_percent / 100) },
    { name: 'Novel Taxa', value: metrics.novel_taxa_percent, count: Math.round(metrics.total_sequences * metrics.novel_taxa_percent / 100) }
  ] : [];

  if (error) {
    return (
      <Layout title="Biodiversity Metrics">
        <div className="text-center py-12">
          <p className="text-red-600">Error loading metrics: {error}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Biodiversity Metrics">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Biodiversity Metrics</h2>
            <p className="mt-1 text-sm text-gray-600">
              Comprehensive analysis of species diversity and ecological patterns
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </button>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metricsLoading ? (
            <>
              {[...Array(4)].map((_, i) => <CardSkeleton key={i} />)}
            </>
          ) : (
            <>
              <MetricCard
                title="Shannon Diversity Index"
                value={metrics?.shannon_index?.toFixed(2) || '0.00'}
                change="Higher diversity"
                changeType="positive"
                icon={BarChart3}
                color="blue"
              />
              <MetricCard
                title="Species Richness"
                value={metrics?.richness?.toLocaleString() || '0'}
                change="+5% this week"
                changeType="positive"
                icon={Target}
                color="green"
              />
              <MetricCard
                title="Evenness Index"
                value={metrics?.evenness?.toFixed(3) || '0.000'}
                change="Well distributed"
                changeType="positive"
                icon={TrendingUp}
                color="amber"
              />
              <MetricCard
                title="Average Quality"
                value={`${metrics?.quality_score_avg?.toFixed(1) || '0.0'}%`}
                change="Excellent quality"
                changeType="positive"
                icon={PieChartIcon}
                color="blue"
              />
            </>
          )}
        </div>

        {/* Main Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Diversity Over Time */}
          <Card
            title="Diversity Trends"
            subtitle="Shannon index and richness over sampling period"
            action={
              <select className="text-sm border border-gray-300 rounded-md px-2 py-1">
                <option>Last 7 days</option>
                <option>Last 30 days</option>
                <option>Last 90 days</option>
              </select>
            }
          >
            {diversityLoading ? (
              <LoadingOverlay message="Loading diversity trends..." />
            ) : (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={diversityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(date) => new Date(date).toLocaleDateString()}
                    />
                    <YAxis yAxisId="shannon" orientation="left" />
                    <YAxis yAxisId="richness" orientation="right" />
                    <Tooltip
                      labelFormatter={(date) => new Date(date).toLocaleDateString()}
                      formatter={(value, name) => [
                        name === 'shannon' ? value.toFixed(2) : value,
                        name === 'shannon' ? 'Shannon Index' : 'Species Richness'
                      ]}
                    />
                    <Line
                      yAxisId="shannon"
                      type="monotone"
                      dataKey="shannon"
                      stroke="#3b82f6"
                      strokeWidth={3}
                      dot={{ r: 4 }}
                    />
                    <Line
                      yAxisId="richness"
                      type="monotone"
                      dataKey="richness"
                      stroke="#10b981"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          {/* Known vs Novel Taxa */}
          <Card
            title="Known vs Novel Taxa"
            subtitle="Distribution of taxonomic novelty"
          >
            {metricsLoading ? (
              <LoadingOverlay message="Loading taxonomic analysis..." />
            ) : (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={knownVsNovelData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}\n${(percent * 100).toFixed(1)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      <Cell fill="#10b981" />
                      <Cell fill="#f59e0b" />
                    </Pie>
                    <Tooltip 
                      formatter={(value, name) => [`${value}%`, name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </div>

        {/* Detailed Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Taxonomic Composition */}
          <Card title="Taxonomic Composition" className="lg:col-span-2">
            {distributionLoading ? (
              <LoadingOverlay message="Loading taxonomic composition..." />
            ) : (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={distribution} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={100} />
                    <Tooltip
                      formatter={(value, name) => [`${value} sequences`, 'Count']}
                      labelFormatter={(label) => `${label}`}
                    />
                    <Bar 
                      dataKey="count" 
                      fill="#3b82f6"
                      radius={[0, 4, 4, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          {/* Diversity Indices Explanation */}
          <Card title="Diversity Indices" subtitle="Understanding the metrics">
            <div className="space-y-4 text-sm">
              <div>
                <h4 className="font-medium text-gray-900">Shannon Index</h4>
                <p className="text-gray-600 mt-1">
                  Measures both richness and evenness. Higher values indicate greater diversity.
                </p>
                <div className="mt-2 p-2 bg-blue-50 rounded">
                  <span className="font-mono text-blue-800">H' = -Σ(pi × ln(pi))</span>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900">Species Richness</h4>
                <p className="text-gray-600 mt-1">
                  Total number of different species observed in the sample.
                </p>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900">Evenness</h4>
                <p className="text-gray-600 mt-1">
                  How evenly distributed the species are. Values closer to 1 indicate more even distribution.
                </p>
                <div className="mt-2 p-2 bg-green-50 rounded">
                  <span className="font-mono text-green-800">J = H'/ln(S)</span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Sample Statistics */}
        <Card title="Sample Analysis">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center p-4 border rounded-lg">
              <p className="text-2xl font-bold text-primary-600">
                {diversityData.reduce((sum, d) => sum + d.samples, 0)}
              </p>
              <p className="text-sm text-gray-600 mt-1">Total Samples</p>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <p className="text-2xl font-bold text-green-600">
                {metrics?.total_sequences?.toLocaleString() || '0'}
              </p>
              <p className="text-sm text-gray-600 mt-1">Total Sequences</p>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <p className="text-2xl font-bold text-amber-600">
                {metrics?.novel_taxa_count || '0'}
              </p>
              <p className="text-sm text-gray-600 mt-1">Novel Taxa Discovered</p>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <p className="text-2xl font-bold text-blue-600">
                {diversityData.length}
              </p>
              <p className="text-sm text-gray-600 mt-1">Sampling Days</p>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
};

export default Metrics;