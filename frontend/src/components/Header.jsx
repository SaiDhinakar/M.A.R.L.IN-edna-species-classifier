import React, { useState } from 'react';
import { Bell, User, ChevronDown } from 'lucide-react';

const Header = ({ title = "Dashboard" }) => {
  const [showProfile, setShowProfile] = useState(false);

  return (
    <header className="bg-white border-b border-gray-200 h-20 flex items-center justify-between px-6 shadow-sm">
      <div className="flex items-center">
        <h1 className="text-2xl font-bold text-gray-900">M.A.R.L.IN eDNA Pipeline</h1>
        <span className="ml-4 text-gray-400">/</span>
        <span className="ml-2 text-lg font-medium text-gray-700">{title}</span>
      </div>
      
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <button className="relative p-3 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all duration-200">
          <Bell className="h-5 w-5" />
          <span className="absolute top-2 right-2 h-2 w-2 bg-red-500 rounded-full"></span>
        </button>
        
        {/* Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center space-x-3 p-2 text-gray-700 hover:bg-gray-100 rounded-xl transition-all duration-200"
          >
            <div className="h-10 w-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center shadow-md">
              <User className="h-5 w-5 text-white" />
            </div>
            <div className="hidden md:block text-left">
              <p className="text-sm font-semibold text-gray-900">Dr. Sarah Chen</p>
              <p className="text-xs text-gray-600">Marine Biologist</p>
            </div>
            <ChevronDown className="h-4 w-4 text-gray-500" />
          </button>
          
          {showProfile && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-lg border border-gray-100 py-2 z-50">
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="text-sm font-semibold text-gray-900">Dr. Sarah Chen</p>
                <p className="text-xs text-gray-600">sarah.chen@marine-institute.org</p>
              </div>
              <a href="#" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors">Profile Settings</a>
              <a href="#" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors">Analysis Preferences</a>
              <a href="#" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors">Export History</a>
              <hr className="my-2 border-gray-100" />
              <a href="#" className="block px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors">Sign out</a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;