import React, { useState } from 'react';
import { TrendingUp, Calendar, BarChart, AlertTriangle, Target, Clock } from 'lucide-react';

interface BacktestPanelProps {
  onRunBacktest: (params: BacktestParams) => void;
  isLoading: boolean;
  error: string | null;
}

interface BacktestParams {
  strategies: string[];
  start_date: string;
  end_date: string;
  portfolio_value: number;
  risk_tolerance: string;
}

interface RecommendationData {
  recommendations: Array<{
    action: string;
    symbol: string;
    confidence: number;
    reasoning: string;
    risk_level: string;
    allocation_percentage: number;
    expected_return: number;
  }>;
  weekly_action_plan: {
    immediate_actions: Array<{ details: string }>;
    risk_alerts: string[];
  };
  market_insights: {
    market_regime: string;
    volatility_environment: string;
    opportunities: string[];
  };
  performance_summary: {
    total_return_ytd: string;
    sharpe_ratio: number;
    max_drawdown: string;
    win_rate: string;
  };
  generated_at: string;
  analysis_period: {
    start_date: string;
    end_date: string;
  };
}

const BacktestPanel: React.FC<BacktestPanelProps & { results?: RecommendationData }> = ({
  onRunBacktest,
  isLoading,
  error,
  results
}) => {
  const [params, setParams] = useState<BacktestParams>({
    strategies: ['wheel', 'rotator'],
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    portfolio_value: 100000,
    risk_tolerance: 'MEDIUM'
  });

  const handleStrategyToggle = (strategy: string) => {
    setParams(prev => ({
      ...prev,
      strategies: prev.strategies.includes(strategy)
        ? prev.strategies.filter(s => s !== strategy)
        : [...prev.strategies, strategy]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (params.strategies.length === 0) {
      alert('Please select at least one strategy');
      return;
    }
    onRunBacktest(params);
  };

  const formatConfidence = (confidence: number) => {
    return `${Math.round(confidence * 100)}%`;
  };

  const getActionIcon = (action: string) => {
    switch (action.toLowerCase()) {
      case 'buy': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'sell': return <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />;
      case 'hold': return <Target className="h-4 w-4 text-blue-500" />;
      case 'reduce': return <BarChart className="h-4 w-4 text-orange-500" />;
      default: return <BarChart className="h-4 w-4 text-gray-500" />;
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low': return 'text-green-600 bg-green-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'high': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="space-y-6">
      {/* Backtesting Configuration */}
      <div className="dashboard-card">
        <div className="flex items-center space-x-2 mb-4">
          <BarChart className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Historical Backtesting & Recommendations</h3>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Strategy Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Strategies to Analyze
            </label>
            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={params.strategies.includes('wheel')}
                  onChange={() => handleStrategyToggle('wheel')}
                  className="h-4 w-4 text-blue-600 rounded border-gray-300"
                />
                <span className="text-sm">Options Wheel Strategy</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={params.strategies.includes('rotator')}
                  onChange={() => handleStrategyToggle('rotator')}
                  className="h-4 w-4 text-blue-600 rounded border-gray-300"
                />
                <span className="text-sm">Crypto Rotator Strategy</span>
              </label>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="h-4 w-4 inline mr-1" />
                Start Date
              </label>
              <input
                type="date"
                value={params.start_date}
                onChange={(e) => setParams(prev => ({ ...prev, start_date: e.target.value }))}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="h-4 w-4 inline mr-1" />
                End Date
              </label>
              <input
                type="date"
                value={params.end_date}
                onChange={(e) => setParams(prev => ({ ...prev, end_date: e.target.value }))}
                className="input-field"
                required
              />
            </div>

            {/* Portfolio Value */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Portfolio Value ($)
              </label>
              <input
                type="number"
                min="1000"
                step="1000"
                value={params.portfolio_value}
                onChange={(e) => setParams(prev => ({ ...prev, portfolio_value: parseInt(e.target.value) }))}
                className="input-field"
                required
              />
            </div>

            {/* Risk Tolerance */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Risk Tolerance
              </label>
              <select
                value={params.risk_tolerance}
                onChange={(e) => setParams(prev => ({ ...prev, risk_tolerance: e.target.value }))}
                className="select-field"
              >
                <option value="LOW">Conservative</option>
                <option value="MEDIUM">Moderate</option>
                <option value="HIGH">Aggressive</option>
              </select>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading || params.strategies.length === 0}
            className="btn-primary w-full flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <Clock className="h-4 w-4 animate-spin" />
                <span>Analyzing Historical Data...</span>
              </>
            ) : (
              <>
                <BarChart className="h-4 w-4" />
                <span>Generate Trading Recommendations</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Results Display */}
      {results && (
        <div className="space-y-6">
          {/* Performance Summary */}
          <div className="dashboard-card">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Performance Summary</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{results.performance_summary.total_return_ytd}</div>
                <div className="text-sm text-gray-600">Total Return</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{results.performance_summary.sharpe_ratio}</div>
                <div className="text-sm text-gray-600">Sharpe Ratio</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{results.performance_summary.max_drawdown}</div>
                <div className="text-sm text-gray-600">Max Drawdown</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{results.performance_summary.win_rate}</div>
                <div className="text-sm text-gray-600">Win Rate</div>
              </div>
            </div>
          </div>

          {/* Trading Recommendations */}
          <div className="dashboard-card">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Trading Recommendations</h4>
            <div className="space-y-3">
              {results.recommendations.map((rec, index) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      {getActionIcon(rec.action)}
                      <div>
                        <div className="font-semibold text-gray-900">
                          {rec.action} {rec.symbol}
                        </div>
                        <div className="text-sm text-gray-600">{rec.reasoning}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {formatConfidence(rec.confidence)} confidence
                      </div>
                      <div className={`text-xs px-2 py-1 rounded ${getRiskColor(rec.risk_level)}`}>
                        {rec.risk_level} risk
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 flex justify-between text-sm text-gray-600">
                    <span>Target allocation: {rec.allocation_percentage.toFixed(1)}%</span>
                    <span>Expected return: {rec.expected_return > 0 ? '+' : ''}{rec.expected_return.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Weekly Action Plan */}
          <div className="dashboard-card">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Weekly Action Plan</h4>
            
            {results.weekly_action_plan.immediate_actions.length > 0 && (
              <div className="mb-4">
                <h5 className="font-medium text-gray-900 mb-2">Immediate Actions</h5>
                <ul className="space-y-2">
                  {results.weekly_action_plan.immediate_actions.map((action, index) => (
                    <li key={index} className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-sm text-gray-700">{action.details}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {results.weekly_action_plan.risk_alerts.length > 0 && (
              <div>
                <h5 className="font-medium text-gray-900 mb-2 flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-orange-500" />
                  <span>Risk Alerts</span>
                </h5>
                <ul className="space-y-2">
                  {results.weekly_action_plan.risk_alerts.map((alert, index) => (
                    <li key={index} className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                      <span className="text-sm text-gray-700">{alert}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Market Insights */}
          <div className="dashboard-card">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Market Insights</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm font-medium text-gray-700">Market Regime</div>
                <div className="text-lg font-semibold text-gray-900">{results.market_insights.market_regime}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700">Volatility Environment</div>
                <div className="text-lg font-semibold text-gray-900">{results.market_insights.volatility_environment}</div>
              </div>
            </div>
            
            <div className="mt-4">
              <div className="text-sm font-medium text-gray-700 mb-2">Key Opportunities</div>
              <ul className="space-y-1">
                {results.market_insights.opportunities.map((opp, index) => (
                  <li key={index} className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-gray-700">{opp}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-4 text-xs text-gray-500">
              Analysis generated: {new Date(results.generated_at).toLocaleString()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BacktestPanel;