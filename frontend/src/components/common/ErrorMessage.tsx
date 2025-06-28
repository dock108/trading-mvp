import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface ErrorMessageProps {
  error: string | null;
  onDismiss?: () => void;
  variant?: 'inline' | 'banner' | 'card';
  className?: string;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({
  error,
  onDismiss,
  variant = 'inline',
  className = ''
}) => {
  if (!error) return null;

  const baseClasses = 'flex items-start space-x-2 text-red-600';
  
  const variantClasses = {
    inline: 'text-sm',
    banner: 'p-3 bg-red-50 border border-red-200 rounded-md',
    card: 'p-4 bg-red-50 border border-red-200 rounded-lg shadow-sm'
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm">{error}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-400 hover:text-red-600 flex-shrink-0"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;