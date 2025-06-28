import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  DollarSign, 
  AlertTriangle, 
  CheckCircle, 
  Calendar,
  RefreshCw,
  Eye
} from 'lucide-react';
import axios from 'axios';

interface Position {
  symbol: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  unrealized_pnl: number;
  allocation: number;
  recommendation: string;
}

interface PortfolioData {
  positions: Position[];
  total_value: number;
  unrealized_pnl: number;
  cash_available: number;
}

interface Alert {
  type: string;
  severity: string;
  message: string;
  timestamp: string;
}

interface MarketAlerts {
  alerts: Alert[];
  upcoming_events: string[];
}

interface Recommendation {
  action: string;
  symbol: string;
  confidence: number;
  reasoning: string;
  risk_level: string;
  allocation_percentage: number;
  expected_return: number;
  quantity?: number;
  current_price?: number;
}

interface ActionItem {
  details: string;
}

interface WeeklyPlan {
  immediate_actions: ActionItem[];
  risk_alerts: string[];
}

interface MarketInsights {
  market_regime: string;
  volatility_environment: string;
  opportunities: string[];
}

interface RecommendationsData {
  recommendations: Recommendation[];
  weekly_action_plan: WeeklyPlan;
  market_insights: MarketInsights;
  performance_summary: {
    total_return_ytd: string;
    sharpe_ratio: number;
    max_drawdown: string;
    win_rate: string;
  };
  generated_at: string;
}

