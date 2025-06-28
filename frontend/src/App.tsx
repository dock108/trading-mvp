import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import ControlsPanel from './components/ControlsPanel';
import ResultsPanel from './components/ResultsPanel';
import type { ConfigData, StrategyResults } from './types';

// Configure axios defaults
axios.defaults.baseURL = 'http://127.0.0.1:8000';

function App() {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [results, setResults] = useState<StrategyResults | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('Ready');

  // Load initial configuration
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await axios.get('/api/config');
      setConfig(response.data);
    } catch (err) {
      console.error('Failed to load config:', err);
      setError('Failed to load configuration');
    }
  };

  const updateConfig = async (newConfig: Partial<ConfigData>) => {
    try {
      const response = await axios.put('/api/config', newConfig);
      setConfig(response.data.config);
      return true;
    } catch (err) {
      console.error('Failed to update config:', err);
      setError('Failed to update configuration');
      return false;
    }
  };

  const runStrategies = async (strategies: string[], configOverrides?: any) => {
    setIsLoading(true);
    setError(null);
    setStatus('Running strategies...');
    setResults(null);

    try {
      const response = await axios.post('/api/run', {
        strategies,
        config_overrides: configOverrides,
        backtest: true
      });

      setResults(response.data);
      setStatus(`Completed at ${new Date().toLocaleTimeString()}`);
    } catch (err: any) {
      console.error('Failed to run strategies:', err);
      setError(err.response?.data?.detail || 'Failed to run strategies');
      setStatus('Failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (!config) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Loading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls Panel */}
          <div className="lg:col-span-1">
            <ControlsPanel
              config={config}
              onConfigUpdate={updateConfig}
              onRunStrategies={runStrategies}
              isLoading={isLoading}
              status={status}
              error={error}
            />
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            <ResultsPanel
              results={results}
              isLoading={isLoading}
              config={config}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
