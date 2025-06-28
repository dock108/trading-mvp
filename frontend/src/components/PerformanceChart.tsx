import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import type { StrategyResult } from '../types';

interface PerformanceChartProps {
  wheelResult?: StrategyResult;
  rotatorResult?: StrategyResult;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({ wheelResult, rotatorResult }) => {
  // Prepare comparison data
  const comparisonData = [];
  
  if (wheelResult && !wheelResult.error) {
    const wheelReturn = wheelResult.summary.final_capital - wheelResult.summary.initial_capital;
    const wheelReturnPct = (wheelReturn / wheelResult.summary.initial_capital) * 100;
    comparisonData.push({
      strategy: 'Options Wheel',
      'Return ($)': wheelReturn,
      'Return (%)': wheelReturnPct,
      trades: wheelResult.summary.total_trades,
      'Initial Capital': wheelResult.summary.initial_capital,
      'Final Capital': wheelResult.summary.final_capital
    });
  }

  if (rotatorResult && !rotatorResult.error) {
    const rotatorReturn = rotatorResult.summary.final_capital - rotatorResult.summary.initial_capital;
    const rotatorReturnPct = (rotatorReturn / rotatorResult.summary.initial_capital) * 100;
    comparisonData.push({
      strategy: 'Crypto Rotator',
      'Return ($)': rotatorReturn,
      'Return (%)': rotatorReturnPct,
      trades: rotatorResult.summary.total_trades,
      'Initial Capital': rotatorResult.summary.initial_capital,
      'Final Capital': rotatorResult.summary.final_capital
    });
  }

  // Prepare action distribution data
  const actionData: { [key: string]: number } = {};
  
  [wheelResult, rotatorResult].forEach(result => {
    if (result && !result.error) {
      result.trades.forEach(trade => {
        const action = trade.action.replace('_', ' ');
        actionData[action] = (actionData[action] || 0) + 1;
      });
    }
  });

  const actionChartData = Object.entries(actionData).map(([action, count]) => ({
    action,
    count
  }));

  const COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444', '#6B7280'];

  const formatCurrency = (value: number) => {
    return value.toLocaleString(undefined, {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  if (comparisonData.length === 0) {
    return (
      <div className="dashboard-card">
        <h4 className="text-md font-medium text-gray-900 mb-4">Performance Charts</h4>
        <div className="text-center py-8">
          <p className="text-gray-500">No data available for charts</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Strategy Performance Comparison */}
      <div className="dashboard-card">
        <h4 className="text-md font-medium text-gray-900 mb-4">Strategy Performance Comparison</h4>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Return Comparison */}
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-3">Returns Comparison</h5>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="strategy" />
                <YAxis />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    name.includes('$') ? formatCurrency(value) : formatPercentage(value),
                    name
                  ]}
                />
                <Bar dataKey="Return (%)" fill="#3B82F6" name="Return %" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Trade Count Comparison */}
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-3">Trade Volume</h5>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="strategy" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="trades" fill="#8B5CF6" name="Number of Trades" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Action Distribution */}
      {actionChartData.length > 0 && (
        <div className="dashboard-card">
          <h4 className="text-md font-medium text-gray-900 mb-4">Trade Action Distribution</h4>
          
          <div className="flex flex-col lg:flex-row items-center">
            <div className="w-full lg:w-1/2">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={actionChartData}
                    dataKey="count"
                    nameKey="action"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#8884d8"
                    label={({ action, count, percent }) => 
                      `${action}: ${(percent * 100).toFixed(1)}%`
                    }
                  >
                    {actionChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="w-full lg:w-1/2 lg:pl-6">
              <div className="space-y-3">
                {actionChartData.map((item, index) => (
                  <div key={item.action} className="flex items-center space-x-3">
                    <div 
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    ></div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{item.action}</div>
                      <div className="text-xs text-gray-600">{item.count} trades</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Summary Statistics */}
      <div className="dashboard-card">
        <h4 className="text-md font-medium text-gray-900 mb-4">Summary Statistics</h4>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Strategy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Initial Capital
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Final Capital
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Return
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trades
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {comparisonData.map((data, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {data.strategy}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(data['Initial Capital'])}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(data['Final Capital'])}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                    data['Return (%)'] >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(data['Return ($)'])} ({formatPercentage(data['Return (%)'])})
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {data.trades}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart;