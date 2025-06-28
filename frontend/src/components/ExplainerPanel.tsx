import React from 'react';
import { 
  Target, 
  BarChart, 
  Play, 
  TrendingUp, 
  Clock, 
  AlertTriangle, 
  CheckCircle,
  DollarSign,
  Calendar,
  Briefcase
} from 'lucide-react';

const ExplainerPanel: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Trading Dashboard Guide</h2>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          Understanding the three different tools in your trading dashboard and when to use each one.
        </p>
      </div>

      {/* Tab Explanations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
        
        {/* Portfolio Manager */}
        <div className="dashboard-card border-green-200 bg-green-50">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-green-500 rounded-lg">
              <Briefcase className="h-6 w-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900">Portfolio Manager</h3>
          </div>
          
          <div className="space-y-4">
            <div className="bg-white p-4 rounded-lg border border-green-200">
              <h4 className="font-semibold text-gray-900 mb-2">💼 What It Does</h4>
              <p className="text-sm text-gray-700">
                Manage your investment positions manually - add, edit, and track all your holdings in one place.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-green-200">
              <h4 className="font-semibold text-gray-900 mb-2">📝 Features</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• Add/edit positions manually</li>
                <li>• Track cash balance and settings</li>
                <li>• Calculate portfolio value and P&L</li>
                <li>• Save configurations easily</li>
              </ul>
            </div>

            <div className="bg-white p-4 rounded-lg border border-green-200">
              <h4 className="font-semibold text-gray-900 mb-2">💡 Example Use</h4>
              <div className="text-sm space-y-1">
                <div className="font-medium">Add Position:</div>
                <div className="text-gray-600">• Symbol: AAPL</div>
                <div className="text-gray-600">• Quantity: 100 shares</div>
                <div className="text-gray-600">• Avg Cost: $150.00</div>
              </div>
            </div>

            <div className="bg-blue-100 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">Start Here First</span>
              </div>
            </div>
          </div>
        </div>

        {/* Investment Recommendations */}
        <div className="dashboard-card border-blue-200 bg-blue-50">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Target className="h-6 w-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900">Investment Recommendations</h3>
          </div>
          
          <div className="space-y-4">
            <div className="bg-white p-4 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-gray-900 mb-2">🎯 What It Does</h4>
              <p className="text-sm text-gray-700">
                Analyzes your current portfolio and market conditions to give you specific trading recommendations for THIS week.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-gray-900 mb-2">📊 Data Used</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• 365 days of real historical market data</li>
                <li>• Your current portfolio positions</li>
                <li>• Live market prices and volatility</li>
              </ul>
            </div>

            <div className="bg-white p-4 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-gray-900 mb-2">💡 Example Output</h4>
              <div className="text-sm space-y-1">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span className="font-medium">BUY 0.28 shares of BTC</span>
                </div>
                <div className="text-gray-600">Confidence: 75% | Risk: LOW</div>
                <div className="text-gray-600">Reason: Top momentum 6.4% (1w)</div>
              </div>
            </div>

            <div className="bg-green-100 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-800">Use This For Real Trading</span>
              </div>
            </div>
          </div>
        </div>

        {/* Historical Analysis */}
        <div className="dashboard-card border-purple-200 bg-purple-50">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-purple-500 rounded-lg">
              <BarChart className="h-6 w-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900">Historical Analysis</h3>
          </div>
          
          <div className="space-y-4">
            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h4 className="font-semibold text-gray-900 mb-2">📈 What It Does</h4>
              <p className="text-sm text-gray-700">
                Runs comprehensive backtests on historical data to analyze strategy performance over custom time periods.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h4 className="font-semibold text-gray-900 mb-2">📅 Data Used</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• Custom date ranges (e.g., 2024-01-01 to 2024-12-31)</li>
                <li>• Real historical price data</li>
                <li>• Performance metrics (Sharpe ratio, drawdown)</li>
              </ul>
            </div>

            <div className="bg-white p-4 rounded-lg border border-purple-200">
              <h4 className="font-semibold text-gray-900 mb-2">📊 Example Output</h4>
              <div className="text-sm space-y-1">
                <div className="font-medium">Performance Summary:</div>
                <div className="text-gray-600">• Total Return: +8.5%</div>
                <div className="text-gray-600">• Sharpe Ratio: 1.2</div>
                <div className="text-gray-600">• Max Drawdown: -5.2%</div>
              </div>
            </div>

            <div className="bg-blue-100 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <BarChart className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">Use This For Strategy Research</span>
              </div>
            </div>
          </div>
        </div>

        {/* Strategy Testing */}
        <div className="dashboard-card border-orange-200 bg-orange-50">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-orange-500 rounded-lg">
              <Play className="h-6 w-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900">Strategy Testing</h3>
          </div>
          
          <div className="space-y-4">
            <div className="bg-white p-4 rounded-lg border border-orange-200">
              <h4 className="font-semibold text-gray-900 mb-2">🧪 What It Does</h4>
              <p className="text-sm text-gray-700">
                Runs simulated "what if" scenarios using current prices as a starting point for 8 weeks of fictional trading.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-orange-200">
              <h4 className="font-semibold text-gray-900 mb-2">🎲 Data Used</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• Current live prices (starting point)</li>
                <li>• Simulated price movements (8 weeks)</li>
                <li>• Fictional scenarios, not real history</li>
              </ul>
            </div>

            <div className="bg-white p-4 rounded-lg border border-orange-200">
              <h4 className="font-semibold text-gray-900 mb-2">📋 Example Output</h4>
              <div className="text-sm space-y-1">
                <div className="font-medium">Simulation Results:</div>
                <div className="text-gray-600">• Week 0: SELL_PUT IWM +$3.96</div>
                <div className="text-gray-600">• Week 2: SELL_PUT IWM +$3.98</div>
                <div className="text-gray-600">• Total Return: 0.03%</div>
              </div>
            </div>

            <div className="bg-yellow-100 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-800">Academic Tool Only</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* When to Use What */}
      <div className="dashboard-card">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">When to Use Each Tool</h3>
        
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900 flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span>For Real Investment Decisions</span>
              </h4>
              <div className="space-y-3">
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="font-medium text-blue-900">Investment Recommendations</div>
                  <div className="text-sm text-blue-700 mt-1">
                    "What should I buy/sell this week with my actual money?"
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900 flex items-center space-x-2">
                <BarChart className="h-5 w-5 text-purple-500" />
                <span>For Research & Analysis</span>
              </h4>
              <div className="space-y-3">
                <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="font-medium text-purple-900">Historical Analysis</div>
                  <div className="text-sm text-purple-700 mt-1">
                    "How did this strategy perform during 2024?"
                  </div>
                </div>
                <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                  <div className="font-medium text-orange-900">Strategy Testing</div>
                  <div className="text-sm text-orange-700 mt-1">
                    "What if I ran this strategy for 8 weeks?"
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Data Sources */}
      <div className="dashboard-card">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Data Sources</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
              <DollarSign className="h-4 w-4 text-green-500" />
              <span>Cryptocurrency Data</span>
            </h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• <strong>Primary:</strong> CoinGecko API</li>
              <li>• <strong>Symbols:</strong> BTC, ETH, SOL</li>
              <li>• <strong>Update Frequency:</strong> Daily historical data</li>
              <li>• <strong>Rate Limit:</strong> 10 calls/minute</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-blue-500" />
              <span>Stock/ETF Data</span>
            </h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• <strong>Primary:</strong> Yahoo Finance</li>
              <li>• <strong>Backup:</strong> Alpha Vantage API</li>
              <li>• <strong>Symbols:</strong> SPY, QQQ, IWM</li>
              <li>• <strong>Rate Limit:</strong> 5 calls/minute</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Quick Start Guide */}
      <div className="dashboard-card bg-gradient-to-r from-green-50 to-blue-50">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">🚀 Quick Start Guide</h3>
        
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
              1
            </div>
            <div>
              <div className="font-medium text-gray-900">Set Up Your Portfolio</div>
              <div className="text-sm text-gray-700">Add your current positions and cash balance in Portfolio Manager</div>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
              2
            </div>
            <div>
              <div className="font-medium text-gray-900">Get Investment Recommendations</div>
              <div className="text-sm text-gray-700">Receive actionable advice based on your actual holdings</div>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
              3
            </div>
            <div>
              <div className="font-medium text-gray-900">Research with Historical Analysis</div>
              <div className="text-sm text-gray-700">Validate strategies using past performance data</div>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
              4
            </div>
            <div>
              <div className="font-medium text-gray-900">Experiment with Strategy Testing</div>
              <div className="text-sm text-gray-700">Run "what if" scenarios for educational purposes</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExplainerPanel;