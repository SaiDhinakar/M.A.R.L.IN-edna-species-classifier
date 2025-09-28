import React, { useState } from 'react';
import { Bell, User, ChevronDown } from 'lucide-react';

const Header = ({ title = "Dashboard" }) => {
  const [showProfile, setShowProfile] = useState(false);

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6">
      <div className="flex items-center">
        <h1 className="text-2xl font-bold text-primary-900">DeepSea eDNA Dashboard</h1>
        <span className="ml-4 text-gray-500">/</span>
        <span className="ml-2 text-lg text-gray-700">{title}</span>
      </div>
      
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <button className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
        </button>
        
        {/* Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center space-x-2 p-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <div className="h-8 w-8 bg-primary-600 rounded-full flex items-center justify-center">
              <User className="h-5 w-5 text-white" />
            </div>
            <span className="hidden md:block text-sm font-medium">Dr. Sarah Chen</span>
            <ChevronDown className="h-4 w-4" />
          </button>
          
          {showProfile && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
              <a href="#" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Profile</a>
              <a href="#" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Settings</a>
              <hr className="my-1" />
              <a href="#" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Sign out</a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;