import React from 'react';

const Card = ({ 
  children, 
  className = '', 
  title, 
  subtitle, 
  action,
  padding = 'p-6' 
}) => {
  return (
    <div className={`bg-white rounded-2xl shadow-md hover:shadow-lg transition-shadow duration-200 border border-gray-100 ${className}`}>
      {(title || subtitle || action) && (
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
            {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={padding}>
        {children}
      </div>
    </div>
  );
};

// Metric card variant for dashboard statistics
const MetricCard = ({ title, value, change, changeType, icon: Icon, color = 'blue' }) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-700',
    green: 'bg-green-100 text-green-700',
    amber: 'bg-amber-100 text-amber-700',
    red: 'bg-red-100 text-red-700',
  };

  const changeColor = changeType === 'positive' ? 'text-green-700' : 
                     changeType === 'negative' ? 'text-red-700' : 'text-gray-700';

  return (
    <Card className="hover:shadow-lg transition-all duration-200 border-l-4 border-l-blue-500">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-700">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {change && (
            <p className={`text-sm mt-2 font-medium ${changeColor}`}>
              {change}
            </p>
          )}
        </div>
        {Icon && (
          <div className={`p-4 rounded-2xl ${colorClasses[color]} flex-shrink-0`}>
            <Icon className="h-8 w-8" />
          </div>
        )}
      </div>
    </Card>
  );
};

export default Card;
export { MetricCard };