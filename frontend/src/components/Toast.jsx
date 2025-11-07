import { useEffect, useState } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

const Toast = ({ message, type = 'info', duration = 4000, onClose }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => {
        onClose?.();
      }, 300); // Wait for fade-out animation
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => {
      onClose?.();
    }, 300);
  };

  const types = {
    success: {
      bgColor: 'bg-green-50',
      borderColor: 'border-green-500',
      textColor: 'text-green-800',
      icon: <CheckCircle className="w-5 h-5 text-green-500" />,
    },
    error: {
      bgColor: 'bg-red-50',
      borderColor: 'border-red-500',
      textColor: 'text-red-800',
      icon: <AlertCircle className="w-5 h-5 text-red-500" />,
    },
    warning: {
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-500',
      textColor: 'text-yellow-800',
      icon: <AlertTriangle className="w-5 h-5 text-yellow-500" />,
    },
    info: {
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-500',
      textColor: 'text-blue-800',
      icon: <Info className="w-5 h-5 text-blue-500" />,
    },
  };

  const { bgColor, borderColor, textColor, icon } = types[type] || types.info;

  return (
    <div
      className={`fixed top-4 right-4 z-50 flex items-center gap-3 min-w-[300px] max-w-[500px] p-4 rounded-lg shadow-lg border-l-4 transition-all duration-300 ${
        isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'
      } ${bgColor} ${borderColor}`}
    >
      <div className="flex-shrink-0">{icon}</div>
      <p className={`flex-1 text-sm font-medium ${textColor}`}>{message}</p>
      <button
        onClick={handleClose}
        className={`flex-shrink-0 ${textColor} hover:opacity-70 transition-opacity`}
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

// Toast Container to manage multiple toasts
export const ToastContainer = ({ toasts, removeToast }) => {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );
};

export default Toast;
