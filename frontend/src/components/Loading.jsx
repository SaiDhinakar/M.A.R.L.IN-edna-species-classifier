import React from 'react';

// Spinner component
export const Spinner = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  return (
    <div
      className={`animate-spin rounded-full border-2 border-gray-300 border-t-primary-600 ${sizes[size]} ${className}`}
    />
  );
};

// Loading overlay for full page/component
export const LoadingOverlay = ({ message = "Loading..." }) => {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <Spinner size="lg" />
        <p className="mt-4 text-gray-600">{message}</p>
      </div>
    </div>
  );
};

// Skeleton loader for table rows
export const TableSkeleton = ({ rows = 5, columns = 4 }) => {
  return (
    <div className="animate-pulse">
      {[...Array(rows)].map((_, rowIndex) => (
        <div key={rowIndex} className="flex space-x-4 py-4 border-b border-gray-200">
          {[...Array(columns)].map((_, colIndex) => (
            <div key={colIndex} className="flex-1">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

// Card skeleton
export const CardSkeleton = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="h-12 w-12 bg-gray-200 rounded-lg"></div>
      </div>
    </div>
  );
};

const Loading = { Spinner, LoadingOverlay, TableSkeleton, CardSkeleton };
export default Loading;