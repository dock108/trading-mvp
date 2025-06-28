import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ArrowUpDown } from 'lucide-react';
import type { TradeRecord } from '../types';

interface TradesTableProps {
  trades: TradeRecord[];
  title: string;
}

type SortField = 'week' | 'symbol' | 'action' | 'quantity' | 'price' | 'cash_flow' | 'timestamp';
type SortDirection = 'asc' | 'desc';

const TradesTable: React.FC<TradesTableProps> = ({ trades, title }) => {
  const [sortField, setSortField] = useState<SortField>('timestamp');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedTrades = [...trades].sort((a, b) => {
    let aValue, bValue;

    switch (sortField) {
      case 'week':
        aValue = a.week;
        bValue = b.week;
        break;
      case 'symbol':
        aValue = a.symbol;
        bValue = b.symbol;
        break;
      case 'action':
        aValue = a.action;
        bValue = b.action;
        break;
      case 'quantity':
        aValue = a.quantity;
        bValue = b.quantity;
        break;
      case 'price':
        aValue = a.price;
        bValue = b.price;
        break;
      case 'cash_flow':
        aValue = a.cash_flow;
        bValue = b.cash_flow;
        break;
      case 'timestamp':
        aValue = new Date(a.timestamp).getTime();
        bValue = new Date(b.timestamp).getTime();
        break;
      default:
        aValue = a.timestamp;
        bValue = b.timestamp;
    }

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortDirection === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    } else {
      return sortDirection === 'asc' 
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    }
  });

  const formatCurrency = (value: number) => {
    return value.toLocaleString(undefined, {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const formatQuantity = (quantity: number) => {
    return quantity.toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: 4
    });
  };

  const getActionColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'buy_shares':
      case 'buy_crypto':
        return 'text-blue-600 bg-blue-50';
      case 'sell_shares':
      case 'sell_crypto':
        return 'text-green-600 bg-green-50';
      case 'sell_put':
      case 'sell_call':
        return 'text-purple-600 bg-purple-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 text-gray-400" />;
    }
    return sortDirection === 'asc' 
      ? <ChevronUp className="h-4 w-4 text-blue-600" />
      : <ChevronDown className="h-4 w-4 text-blue-600" />;
  };

  if (trades.length === 0) {
    return (
      <div className="dashboard-card">
        <h4 className="text-md font-medium text-gray-900 mb-4">{title}</h4>
        <div className="text-center py-8">
          <p className="text-gray-500">No trades executed</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-card">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-md font-medium text-gray-900">{title}</h4>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">{trades.length} trades</span>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 hover:bg-gray-100 rounded"
          >
            {isCollapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="overflow-x-auto">
          <table className="trades-table">
            <thead>
              <tr>
                <th 
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('week')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Week</span>
                    {getSortIcon('week')}
                  </div>
                </th>
                <th 
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('symbol')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Symbol</span>
                    {getSortIcon('symbol')}
                  </div>
                </th>
                <th 
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('action')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Action</span>
                    {getSortIcon('action')}
                  </div>
                </th>
                <th 
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('quantity')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Quantity</span>
                    {getSortIcon('quantity')}
                  </div>
                </th>
                <th 
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('price')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Price</span>
                    {getSortIcon('price')}
                  </div>
                </th>
                <th 
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('cash_flow')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Cash Flow</span>
                    {getSortIcon('cash_flow')}
                  </div>
                </th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sortedTrades.map((trade, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="font-medium">{trade.week}</td>
                  <td className="font-mono text-sm">{trade.symbol}</td>
                  <td>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getActionColor(trade.action)}`}>
                      {trade.action.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="text-right font-mono">
                    {formatQuantity(trade.quantity)}
                  </td>
                  <td className="text-right font-mono">
                    {formatCurrency(trade.price)}
                  </td>
                  <td className={`text-right font-mono font-semibold ${
                    trade.cash_flow >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(trade.cash_flow)}
                  </td>
                  <td className="text-sm text-gray-600 max-w-xs truncate" title={trade.notes}>
                    {trade.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TradesTable;