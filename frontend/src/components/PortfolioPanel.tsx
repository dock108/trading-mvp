import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Edit3, 
  Trash2, 
  Save, 
  X, 
  DollarSign, 
  TrendingUp, 
  Settings,
  Upload,
  Download,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';

interface Position {
  id: string;
  symbol: string;
  asset_type: 'stock' | 'etf' | 'crypto';
  quantity: number;
  avg_cost: number;
  current_price?: number;
  market_value?: number;
  unrealized_pnl?: number;
  notes?: string;
}

interface PortfolioSettings {
  initial_capital: number;
  cash_balance: number;
  risk_tolerance: 'LOW' | 'MEDIUM' | 'HIGH';
  rebalance_frequency: 'weekly' | 'monthly' | 'quarterly';
  data_mode: 'live' | 'mock';
}

const PortfolioPanel: React.FC = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [settings, setSettings] = useState<PortfolioSettings>({
    initial_capital: 100000,
    cash_balance: 50000,
    risk_tolerance: 'MEDIUM',
    rebalance_frequency: 'weekly',
    data_mode: 'live'
  });
  const [editingPosition, setEditingPosition] = useState<Position | null>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadPortfolioData();
  }, []);

  const loadPortfolioData = async () => {
    setIsLoading(true);
    try {
      // Load existing positions from API
      const positionsResponse = await axios.get('/api/recommendations/current-positions');
      if (positionsResponse.data?.positions) {
        const apiPositions: Position[] = positionsResponse.data.positions.map((pos: any, index: number) => ({
          id: `pos_${index}`,
          symbol: pos.symbol,
          asset_type: pos.symbol.length === 3 ? 'etf' : 'crypto',
          quantity: pos.quantity,
          avg_cost: pos.avg_cost,
          current_price: pos.current_price,
          market_value: pos.quantity * pos.current_price,
          unrealized_pnl: pos.unrealized_pnl,
          notes: pos.recommendation
        }));
        setPositions(apiPositions);
      }

      // Load settings from config
      const configResponse = await axios.get('/api/config');
      if (configResponse.data) {
        setSettings({
          initial_capital: configResponse.data.initial_capital || 100000,
          cash_balance: positionsResponse.data?.cash_available || 50000,
          risk_tolerance: 'MEDIUM',
          rebalance_frequency: 'weekly',
          data_mode: configResponse.data.data_mode || 'live'
        });
      }
    } catch (err) {
      console.error('Failed to load portfolio data:', err);
      setError('Failed to load portfolio data');
    } finally {
      setIsLoading(false);
    }
  };

  const savePortfolioData = async () => {
    setIsSaving(true);
    setError(null);
    try {
      // Save positions and settings
      const portfolioData = {
        positions,
        settings,
        updated_at: new Date().toISOString()
      };

      // For now, save to config - in a real app this would be a dedicated portfolio API
      await axios.put('/api/config', {
        initial_capital: settings.initial_capital,
        data_mode: settings.data_mode,
        portfolio: portfolioData
      });

      alert('Portfolio saved successfully!');
    } catch (err) {
      console.error('Failed to save portfolio:', err);
      setError('Failed to save portfolio');
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddPosition = () => {
    const newPosition: Position = {
      id: `new_${Date.now()}`,
      symbol: '',
      asset_type: 'stock',
      quantity: 0,
      avg_cost: 0,
      notes: ''
    };
    setEditingPosition(newPosition);
    setIsAddingNew(true);
  };

  const handleEditPosition = (position: Position) => {
    setEditingPosition({ ...position });
    setIsAddingNew(false);
  };

  const handleSavePosition = () => {
    if (!editingPosition) return;

    if (!editingPosition.symbol || editingPosition.quantity <= 0 || editingPosition.avg_cost <= 0) {
      alert('Please fill in all required fields');
      return;
    }

    if (isAddingNew) {
      setPositions([...positions, editingPosition]);
    } else {
      setPositions(positions.map(pos => 
        pos.id === editingPosition.id ? editingPosition : pos
      ));
    }

    setEditingPosition(null);
    setIsAddingNew(false);
  };

  const handleDeletePosition = (id: string) => {
    if (confirm('Are you sure you want to delete this position?')) {
      setPositions(positions.filter(pos => pos.id !== id));
    }
  };

  const handleCancelEdit = () => {
    setEditingPosition(null);
    setIsAddingNew(false);
  };

  const updatePositionField = (field: keyof Position, value: any) => {
    if (!editingPosition) return;
    setEditingPosition({
      ...editingPosition,
      [field]: value
    });
  };

  const calculateTotalValue = () => {
    const positionsValue = positions.reduce((total, pos) => {
      return total + (pos.market_value || pos.quantity * pos.avg_cost);
    }, 0);
    return positionsValue + settings.cash_balance;
  };

  const calculateTotalPnL = () => {
    return positions.reduce((total, pos) => {
      const currentValue = pos.market_value || pos.quantity * pos.avg_cost;
      const costBasis = pos.quantity * pos.avg_cost;
      return total + (currentValue - costBasis);
    }, 0);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const getAssetTypeColor = (type: string) => {
    switch (type) {
      case 'stock': return 'bg-blue-100 text-blue-800';
      case 'etf': return 'bg-green-100 text-green-800';
      case 'crypto': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Portfolio Management</h2>
        <div className="flex space-x-3">
          <button
            onClick={loadPortfolioData}
            disabled={isLoading}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={savePortfolioData}
            disabled={isSaving}
            className="btn-primary flex items-center space-x-2"
          >
            <Save className="h-4 w-4" />
            <span>{isSaving ? 'Saving...' : 'Save Portfolio'}</span>
          </button>
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="dashboard-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{formatCurrency(calculateTotalValue())}</div>
            <div className="text-sm text-gray-600">Total Value</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{formatCurrency(settings.cash_balance)}</div>
            <div className="text-sm text-gray-600">Cash Balance</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${calculateTotalPnL() >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(calculateTotalPnL())}
            </div>
            <div className="text-sm text-gray-600">Unrealized P&L</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{positions.length}</div>
            <div className="text-sm text-gray-600">Positions</div>
          </div>
        </div>
      </div>

      {/* Portfolio Settings */}
      <div className="dashboard-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <Settings className="h-5 w-5" />
          <span>Portfolio Settings</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Initial Capital
            </label>
            <input
              type="number"
              value={settings.initial_capital}
              onChange={(e) => setSettings({...settings, initial_capital: parseFloat(e.target.value) || 0})}
              className="input-field"
              min="0"
              step="1000"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Cash Balance
            </label>
            <input
              type="number"
              value={settings.cash_balance}
              onChange={(e) => setSettings({...settings, cash_balance: parseFloat(e.target.value) || 0})}
              className="input-field"
              min="0"
              step="100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Risk Tolerance
            </label>
            <select
              value={settings.risk_tolerance}
              onChange={(e) => setSettings({...settings, risk_tolerance: e.target.value as any})}
              className="select-field"
            >
              <option value="LOW">Conservative</option>
              <option value="MEDIUM">Moderate</option>
              <option value="HIGH">Aggressive</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Mode
            </label>
            <select
              value={settings.data_mode}
              onChange={(e) => setSettings({...settings, data_mode: e.target.value as any})}
              className="select-field"
            >
              <option value="live">Live Market Data</option>
              <option value="mock">Mock Data</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="dashboard-card border-red-200 bg-red-50">
          <div className="text-red-600 flex items-center space-x-2">
            <X className="h-5 w-5" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Positions Table */}
      <div className="dashboard-card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Current Positions</h3>
          <button
            onClick={handleAddPosition}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Add Position</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Market Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {positions.map((position) => (
                <tr key={position.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{position.symbol}</div>
                    {position.notes && (
                      <div className="text-sm text-gray-500">{position.notes}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getAssetTypeColor(position.asset_type)}`}>
                      {position.asset_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                    {position.quantity.toLocaleString(undefined, { maximumFractionDigits: 4 })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                    {formatCurrency(position.avg_cost)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                    {position.current_price ? formatCurrency(position.current_price) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                    {formatCurrency(position.market_value || position.quantity * position.avg_cost)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {position.unrealized_pnl !== undefined ? (
                      <span className={position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(position.unrealized_pnl)}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEditPosition(position)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Edit3 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeletePosition(position.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {positions.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                    <div className="flex flex-col items-center">
                      <DollarSign className="h-8 w-8 text-gray-400 mb-2" />
                      <div>No positions yet</div>
                      <div className="text-sm">Click "Add Position" to get started</div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Position Modal */}
      {editingPosition && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {isAddingNew ? 'Add New Position' : 'Edit Position'}
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Symbol *
                </label>
                <input
                  type="text"
                  value={editingPosition.symbol}
                  onChange={(e) => updatePositionField('symbol', e.target.value.toUpperCase())}
                  className="input-field"
                  placeholder="e.g., AAPL, BTC, SPY"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Asset Type
                </label>
                <select
                  value={editingPosition.asset_type}
                  onChange={(e) => updatePositionField('asset_type', e.target.value)}
                  className="select-field"
                >
                  <option value="stock">Stock</option>
                  <option value="etf">ETF</option>
                  <option value="crypto">Cryptocurrency</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quantity *
                </label>
                <input
                  type="number"
                  value={editingPosition.quantity}
                  onChange={(e) => updatePositionField('quantity', parseFloat(e.target.value) || 0)}
                  className="input-field"
                  min="0"
                  step="0.0001"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Average Cost *
                </label>
                <input
                  type="number"
                  value={editingPosition.avg_cost}
                  onChange={(e) => updatePositionField('avg_cost', parseFloat(e.target.value) || 0)}
                  className="input-field"
                  min="0"
                  step="0.01"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  value={editingPosition.notes || ''}
                  onChange={(e) => updatePositionField('notes', e.target.value)}
                  className="input-field"
                  rows={2}
                  placeholder="Optional notes about this position"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={handleCancelEdit}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleSavePosition}
                className="btn-primary"
              >
                {isAddingNew ? 'Add Position' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioPanel;