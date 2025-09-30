import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  Upload,
  Settings,
  Menu,
  X,
  Dna
} from 'lucide-react';

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Search Data', href: '/search', icon: Search },
    { name: 'Submit Data', href: '/submit', icon: Upload },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const isActive = (href) => location.pathname === href;

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-lg border"
      >
        {isMobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-40 bg-white border-r border-gray-200 transition-transform duration-300 ease-in-out shadow-lg lg:shadow-none
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          ${isCollapsed ? 'w-16' : 'w-64'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo section */}
          <div className="h-20 flex items-center justify-between px-4 border-b border-gray-200">
            {!isCollapsed && (
              <div className="flex items-center">
                <div className="h-10 w-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-md">
                  <Dna className="h-6 w-6 text-white" />
                </div>
                <span className="ml-3 text-lg font-bold text-gray-900">M.A.R.L.IN</span>
              </div>
            )}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="hidden lg:block p-2 rounded-xl hover:bg-gray-100 transition-colors"
            >
              <Menu className="h-5 w-5 text-gray-600" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsMobileOpen(false)}
                  className={`
                    flex items-center px-4 py-3 text-sm font-medium rounded-2xl transition-all duration-200
                    ${isActive(item.href)
                      ? 'bg-blue-50 text-blue-700 shadow-md border-l-4 border-l-blue-600'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  <Icon
                    className={`
                      h-5 w-5 flex-shrink-0
                      ${isActive(item.href) ? 'text-blue-600' : 'text-gray-500'}
                    `}
                  />
                  {!isCollapsed && <span className="ml-3">{item.name}</span>}
                </Link>
              );
            })}
          </nav>

          {/* User info at bottom */}
          {!isCollapsed && (
            <div className="p-4 border-t border-gray-100">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-3">
                <div className="text-xs font-medium text-blue-900 mb-1">
                  M.A.R.L.IN Pipeline
                </div>
                <div className="text-xs text-blue-700">
                  Version 1.0.0 - Marine Biodiversity Analysis
                </div>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;