import React from 'react';
import { BarChart3, TrendingUp, TrendingDown, Clock } from 'lucide-react';
import { LoadingSpinner } from './common';
import type { StrategyResults, ConfigData } from '../types';
import TradesTable from './TradesTable';
import SummaryMetrics from './SummaryMetrics';
import PerformanceChart from './PerformanceChart';

interface ResultsPanelProps {
  results: StrategyResults | null;
  isLoading: boolean;
  config: ConfigData;
}

const ResultsPanel: React.FC<ResultsPanelProps> = ({ results, isLoading, config }) => {
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="dashboard-card">
          <div className="text-center py-12">
            <LoadingSpinner size="lg" className="mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Running Strategies</h3>
            <p className="text-gray-600">
              Executing trading strategies with {config.data_mode} data...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="space-y-6">
        <div className="dashboard-card">
          <div className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Run</h3>
            <p className="text-gray-600">
              Select strategies and click "Run" to see results here.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const { wheel, rotator } = results.results;
  const hasResults = wheel || rotator;

  if (!hasResults) {
    return (
      <div className="space-y-6">
        <div className="dashboard-card">
          <div className="text-center py-12">
            <TrendingDown className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Results</h3>
            <p className="text-gray-600">
              No strategy results were generated. Check the error messages and try again.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Execution Summary */}
      <div className="dashboard-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Execution Summary</h3>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="h-4 w-4" />
            <span>{new Date(results.ran_at).toLocaleString()}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="metric-card">
            <div className="text-2xl font-bold text-blue-600">
              {results.total_trades}
            </div>
            <div className="text-sm text-gray-600">Total Trades</div>
          </div>

          <div className="metric-card">
            <div className="text-2xl font-bold text-green-600">
              {results.combined_summary.total_strategies_run}
            </div>
            <div className="text-sm text-gray-600">Strategies Run</div>
          </div>

          <div className="metric-card">
            <div className={`text-2xl font-bold ${results.combined_summary.combined_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${results.combined_summary.combined_cash_flow.toLocaleString(undefined, { 
                minimumFractionDigits: 2, 
                maximumFractionDigits: 2 
              })}
            </div>
            <div className="text-sm text-gray-600">Net Cash Flow</div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {results.combined_summary.strategies_requested.map(strategy => (
            <span
              key={strategy}
              className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
            >
              {strategy === 'wheel' ? 'Options Wheel' : 'Crypto Rotator'}
            </span>
          ))}
          <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
            {results.combined_summary.data_mode} mode
          </span>
        </div>
      </div>

      {/* Strategy Results */}
      {wheel && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Options Wheel Strategy</h3>
          </div>
          
          <SummaryMetrics 
            result={wheel} 
            strategyName="Wheel"
          />
          
          <TradesTable 
            trades={wheel.trades} 
            title="Wheel Strategy Trades"
          />
        </div>
      )}

      {rotator && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">Crypto Rotator Strategy</h3>
          </div>
          
          <SummaryMetrics 
            result={rotator} 
            strategyName="Rotator"
          />
          
          <TradesTable 
            trades={rotator.trades} 
            title="Crypto Rotator Trades"
          />
        </div>
      )}

      {/* Performance Visualization */}
      {(wheel || rotator) && (
        <PerformanceChart 
          wheelResult={wheel}
          rotatorResult={rotator}
        />
      )}
    </div>
  );
};

export default ResultsPanel;