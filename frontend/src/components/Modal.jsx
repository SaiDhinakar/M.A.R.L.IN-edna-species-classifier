import React, { useEffect } from 'react';
import { X } from 'lucide-react';

const Modal = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'md',
  className = '' 
}) => {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-7xl',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        {/* Center the modal */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" />

        {/* Modal panel */}
        <div
          className={`
            inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:p-6
            ${sizes[size]}
            ${className}
          `}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            {title && (
              <h3 className="text-lg font-medium text-gray-900">
                {title}
              </h3>
            )}
            <button
              onClick={onClose}
              className="rounded-md bg-white text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          <div className="mt-2">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

// Confirmation modal variant
export const ConfirmModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = "Confirm Action", 
  message = "Are you sure you want to proceed?",
  confirmText = "Confirm",
  cancelText = "Cancel",
  variant = "danger"
}) => {
  const buttonColors = {
    danger: 'bg-red-600 hover:bg-red-700 text-white',
    primary: 'bg-primary-600 hover:bg-primary-700 text-white',
    success: 'bg-green-600 hover:bg-green-700 text-white',
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <div className="mt-2">
        <p className="text-sm text-gray-500">{message}</p>
      </div>
      <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
        <button
          type="button"
          onClick={onConfirm}
          className={`w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm ${buttonColors[variant]}`}
        >
          {confirmText}
        </button>
        <button
          type="button"
          onClick={onClose}
          className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:w-auto sm:text-sm"
        >
          {cancelText}
        </button>
      </div>
    </Modal>
  );
};

export default Modal;