import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import SearchData from './pages/SearchData';
import SubmitData from './pages/SubmitData';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Main pages */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/search" element={<SearchData />} />
          <Route path="/submit" element={<SubmitData />} />
          <Route path="/settings" element={<Settings />} />
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
