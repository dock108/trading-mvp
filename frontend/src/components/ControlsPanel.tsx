import React, { useState } from 'react';
import { Play, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import type { ConfigData } from '../types';

interface ControlsPanelProps {
  config: ConfigData;
  onConfigUpdate: (newConfig: Partial<ConfigData>) => Promise<boolean>;
  onRunStrategies: (strategies: string[], configOverrides?: any) => void;
  isLoading: boolean;
  status: string;
  error: string | null;
}

const ControlsPanel: React.FC<ControlsPanelProps> = ({
  config,
  onConfigUpdate,
  onRunStrategies,
  isLoading,
  status,
  error
}) => {
  const [localConfig, setLocalConfig] = useState(config);
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>(['wheel', 'rotator']);

  const handleConfigChange = (key: string, value: any, nested?: string) => {
    setLocalConfig(prev => {
      const newConfig = { ...prev };
      if (nested) {
        newConfig[nested] = { ...newConfig[nested], [key]: value };
      } else {
        newConfig[key] = value;
      }
      return newConfig;
    });
  };

  const handleStrategyToggle = (strategy: string) => {
    setSelectedStrategies(prev => 
      prev.includes(strategy) 
        ? prev.filter(s => s !== strategy)
        : [...prev, strategy]
    );
  };

  const handleSymbolsChange = (type: 'wheel_symbols' | 'rotator_symbols', value: string) => {
    const symbols = value.split(',').map(s => s.trim()).filter(s => s.length > 0);
    handleConfigChange(type, symbols);
  };

  const handleRun = () => {
    if (selectedStrategies.length === 0) {
      alert('Please select at least one strategy to run');
      return;
    }

    // Create config overrides from local state
    const configOverrides = {
      data_mode: localConfig.data_mode,
      wheel_symbols: localConfig.wheel_symbols,
      rotator_symbols: localConfig.rotator_symbols,
      simulation: localConfig.simulation
    };

    onRunStrategies(selectedStrategies, configOverrides);
  };

  const getStatusIcon = () => {
    if (isLoading) return <Clock className="h-4 w-4 animate-spin" />;
    if (error) return <AlertCircle className="h-4 w-4 text-red-500" />;
    if (status.includes('Completed')) return <CheckCircle className="h-4 w-4 text-green-500" />;
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Strategy Selection */}
      <div className="dashboard-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Strategy Selection</h3>
        
        <div className="space-y-3">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={selectedStrategies.includes('wheel')}
              onChange={() => handleStrategyToggle('wheel')}
              className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
            <div>
              <span className="font-medium text-gray-900">Options Wheel Strategy</span>
              <p className="text-sm text-gray-600">Cash-secured puts and covered calls on ETFs</p>
            </div>
          </label>

          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={selectedStrategies.includes('rotator')}
              onChange={() => handleStrategyToggle('rotator')}
              className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
            <div>
              <span className="font-medium text-gray-900">Crypto Rotator Strategy</span>
              <p className="text-sm text-gray-600">Momentum-based rotation between cryptocurrencies</p>
            </div>
          </label>
        </div>
      </div>

      {/* Configuration */}
      <div className="dashboard-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h3>
        
        <div className="space-y-4">
          {/* Data Mode */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Mode
            </label>
            <select
              value={localConfig.data_mode}
              onChange={(e) => handleConfigChange('data_mode', e.target.value)}
              className="select-field"
            >
              <option value="mock">Mock Data (Simulation)</option>
              <option value="live">Live Market Data</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Live data uses real market feeds but still runs in simulation mode
            </p>
          </div>

          {/* Wheel Symbols */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Wheel Strategy Symbols
            </label>
            <input
              type="text"
              value={localConfig.wheel_symbols.join(', ')}
              onChange={(e) => handleSymbolsChange('wheel_symbols', e.target.value)}
              placeholder="SPY, QQQ, IWM"
              className="input-field"
            />
            <p className="text-xs text-gray-500 mt-1">
              Comma-separated list of ETF symbols
            </p>
          </div>

          {/* Rotator Symbols */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Crypto Rotator Symbols
            </label>
            <input
              type="text"
              value={localConfig.rotator_symbols.join(', ')}
              onChange={(e) => handleSymbolsChange('rotator_symbols', e.target.value)}
              placeholder="BTC, ETH, SOL"
              className="input-field"
            />
            <p className="text-xs text-gray-500 mt-1">
              Comma-separated list of cryptocurrency symbols
            </p>
          </div>

          {/* Simulation Weeks */}
          {localConfig.simulation && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Simulation Weeks
              </label>
              <input
                type="number"
                min="1"
                max="52"
                value={localConfig.simulation.weeks_to_simulate}
                onChange={(e) => handleConfigChange('weeks_to_simulate', parseInt(e.target.value), 'simulation')}
                className="input-field"
              />
              <p className="text-xs text-gray-500 mt-1">
                Number of weeks to simulate (1-52)
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Run Controls */}
      <div className="dashboard-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Execution</h3>
        
        {/* Status Display */}
        <div className="mb-4">
          <div className="flex items-center space-x-2 text-sm">
            {getStatusIcon()}
            <span className={`${error ? 'text-red-600' : 'text-gray-600'}`}>
              Status: {error || status}
            </span>
          </div>
          {error && (
            <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
        </div>

        {/* Run Button */}
        <button
          onClick={handleRun}
          disabled={isLoading || selectedStrategies.length === 0}
          className="btn-primary w-full flex items-center justify-center space-x-2"
        >
          <Play className="h-4 w-4" />
          <span>
            {isLoading 
              ? 'Running Strategies...' 
              : `Run ${selectedStrategies.length} Strategy${selectedStrategies.length !== 1 ? 'ies' : ''}`
            }
          </span>
        </button>

        <p className="text-xs text-gray-500 mt-2 text-center">
          ⚠️ Simulation mode only - no real trades will be executed
        </p>
      </div>
    </div>
  );
};

export default ControlsPanel;