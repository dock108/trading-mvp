import React from 'react';
import { TrendingUp, Settings, Download, Upload } from 'lucide-react';

const Header: React.FC = () => {
  const handleDownloadConfig = () => {
    // Create a download link for the config file
    const link = document.createElement('a');
    link.href = 'http://127.0.0.1:8000/api/download/config';
    link.download = 'config.yaml';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleUploadConfig = () => {
    // Create a file input for uploading config
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.yaml,.yml';
    input.addEventListener('change', async (event) => {
      const file = (event.target as HTMLInputElement).files?.[0];
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
          const response = await fetch('http://127.0.0.1:8000/api/upload/config', {
            method: 'POST',
            body: formData,
          });
          
          if (response.ok) {
            alert('Configuration uploaded successfully! Please refresh the page.');
            window.location.reload();
          } else {
            alert('Failed to upload configuration');
          }
        } catch (error) {
          console.error('Upload error:', error);
          alert('Failed to upload configuration');
        }
      }
    });
    input.click();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600 rounded-lg">
              <TrendingUp className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Trading Dashboard</h1>
              <p className="text-sm text-gray-600">Personal Trading MVP - Sprint 3</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleUploadConfig}
              className="flex items-center space-x-2 btn-secondary text-sm"
              title="Upload Configuration"
            >
              <Upload className="h-4 w-4" />
              <span className="hidden sm:inline">Upload Config</span>
            </button>
            
            <button
              onClick={handleDownloadConfig}
              className="flex items-center space-x-2 btn-secondary text-sm"
              title="Download Configuration"
            >
              <Download className="h-4 w-4" />
              <span className="hidden sm:inline">Download Config</span>
            </button>

            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">v3.0.0</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;