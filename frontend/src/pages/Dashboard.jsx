import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  Upload, 
  Database, 
  Dna, 
  Users,
  BarChart3, 
  ArrowRight, 
  Activity,
  TrendingUp
} from 'lucide-react';
import Layout from '../components/Layout';
import Card from '../components/Card';
import Loading from '../components/Loading';
import { datasetAPI, visualizationAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Dashboard = () => {
  const { user, isAdmin } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentDatasets, setRecentDatasets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch recent datasets first
      const datasetsData = await datasetAPI.getDatasets({ limit: 5 });
      const datasets = datasetsData.datasets || [];
      setRecentDatasets(datasets);

      // Get the most recent processed dataset for visualization
      const processedDataset = datasets.find(ds => ds.status === 'completed' || ds.status === 'approved');
      
      if (processedDataset) {
        // Fetch statistics from visualization API with dataset_id
        const statsData = await visualizationAPI.getSummary(processedDataset.id);
        setStats(statsData);
      } else {
        // Set default stats if no processed dataset found
        setStats({
          biodiversity: {
            total_sequences: 0,
            unique_clusters: 0,
            shannon_index: 0,
            simpson_index: 0,
            taxa_richness: 0
          },
          top_clusters: [],
          dataset_id: null,
          model_version: 'N/A'
        });
      }

    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      // Set default stats on error
      setStats({
        biodiversity: {
          total_sequences: 0,
          unique_clusters: 0,
          shannon_index: 0,
          simpson_index: 0,
          taxa_richness: 0
        },
        top_clusters: [],
        dataset_id: null,
        model_version: 'N/A'
      });
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    return num.toLocaleString();
  };

  const features = [
    {
      icon: Search,
      title: "Search & Classify",
      description: "Classify DNA sequences using our trained model and search existing database with advanced filtering.",
      link: "/search",
      color: "blue",
      stats: stats ? `${formatNumber(stats.total_sequences)} sequences` : "Loading..."
    },
    {
      icon: Database,
      title: "Browse Databases",
      description: "View all uploaded datasets with metadata, user information, and download options.",
      link: "/databases",
      color: "purple",
      stats: stats ? `${formatNumber(stats.total_datasets)} datasets` : "Loading..."
    },
    {
      icon: Upload,
      title: "Submit Data",
      description: "Upload your DNA sequence datasets in FASTA, FASTQ, or BLAST format for analysis.",
      link: "/submit",
      color: "green",
      stats: "Easy submission"
    }
  ];

  if (loading) {
    return (
      <Layout>
        <Loading.LoadingOverlay message="Loading dashboard..." />
      </Layout>
    );
  }

  return (
    <Layout title="Overview">
      <div className="space-y-8">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-3xl p-8 text-white">
          <div className="max-w-4xl">
            <h1 className="text-4xl font-bold mb-4">
              Welcome back, {user?.full_name || user?.username}!
            </h1>
            <p className="text-xl text-blue-100 mb-6 leading-relaxed">
              M.A.R.L.IN eDNA Species Classifier - Advanced environmental DNA analysis pipeline 
              for marine biodiversity research using machine learning.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link 
                to="/search"
                className="bg-white text-blue-600 px-6 py-3 rounded-2xl font-semibold hover:bg-blue-50 transition-colors flex items-center space-x-2"
              >
                <Search className="h-5 w-5" />
                <span>Start Classifying</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link 
                to="/submit"
                className="bg-blue-500 text-white px-6 py-3 rounded-2xl font-semibold hover:bg-blue-400 transition-colors flex items-center space-x-2"
              >
                <Upload className="h-5 w-5" />
                <span>Submit Data</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Statistics Cards */}
        {/* {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-600 font-medium">Total Sequences</p>
                  <p className="text-3xl font-bold text-blue-900 mt-1">
                    {formatNumber(stats.total_sequences)}
                  </p>
                </div>
                <div className="bg-blue-600 p-3 rounded-full">
                  <Dna className="h-6 w-6 text-white" />
                </div>
              </div>
            </Card>

            <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-600 font-medium">Datasets</p>
                  <p className="text-3xl font-bold text-purple-900 mt-1">
                    {formatNumber(stats.total_datasets)}
                  </p>
                </div>
                <div className="bg-purple-600 p-3 rounded-full">
                  <Database className="h-6 w-6 text-white" />
                </div>
              </div>
            </Card>

            <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-600 font-medium">Clusters</p>
                  <p className="text-3xl font-bold text-green-900 mt-1">
                    {formatNumber(stats.total_clusters)}
                  </p>
                </div>
                <div className="bg-green-600 p-3 rounded-full">
                  <Activity className="h-6 w-6 text-white" />
                </div>
              </div>
            </Card>

            <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-600 font-medium">Unique Taxa</p>
                  <p className="text-3xl font-bold text-orange-900 mt-1">
                    {formatNumber(stats.unique_taxonomy_count)}
                  </p>
                </div>
                <div className="bg-orange-600 p-3 rounded-full">
                  <TrendingUp className="h-6 w-6 text-white" />
                </div>
              </div>
            </Card>
          </div>
        )} */}

        {/* Main Features */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => {
            const IconComponent = feature.icon;
            const colorClasses = {
              blue: "bg-blue-100 text-blue-600 border-blue-200",
              purple: "bg-purple-100 text-purple-600 border-purple-200",
              green: "bg-green-100 text-green-600 border-green-200"
            };
            
            return (
              <Link 
                key={index}
                to={feature.link}
              >
                <Card className="hover:shadow-lg transition-all border-2 hover:border-blue-200 h-full">
                  <div className="flex flex-col h-full">
                    <div className={`p-4 rounded-2xl ${colorClasses[feature.color]} w-fit mb-4`}>
                      <IconComponent className="h-6 w-6" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 mb-4 flex-grow">
                      {feature.description}
                    </p>
                    {/* <div className="flex items-center justify-between mt-auto">
                      <span className="text-sm font-semibold text-gray-500">
                        {feature.stats}
                      </span>
                      <ArrowRight className="h-5 w-5 text-blue-600" />
                    </div> */}
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>

        {/* Recent Datasets */}
        {recentDatasets.length > 0 && (
          <Card>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Recent Datasets</h2>
              <Link 
                to="/databases"
                className="text-blue-600 hover:text-blue-700 font-medium flex items-center"
              >
                View All
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
            
            <div className="space-y-4">
              {recentDatasets.map((dataset) => (
                <div 
                  key={dataset.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="bg-blue-100 p-2 rounded-lg">
                      <Database className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">
                        {dataset.original_filename}
                      </h4>
                      <p className="text-sm text-gray-600">
                        Uploaded by {dataset.owner?.username || 'Unknown'} • {dataset.num_sequences?.toLocaleString()} sequences
                      </p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    dataset.status === 'completed' ? 'bg-green-100 text-green-800' :
                    dataset.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                    dataset.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {dataset.status}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-gradient-to-br from-blue-50 to-indigo-50">
            <h3 className="text-xl font-bold text-gray-900 mb-2">Getting Started</h3>
            <p className="text-gray-600 mb-4">
              New to M.A.R.L.IN? Learn how to classify sequences and explore our databases.
            </p>
            <Link 
              to="/search"
              className="text-blue-600 hover:text-blue-700 font-medium flex items-center"
            >
              View Tutorial
              <ArrowRight className="h-4 w-4 ml-1" />
            </Link>
          </Card>

          {isAdmin && (
            <Card className="bg-gradient-to-br from-purple-50 to-pink-50">
              <h3 className="text-xl font-bold text-gray-900 mb-2">Admin Panel</h3>
              <p className="text-gray-600 mb-4">
                Manage datasets, users, and monitor training runs.
              </p>
              <Link 
                to="/settings"
                className="text-purple-600 hover:text-purple-700 font-medium flex items-center"
              >
                Go to Admin Panel
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </Card>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