const RecommendationsPanel: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [alerts, setAlerts] = useState<MarketAlerts | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    await Promise.all([
      loadPortfolio(),
      loadAlerts()
    ]);
  };

  const loadPortfolio = async () => {
    try {
      const response = await axios.get('/api/recommendations/current-positions');
      setPortfolio(response.data);
    } catch (err) {
      console.error('Failed to load portfolio:', err);
    }
  };

  const loadAlerts = async () => {
    try {
      const response = await axios.get('/api/recommendations/market-alerts');
      setAlerts(response.data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    }
  };

  const generateRecommendations = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/recommendations/analyze', {
        strategies: ['wheel', 'rotator'],
        portfolio_value: portfolio?.total_value || 100000,
        risk_tolerance: 'MEDIUM'
      });
      
      setRecommendations(response.data);
      setLastUpdate(new Date());
    } catch (err: any) {
      console.error('Failed to generate recommendations:', err);
      setError(err.response?.data?.detail || 'Failed to generate recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  const getActionIcon = (action: string) => {
    switch (action.toLowerCase()) {
      case 'buy': return <TrendingUp className="h-5 w-5 text-green-500" />;
      case 'sell': return <TrendingDown className="h-5 w-5 text-red-500" />;
      case 'hold': return <Target className="h-5 w-5 text-blue-500" />;
      case 'reduce': return <TrendingDown className="h-5 w-5 text-orange-500" />;
      default: return <Target className="h-5 w-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Header with Refresh */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Investment Recommendations</h2>
        <button
          onClick={generateRecommendations}
          disabled={isLoading}
          className="btn-primary flex items-center space-x-2"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'Analyzing...' : 'Get Recommendations'}</span>
        </button>
      </div>

      {/* Current Portfolio Overview */}
      {portfolio && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <DollarSign className="h-5 w-5" />
            <span>Current Portfolio</span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{formatCurrency(portfolio.total_value)}</div>
              <div className="text-sm text-gray-600">Total Value</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${portfolio.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(portfolio.unrealized_pnl)}
              </div>
              <div className="text-sm text-gray-600">Unrealized P&L</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{formatCurrency(portfolio.cash_available)}</div>
              <div className="text-sm text-gray-600">Cash Available</div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Current Positions</h4>
            {portfolio.positions?.map((position, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium text-gray-900">{position.symbol}</div>
                  <div className="text-sm text-gray-600">
                    {position.quantity} shares @ {formatCurrency(position.current_price)}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-medium ${position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(position.unrealized_pnl)}
                  </div>
                  <div className="text-sm text-gray-600">{position.allocation.toFixed(1)}% allocation</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Market Alerts */}
      {alerts && (
        <div className="dashboard-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5" />
            <span>Market Alerts</span>
          </h3>
          
          <div className="space-y-3">
            {alerts.alerts?.map((alert, index) => (
              <div key={index} className={`p-3 border rounded-lg ${getSeverityColor(alert.severity)}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">{alert.type}</div>
                    <div className="text-sm mt-1">{alert.message}</div>
                  </div>
                  <div className="text-xs opacity-75">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {alerts.upcoming_events?.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium text-gray-900 mb-2 flex items-center space-x-2">
                <Calendar className="h-4 w-4" />
                <span>Upcoming Events</span>
              </h4>
              <ul className="space-y-1">
                {alerts.upcoming_events?.map((event, index) => (
                  <li key={index} className="text-sm text-gray-600 flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>{event}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="dashboard-card border-red-200 bg-red-50">
          <div className="flex items-center space-x-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <span className="font-medium">Error</span>
          </div>
          <p className="text-sm text-red-600 mt-2">{error}</p>
        </div>
      )}

      {/* Trading Recommendations */}
      {recommendations && (
        <div className="space-y-6">
          {/* Performance Summary */}
          <div className="dashboard-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Analysis</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-xl font-bold text-green-600">{recommendations.performance_summary.total_return_ytd}</div>
                <div className="text-sm text-gray-600">YTD Return</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-blue-600">{recommendations.performance_summary.sharpe_ratio}</div>
                <div className="text-sm text-gray-600">Sharpe Ratio</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-red-600">{recommendations.performance_summary.max_drawdown}</div>
                <div className="text-sm text-gray-600">Max Drawdown</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-purple-600">{recommendations.performance_summary.win_rate}</div>
                <div className="text-sm text-gray-600">Win Rate</div>
              </div>
            </div>
          </div>

          {/* Actionable Recommendations */}
          <div className="dashboard-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <Target className="h-5 w-5" />
              <span>What To Do This Week</span>
            </h3>
            <div className="space-y-4">
              {recommendations.recommendations.map((rec, index) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg bg-gradient-to-r from-blue-50 to-white">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      {getActionIcon(rec.action)}
                      <div>
                        <div className="font-semibold text-gray-900 text-lg">
                          {rec.action.toUpperCase()} {rec.symbol}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">{rec.reasoning}</div>
                        {rec.quantity && rec.current_price && (
                          <div className="text-sm font-medium text-blue-600 mt-2">
                            Suggested: {rec.quantity.toFixed(4)} shares at ~{formatCurrency(rec.current_price)}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {(rec.confidence * 100).toFixed(0)}% confidence
                      </div>
                      <div className={`text-xs px-2 py-1 rounded mt-1 ${
                        rec.risk_level.toLowerCase() === 'low' ? 'bg-green-100 text-green-700' :
                        rec.risk_level.toLowerCase() === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {rec.risk_level} risk
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 flex justify-between text-sm">
                    <span className="text-gray-600">Target allocation: {rec.allocation_percentage.toFixed(1)}%</span>
                    <span className={`font-medium ${rec.expected_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      Expected return: {formatPercentage(rec.expected_return)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Weekly Action Plan */}
          <div className="dashboard-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <CheckCircle className="h-5 w-5" />
              <span>Weekly Action Plan</span>
            </h3>
            
            {recommendations.weekly_action_plan.immediate_actions.length > 0 && (
              <div className="mb-4">
                <h4 className="font-medium text-gray-900 mb-3">Immediate Actions Needed</h4>
                <div className="space-y-2">
                  {recommendations.weekly_action_plan.immediate_actions.map((action, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                      <CheckCircle className="h-5 w-5 text-blue-500 mt-0.5" />
                      <span className="text-gray-700">{action.details}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {recommendations.weekly_action_plan.risk_alerts.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-orange-500" />
                  <span>Risk Alerts</span>
                </h4>
                <div className="space-y-2">
                  {recommendations.weekly_action_plan.risk_alerts.map((alert, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-orange-50 rounded-lg">
                      <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5" />
                      <span className="text-gray-700">{alert}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Market Insights */}
          <div className="dashboard-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <Eye className="h-5 w-5" />
              <span>Market Insights</span>
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-sm font-medium text-gray-700">Market Regime</div>
                <div className="text-lg font-semibold text-gray-900">{recommendations.market_insights.market_regime}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700">Volatility Environment</div>
                <div className="text-lg font-semibold text-gray-900">{recommendations.market_insights.volatility_environment}</div>
              </div>
            </div>

            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">Key Opportunities</div>
              <div className="space-y-2">
                {recommendations.market_insights.opportunities.map((opportunity, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                    <span className="text-gray-700">{opportunity}</span>
                  </div>
                ))}
              </div>
            </div>

            {lastUpdate && (
              <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-500">
                Last updated: {lastUpdate.toLocaleString()}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Call to Action when no recommendations */}
      {!recommendations && !isLoading && (
        <div className="dashboard-card text-center py-8">
          <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Get Your Trading Recommendations</h3>
          <p className="text-gray-600 mb-4">
            Click "Get Recommendations" to analyze your portfolio and receive specific investment guidance for this week.
          </p>
          <button
            onClick={generateRecommendations}
            className="btn-primary"
          >
            Start Analysis
          </button>
        </div>
      )}
    </div>
  );
};

export default RecommendationsPanel;