import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Dna,
  GitBranch,
  BarChart3,
  Settings,
  Menu,
  X
} from 'lucide-react';

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Sequences', href: '/sequences', icon: Dna },
    { name: 'Clusters', href: '/clusters', icon: GitBranch },
    { name: 'Metrics', href: '/metrics', icon: BarChart3 },
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
          fixed lg:static inset-y-0 left-0 z-40 bg-white border-r border-gray-200 transition-transform duration-300 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          ${isCollapsed ? 'w-16' : 'w-64'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo section */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
            {!isCollapsed && (
              <div className="flex items-center">
                <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <Dna className="h-5 w-5 text-white" />
                </div>
                <span className="ml-2 text-lg font-semibold text-gray-900">eDNA</span>
              </div>
            )}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="hidden lg:block p-1 rounded hover:bg-gray-100"
            >
              <Menu className="h-5 w-5 text-gray-500" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsMobileOpen(false)}
                  className={`
                    flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors
                    ${isActive(item.href)
                      ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                      : 'text-gray-700 hover:bg-gray-100'
                    }
                  `}
                >
                  <Icon
                    className={`
                      h-5 w-5 flex-shrink-0
                      ${isActive(item.href) ? 'text-primary-600' : 'text-gray-500'}
                    `}
                  />
                  {!isCollapsed && <span className="ml-3">{item.name}</span>}
                </Link>
              );
            })}
          </nav>

          {/* User info at bottom */}
          {!isCollapsed && (
            <div className="p-4 border-t border-gray-200">
              <div className="text-xs text-gray-500">
                Version 1.0.0
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;