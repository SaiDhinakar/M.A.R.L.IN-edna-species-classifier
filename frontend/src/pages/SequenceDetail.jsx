import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Copy, Download, Star, Eye, Edit } from 'lucide-react';
import Layout from '../components/Layout';
import Card from '../components/Card';
import Badge, { QualityBadge, NoveltyBadge } from '../components/Badge';
import { LoadingOverlay } from '../components/Loading';
import { useSequence } from '../hooks/useData';

const SequenceDetail = () => {
  const { id } = useParams();
  const { sequence, loading, error } = useSequence(id);
  const [notes, setNotes] = useState('');
  const [isEditingNotes, setIsEditingNotes] = useState(false);

  const copySequence = () => {
    navigator.clipboard.writeText(sequence.sequence);
    // Could add toast notification here
  };

  const downloadFasta = () => {
    const fasta = `>${sequence.id} | ${sequence.taxa} | Quality: ${sequence.quality}%\n${sequence.sequence}`;
    const blob = new Blob([fasta], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${sequence.id}.fasta`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Layout title="Sequence Details">
        <LoadingOverlay message="Loading sequence details..." />
      </Layout>
    );
  }

  if (error || !sequence) {
    return (
      <Layout title="Sequence Details">
        <div className="text-center py-12">
          <p className="text-red-600">Error loading sequence: {error || 'Sequence not found'}</p>
          <Link 
            to="/sequences" 
            className="mt-4 inline-flex items-center text-primary-600 hover:text-primary-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Sequences
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Sequence ${sequence.id}`}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link 
              to="/sequences"
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{sequence.id}</h1>
              <p className="text-sm text-gray-600">
                Cluster: <Link to={`/cluster/${sequence.cluster}`} className="text-primary-600 hover:underline">{sequence.cluster}</Link>
              </p>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={copySequence}
              className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <Copy className="h-4 w-4 mr-2" />
              Copy
            </button>
            <button
              onClick={downloadFasta}
              className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <Download className="h-4 w-4 mr-2" />
              Download
            </button>
            <button className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
              <Star className="h-4 w-4 mr-2" />
              Mark for Review
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Sequence Information */}
            <Card title="Sequence Information">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Sequence ID</label>
                    <p className="mt-1 font-mono text-sm text-gray-900">{sequence.id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Length</label>
                    <p className="mt-1 text-sm text-gray-900">{sequence.length.toLocaleString()} bp</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Quality Score</label>
                    <div className="mt-1">
                      <QualityBadge score={sequence.quality} />
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Taxonomic Assignment</label>
                    <div className="mt-1">
                      <Badge variant={sequence.taxa === 'Novel' ? 'novel' : 'known'}>
                        {sequence.taxa}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Novelty Score</label>
                    <div className="mt-1">
                      <NoveltyBadge score={sequence.novelty_score} />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Sample Date</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {new Date(sequence.sample_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            {/* Sequence Data */}
            <Card 
              title="Sequence Data"
              action={
                <button
                  onClick={copySequence}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  Copy Sequence
                </button>
              }
            >
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <pre className="text-green-400 font-mono text-sm leading-relaxed whitespace-pre-wrap break-all">
                  {sequence.sequence}
                </pre>
              </div>
              <div className="mt-3 text-xs text-gray-500">
                Sequence length: {sequence.length} base pairs
              </div>
            </Card>

            {/* Taxonomic Hierarchy (Mock visualization) */}
            <Card title="Taxonomic Classification" subtitle="Hierarchical classification tree">
              <div className="space-y-3">
                {[
                  { level: 'Kingdom', name: 'Bacteria', confidence: 0.98 },
                  { level: 'Phylum', name: sequence.taxa === 'Novel' ? 'Unknown' : sequence.taxa, confidence: sequence.taxa === 'Novel' ? 0.45 : 0.92 },
                  { level: 'Class', name: sequence.taxa === 'Novel' ? 'Unknown' : `${sequence.taxa}ia`, confidence: sequence.taxa === 'Novel' ? 0.32 : 0.87 },
                  { level: 'Order', name: sequence.taxa === 'Novel' ? 'Unknown' : `${sequence.taxa}ales`, confidence: sequence.taxa === 'Novel' ? 0.21 : 0.78 },
                  { level: 'Family', name: sequence.taxa === 'Novel' ? 'Unknown' : `${sequence.taxa}aceae`, confidence: sequence.taxa === 'Novel' ? 0.15 : 0.65 }
                ].map((tax, index) => (
                  <div key={tax.level} className="flex items-center space-x-4 ml-4" style={{ marginLeft: `${index * 20}px` }}>
                    <div className="h-2 w-2 bg-primary-400 rounded-full"></div>
                    <div className="flex-1 flex items-center justify-between">
                      <div>
                        <span className="text-sm font-medium text-gray-900">{tax.level}:</span>
                        <span className="ml-2 text-sm text-gray-700">{tax.name}</span>
                      </div>
                      <Badge 
                        variant={tax.confidence > 0.8 ? 'success' : tax.confidence > 0.5 ? 'warning' : 'danger'}
                        size="sm"
                      >
                        {(tax.confidence * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Sample Information */}
            <Card title="Sample Information">
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Location</label>
                  <p className="mt-1 text-sm text-gray-900">{sequence.location}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Collection Date</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {new Date(sequence.sample_date).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Cluster</label>
                  <Link 
                    to={`/cluster/${sequence.cluster}`}
                    className="mt-1 inline-flex items-center text-sm text-primary-600 hover:text-primary-700 hover:underline"
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    {sequence.cluster}
                  </Link>
                </div>
              </div>
            </Card>

            {/* Quality Metrics */}
            <Card title="Quality Metrics">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Overall Quality</span>
                  <QualityBadge score={sequence.quality} />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Novelty Score</span>
                  <span className="text-sm font-medium">{sequence.novelty_score.toFixed(3)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Length</span>
                  <span className="text-sm font-medium">{sequence.length} bp</span>
                </div>
              </div>
            </Card>

            {/* Notes & Annotations */}
            <Card 
              title="Notes & Annotations"
              action={
                <button
                  onClick={() => setIsEditingNotes(!isEditingNotes)}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  <Edit className="h-4 w-4" />
                </button>
              }
            >
              {isEditingNotes ? (
                <div className="space-y-3">
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Add your notes and annotations here..."
                    className="w-full h-24 px-3 py-2 border border-gray-300 rounded-md text-sm resize-none focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  />
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setIsEditingNotes(false)}
                      className="px-3 py-1 text-sm bg-primary-600 text-white rounded-md hover:bg-primary-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => {
                        setIsEditingNotes(false);
                        setNotes('');
                      }}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-600">
                  {notes || 'No notes added yet. Click the edit button to add annotations.'}
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default SequenceDetail;