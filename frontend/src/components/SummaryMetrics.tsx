import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, Clock, BarChart3 } from 'lucide-react';
import type { StrategyResult } from '../types';

interface SummaryMetricsProps {
  result: StrategyResult;
  strategyName: string;
}

const SummaryMetrics: React.FC<SummaryMetricsProps> = ({ result, strategyName }) => {
  if (result.error) {
    return (
      <div className="dashboard-card">
        <div className="flex items-center space-x-2 mb-4">
          <TrendingDown className="h-5 w-5 text-red-500" />
          <h4 className="text-md font-medium text-gray-900">{strategyName} Summary</h4>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">Error: {result.error}</p>
        </div>
      </div>
    );
  }

  const { summary } = result;
  
  // Calculate return percentage
  const returnPercentage = summary.initial_capital > 0 
    ? ((summary.final_capital - summary.initial_capital) / summary.initial_capital) * 100
    : 0;

  // Calculate total P&L
  const totalPnL = summary.final_capital - summary.initial_capital;

  const formatCurrency = (value: number) => {
    return value.toLocaleString(undefined, {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    } else {
      return `${(seconds / 60).toFixed(1)}m`;
    }
  };

  return (
    <div className="dashboard-card">
      <div className="flex items-center space-x-2 mb-4">
        <BarChart3 className="h-5 w-5 text-blue-600" />
        <h4 className="text-md font-medium text-gray-900">{strategyName} Performance Summary</h4>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Initial Capital */}
        <div className="metric-card">
          <div className="flex items-center space-x-2 mb-2">
            <DollarSign className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Initial Capital</span>
          </div>
          <div className="text-xl font-bold text-gray-900">
            {formatCurrency(summary.initial_capital)}
          </div>
        </div>

        {/* Final Capital */}
        <div className="metric-card">
          <div className="flex items-center space-x-2 mb-2">
            <DollarSign className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Final Capital</span>
          </div>
          <div className={`text-xl font-bold ${
            summary.final_capital >= summary.initial_capital ? 'text-green-600' : 'text-red-600'
          }`}>
            {formatCurrency(summary.final_capital)}
          </div>
        </div>

        {/* Total P&L */}
        <div className="metric-card">
          <div className="flex items-center space-x-2 mb-2">
            {totalPnL >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
            <span className="text-sm font-medium text-gray-700">Total P&L</span>
          </div>
          <div className={`text-xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(totalPnL)}
          </div>
          <div className={`text-sm ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercentage(returnPercentage)}
          </div>
        </div>

        {/* Total Trades */}
        <div className="metric-card">
          <div className="flex items-center space-x-2 mb-2">
            <BarChart3 className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Total Trades</span>
          </div>
          <div className="text-xl font-bold text-gray-900">
            {summary.total_trades}
          </div>
          <div className="text-sm text-gray-600">
            {formatDuration(summary.execution_time)}
          </div>
        </div>
      </div>

      {/* Additional Metrics */}
      {Object.keys(summary).length > 5 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h5 className="text-sm font-medium text-gray-700 mb-3">Additional Metrics</h5>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {Object.entries(summary).map(([key, value]) => {
              // Skip the main metrics we already displayed
              if (['total_trades', 'initial_capital', 'final_capital', 'total_return', 'execution_time'].includes(key)) {
                return null;
              }

              const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
              
              return (
                <div key={key} className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-600 mb-1">{displayKey}</div>
                  <div className="text-sm font-medium text-gray-900">
                    {typeof value === 'number' 
                      ? (key.includes('rate') || key.includes('percentage') || key.includes('ratio'))
                        ? formatPercentage(value)
                        : value.toLocaleString()
                      : String(value)
                    }
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default SummaryMetrics;