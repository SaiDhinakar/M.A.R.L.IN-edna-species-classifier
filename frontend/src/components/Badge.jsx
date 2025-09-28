import React from 'react';

const Badge = ({ 
  children, 
  variant = 'default', 
  size = 'md',
  className = '' 
}) => {
  const variants = {
    default: 'bg-gray-100 text-gray-800',
    primary: 'bg-primary-100 text-primary-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-amber-100 text-amber-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
    novel: 'bg-purple-100 text-purple-800',
    known: 'bg-green-100 text-green-800',
  };

  const sizes = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };

  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-full
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
    >
      {children}
    </span>
  );
};

// Quality score badge with automatic color coding
export const QualityBadge = ({ score }) => {
  let variant = 'danger';
  if (score >= 95) variant = 'success';
  else if (score >= 85) variant = 'warning';
  else if (score >= 70) variant = 'info';

  return (
    <Badge variant={variant}>
      {score}%
    </Badge>
  );
};

// Novelty score badge
export const NoveltyBadge = ({ score }) => {
  const variant = score > 0.7 ? 'novel' : score > 0.4 ? 'warning' : 'known';
  const label = score > 0.7 ? 'Novel' : score > 0.4 ? 'Partial' : 'Known';

  return (
    <Badge variant={variant}>
      {label} ({score.toFixed(2)})
    </Badge>
  );
};

export default Badge;