import React, { useState } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { 
  Search, 
  Filter, 
  Database, 
  Dna, 
  GitBranch, 
  Download, 
  Eye, 
  MapPin, 
  Calendar,
  BarChart3,
  TrendingUp,
  Layers
} from 'lucide-react';
import Layout from '../components/Layout';
import Card from '../components/Card';
const COLORS = ['#1e40af', '#3b82f6', '#60a5fa', '#93c5fd', '#dbeafe', '#dc2626', '#16a34a', '#ca8a04', '#9333ea'];

const SearchData = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDatabase, setSelectedDatabase] = useState('all');
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [selectedDateRange, setSelectedDateRange] = useState('all');
  const [viewMode, setViewMode] = useState('grid'); // grid or list
  const [loading, setLoading] = useState(false);

  // Mock data for visualizations
  const taxonomicDistribution = [
    { name: 'Proteobacteria', value: 450, percentage: '45.0' },
    { name: 'Bacteroidetes', value: 280, percentage: '28.0' },
    { name: 'Firmicutes', value: 150, percentage: '15.0' },
    { name: 'Actinobacteria', value: 120, percentage: '12.0' }
  ];

  const clusterDistribution = [
    { clusterId: 'C1', size: 120, diversity: 0.85 },
    { clusterId: 'C2', size: 95, diversity: 0.72 },
    { clusterId: 'C3', size: 89, diversity: 0.68 },
    { clusterId: 'C4', size: 76, diversity: 0.91 },
    { clusterId: 'C5', size: 67, diversity: 0.78 },
    { clusterId: 'C6', size: 54, diversity: 0.65 }
  ];

  // Mock search results data
  const searchResults = [
    {
      id: 'DS_001',
      title: 'Pacific Ocean Deep Sea Sample - Site A',
      database: '16S_ribosomal_RNA',
      location: 'Pacific Ocean',
      coordinates: '35.6762°N, 139.6503°E',
      date: '2024-03-15',
      sequences: 1245,
      clusters: 89,
      novelTaxa: 12,
      quality: 98.5,
      dominantTaxa: ['Proteobacteria', 'Bacteroidetes', 'Firmicutes'],
      shannonIndex: 3.42,
      description: 'Deep sea eDNA sample from Pacific Ocean showing high microbial diversity'
    },
    {
      id: 'DS_002', 
      title: 'Arctic Ocean Fungal Community - Site B',
      database: '18S_fungal_sequences',
      location: 'Arctic Ocean',
      coordinates: '71.0°N, 8.0°W',
      date: '2024-02-28',
      sequences: 892,
      clusters: 67,
      novelTaxa: 8,
      quality: 96.2,
      dominantTaxa: ['Ascomycota', 'Basidiomycota'],
      shannonIndex: 2.87,
      description: 'Arctic marine fungal communities with cold-adapted species'
    },
    {
      id: 'DS_003',
      title: 'Mediterranean Coastal Sample - Site C', 
      database: '28S_fungal_sequences',
      location: 'Mediterranean Sea',
      coordinates: '43.7696°N, 7.4081°E',
      date: '2024-03-10',
      sequences: 567,
      clusters: 45,
      novelTaxa: 5,
      quality: 94.8,
      dominantTaxa: ['Ascomycota', 'Chytridiomycota'],
      shannonIndex: 2.31,
      description: 'Coastal Mediterranean fungal diversity analysis'
    }
  ];

  const filteredResults = searchResults.filter(result => {
    const matchesSearch = !searchQuery || 
      result.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      result.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      result.dominantTaxa.some(taxa => taxa.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesDatabase = selectedDatabase === 'all' || result.database === selectedDatabase;
    const matchesLocation = selectedLocation === 'all' || result.location.toLowerCase().includes(selectedLocation.toLowerCase());
    
    return matchesSearch && matchesDatabase && matchesLocation;
  });

  const selectedResult = filteredResults[0]; // For detailed view

  return (
    <Layout title="Search Data">
      <div className="space-y-6">
        {/* Search Header */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
            <Search className="h-6 w-6 mr-2 text-blue-600" />
            Search eDNA Data
          </h2>
          <p className="text-gray-600 mb-6">
            Explore comprehensive datasets from various sources with detailed analysis and visualizations
          </p>

          {/* Search Bar */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by location, taxa, or sample name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <select
              value={selectedDatabase}
              onChange={(e) => setSelectedDatabase(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Databases</option>
              <option value="16S_ribosomal_RNA">16S ribosomal RNA</option>
              <option value="18S_fungal_sequences">18S fungal sequences</option>
              <option value="28S_fungal_sequences">28S fungal sequences</option>
              <option value="Betacoronavirus">Betacoronavirus</option>
            </select>
            
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Locations</option>
              <option value="pacific">Pacific Ocean</option>
              <option value="atlantic">Atlantic Ocean</option>
              <option value="arctic">Arctic Ocean</option>
              <option value="mediterranean">Mediterranean Sea</option>
            </select>

            <select
              value={selectedDateRange}
              onChange={(e) => setSelectedDateRange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Time</option>
              <option value="last30">Last 30 days</option>
              <option value="last90">Last 90 days</option>
              <option value="lastyear">Last year</option>
            </select>

            <div className="flex space-x-2">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-4 py-2 rounded-xl ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}
              >
                <Layers className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-4 py-2 rounded-xl ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}
              >
                <BarChart3 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Search Results Count */}
        <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
          <p className="text-blue-800">
            Found <span className="font-bold">{filteredResults.length}</span> datasets matching your criteria
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Search Results List */}
          <div className="lg:col-span-2">
            <Card title="Search Results" subtitle="eDNA datasets from various sources">
              <div className="space-y-4">
                {filteredResults.map((result) => (
                  <div key={result.id} className="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-1">{result.title}</h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span className="flex items-center">
                            <Database className="h-4 w-4 mr-1" />
                            {result.database.replace(/_/g, ' ')}
                          </span>
                          <span className="flex items-center">
                            <MapPin className="h-4 w-4 mr-1" />
                            {result.location}
                          </span>
                          <span className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            {result.date}
                          </span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg">
                          <Eye className="h-4 w-4" />
                        </button>
                        <button className="p-2 text-green-600 hover:bg-green-50 rounded-lg">
                          <Download className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3">{result.description}</p>
                    
                    <div className="grid grid-cols-4 gap-4 text-center">
                      <div>
                        <div className="text-lg font-bold text-blue-600">{result.sequences}</div>
                        <div className="text-xs text-gray-500">Sequences</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-green-600">{result.clusters}</div>
                        <div className="text-xs text-gray-500">Clusters</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-amber-600">{result.novelTaxa}</div>
                        <div className="text-xs text-gray-500">Novel Taxa</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-purple-600">{result.shannonIndex}</div>
                        <div className="text-xs text-gray-500">Shannon Index</div>
                      </div>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2">
                      {result.dominantTaxa.map((taxa, index) => (
                        <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-lg">
                          {taxa}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Detailed Analysis Sidebar */}
          <div className="space-y-6">
            {selectedResult && (
              <>
                {/* Selected Dataset Overview */}
                <Card title="Dataset Details" subtitle={selectedResult.title}>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-blue-50 rounded-xl">
                        <div className="text-xl font-bold text-blue-600">{selectedResult.sequences}</div>
                        <div className="text-sm text-gray-600">Sequences</div>
                      </div>
                      <div className="text-center p-3 bg-green-50 rounded-xl">
                        <div className="text-xl font-bold text-green-600">{selectedResult.clusters}</div>
                        <div className="text-sm text-gray-600">Clusters</div>
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-600 space-y-2">
                      <div className="flex justify-between">
                        <span>Location:</span>
                        <span className="font-medium">{selectedResult.location}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Coordinates:</span>
                        <span className="font-medium">{selectedResult.coordinates}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Collection Date:</span>
                        <span className="font-medium">{selectedResult.date}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Quality Score:</span>
                        <span className="font-medium text-green-600">{selectedResult.quality}%</span>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Taxonomic Distribution for Selected */}
                <Card title="Taxonomic Distribution" subtitle="Species composition">
                  {taxonomicDistribution && taxonomicDistribution.length > 0 ? (
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={taxonomicDistribution}
                            cx="50%"
                            cy="50%"
                            outerRadius={60}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {taxonomicDistribution.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-64 flex items-center justify-center text-gray-500">
                      <p>No distribution data available</p>
                    </div>
                  )}
                </Card>

                {/* Cluster Analysis */}
                <Card title="Cluster Analysis" subtitle="Size distribution">
                  {clusterDistribution && clusterDistribution.length > 0 ? (
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={clusterDistribution.slice(0, 6)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="clusterId" tick={{ fontSize: 10 }} />
                          <YAxis tick={{ fontSize: 10 }} />
                          <Tooltip />
                          <Bar dataKey="size" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-64 flex items-center justify-center text-gray-500">
                      <p>No cluster data available</p>
                    </div>
                  )}
                </Card>
              </>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default SearchData;