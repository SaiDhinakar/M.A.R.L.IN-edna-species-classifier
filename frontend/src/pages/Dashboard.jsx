import React from 'react';
import { Link } from 'react-router-dom';
import { Search, Upload, Database, Dna, GitBranch, BarChart3, ArrowRight, FileText, Globe } from 'lucide-react';
import Layout from '../components/Layout';
import Card from '../components/Card';

const Dashboard = () => {
  const features = [
    {
      icon: Search,
      title: "Search eDNA Data",
      description: "Explore comprehensive datasets from various sources with detailed cluster analysis, sequence matching, and biodiversity insights.",
      link: "/search",
      color: "blue",
      stats: "1M+ sequences analyzed"
    },
    {
      icon: Upload,
      title: "Submit Data",
      description: "Contribute your eDNA samples and sequences to our growing database with standardized metadata and quality validation.",
      link: "/submit",
      color: "green",
      stats: "Easy submission process"
    }
  ];

  const capabilities = [
    {
      icon: Database,
      title: "Reference Databases",
      description: "Access to 16S/18S/28S ribosomal RNA sequences and viral genomes from trusted sources",
      count: "4+ databases"
    },
    {
      icon: GitBranch,
      title: "Cluster Analysis",
      description: "Advanced clustering algorithms for species identification and phylogenetic analysis",
      count: "ML-powered"
    },
    {
      icon: BarChart3,
      title: "Biodiversity Metrics",
      description: "Shannon diversity index, species richness, and novel taxa discovery analytics",
      count: "Real-time stats"
    },
    {
      icon: Globe,
      title: "Global Coverage",
      description: "Marine samples from Pacific, Atlantic, Arctic, and Mediterranean regions",
      count: "Worldwide"
    }
  ];

  return (
    <Layout title="Overview">
      <div className="space-y-8">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-3xl p-8 text-white">
          <div className="max-w-4xl">
            <h1 className="text-4xl font-bold mb-4">
              M.A.R.L.IN eDNA Species Classifier
            </h1>
            <p className="text-xl text-blue-100 mb-6 leading-relaxed">
              Advanced environmental DNA analysis pipeline for marine biodiversity research. 
              Identify species, analyze clusters, and discover new taxa from environmental samples 
              using cutting-edge machine learning and comprehensive reference databases.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link 
                to="/search"
                className="bg-white text-blue-600 px-6 py-3 rounded-2xl font-semibold hover:bg-blue-50 transition-colors flex items-center space-x-2"
              >
                <Search className="h-5 w-5" />
                <span>Start Searching</span>
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

        {/* Main Features */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {features.map((feature, index) => {
            const IconComponent = feature.icon;
            const colorClasses = {
              blue: "bg-blue-100 text-blue-600 border-blue-200",
              green: "bg-green-100 text-green-600 border-green-200"
            };
            
            return (
              <Card key={index} className="hover:shadow-lg transition-shadow border-2 hover:border-blue-200">
                <div className="flex items-start space-x-4">
                  <div className={`p-4 rounded-2xl ${colorClasses[feature.color]}`}>
                    <IconComponent className="h-8 w-8" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                    <p className="text-gray-600 mb-4 leading-relaxed">{feature.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500 font-medium">{feature.stats}</span>
                      <Link 
                        to={feature.link}
                        className="flex items-center space-x-1 text-blue-600 hover:text-blue-700 font-semibold"
                      >
                        <span>Get Started</span>
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Platform Capabilities */}
        <Card title="Platform Capabilities" subtitle="Comprehensive tools for eDNA analysis and research">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {capabilities.map((capability, index) => {
              const IconComponent = capability.icon;
              return (
                <div key={index} className="text-center">
                  <div className="bg-gray-100 p-4 rounded-2xl inline-flex mb-4">
                    <IconComponent className="h-8 w-8 text-gray-600" />
                  </div>
                  <h4 className="font-semibold text-gray-900 mb-2">{capability.title}</h4>
                  <p className="text-sm text-gray-600 mb-2">{capability.description}</p>
                  <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-lg">
                    {capability.count}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>

        {/* How It Works */}
        <Card title="How It Works" subtitle="Simple workflow for eDNA analysis">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-blue-100 p-4 rounded-2xl inline-flex mb-4">
                <span className="text-2xl font-bold text-blue-600">1</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Search & Explore</h4>
              <p className="text-sm text-gray-600">
                Browse existing datasets, filter by location, taxa, or sample type to find relevant data
              </p>
            </div>
            <div className="text-center">
              <div className="bg-green-100 p-4 rounded-2xl inline-flex mb-4">
                <span className="text-2xl font-bold text-green-600">2</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Analyze Results</h4>
              <p className="text-sm text-gray-600">
                View detailed visualizations, cluster analysis, and biodiversity metrics for your data
              </p>
            </div>
            <div className="text-center">
              <div className="bg-amber-100 p-4 rounded-2xl inline-flex mb-4">
                <span className="text-2xl font-bold text-amber-600">3</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Submit & Contribute</h4>
              <p className="text-sm text-gray-600">
                Upload your own samples to expand the database and support marine research
              </p>
            </div>
          </div>
        </Card>

        {/* Research Impact */}
        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-2xl p-6 border border-green-100">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Research Impact</h3>
            <p className="text-gray-600 mb-6 max-w-3xl mx-auto">
              Supporting marine biodiversity research worldwide through advanced eDNA analysis, 
              species discovery, and ecosystem monitoring for conservation efforts.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <div className="text-3xl font-bold text-blue-600 mb-2">1M+</div>
                <div className="text-sm text-gray-600">Sequences Analyzed</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">500+</div>
                <div className="text-sm text-gray-600">Species Identified</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-600 mb-2">50+</div>
                <div className="text-sm text-gray-600">Novel Taxa Discovered</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;