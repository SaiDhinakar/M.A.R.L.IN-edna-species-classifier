import React from 'react';
import { Search } from 'lucide-react';

// Base Input component
export const Input = ({ 
  label, 
  error, 
  className = '', 
  ...props 
}) => {
  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <input
        className={`
          block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400
          focus:outline-none focus:ring-primary-500 focus:border-primary-500
          ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}
        `}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

// Search Input component
export const SearchInput = ({ 
  placeholder = "Search...", 
  value, 
  onChange, 
  className = '' 
}) => {
  return (
    <div className={`relative ${className}`}>
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <Search className="h-5 w-5 text-gray-400" />
      </div>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
      />
    </div>
  );
};

// Select Dropdown component
export const Select = ({ 
  label, 
  options = [], 
  error, 
  placeholder = "Select an option",
  className = '', 
  ...props 
}) => {
  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <select
        className={`
          block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white
          focus:outline-none focus:ring-primary-500 focus:border-primary-500
          ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}
        `}
        {...props}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

// Toggle Switch component
export const Switch = ({ 
  label, 
  checked, 
  onChange, 
  className = '' 
}) => {
  return (
    <div className={`flex items-center ${className}`}>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={`
          relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent 
          transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
          ${checked ? 'bg-primary-600' : 'bg-gray-200'}
        `}
      >
        <span
          className={`
            pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 
            transition duration-200 ease-in-out
            ${checked ? 'translate-x-5' : 'translate-x-0'}
          `}
        />
      </button>
      {label && (
        <span className="ml-3 text-sm font-medium text-gray-700">
          {label}
        </span>
      )}
    </div>
  );
};

// Filter Bar component
export const FilterBar = ({ 
  searchValue, 
  onSearchChange, 
  filters = [], 
  className = '' 
}) => {
  return (
    <div className={`flex flex-col sm:flex-row gap-4 ${className}`}>
      <div className="flex-1">
        <SearchInput
          value={searchValue}
          onChange={onSearchChange}
          placeholder="Search sequences, clusters, or taxa..."
        />
      </div>
      <div className="flex gap-2">
        {filters.map((filter) => (
          <Select
            key={filter.key}
            placeholder={filter.placeholder}
            options={filter.options}
            value={filter.value}
            onChange={filter.onChange}
            className="min-w-[150px]"
          />
        ))}
      </div>
    </div>
  );
};