import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Sequences from './pages/Sequences';
import SequenceDetail from './pages/SequenceDetail';
import Clusters from './pages/Clusters';
import ClusterDetail from './pages/ClusterDetail';
import Metrics from './pages/Metrics';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Routes>
          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Main pages */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/sequences" element={<Sequences />} />
          <Route path="/sequence/:id" element={<SequenceDetail />} />
          <Route path="/clusters" element={<Clusters />} />
          <Route path="/cluster/:id" element={<ClusterDetail />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/settings" element={<Settings />} />
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
