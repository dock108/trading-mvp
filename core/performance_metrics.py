"""
Performance Metrics Calculator

This module provides comprehensive performance analysis for trading strategies including:
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Volatility
- Additional risk and performance metrics
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Calculate comprehensive performance metrics for trading strategies."""
    
    def __init__(self, risk_free_rate: float = 0.045):
        """
        Initialize performance metrics calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation (default 4.5%)
        """
        self.risk_free_rate = risk_free_rate
        
    def calculate_all_metrics(self, 
                            portfolio_values: List[float], 
                            trades: List[Dict[str, Any]], 
                            period: str = 'weekly') -> Dict[str, float]:
        """
        Calculate all performance metrics from portfolio values and trades.
        
        Args:
            portfolio_values: List of portfolio values over time
            trades: List of trade dictionaries
            period: Time period for returns ('daily', 'weekly', 'monthly')
            
        Returns:
            Dictionary of performance metrics
        """
        if len(portfolio_values) < 2:
            logger.warning("Insufficient data for metrics calculation")
            return self._empty_metrics()
            
        # Calculate returns
        returns = self._calculate_returns(portfolio_values)
        
        # Calculate individual metrics
        metrics = {
            'total_return': self._calculate_total_return(portfolio_values),
            'annualized_return': self._calculate_annualized_return(portfolio_values, period),
            'volatility': self._calculate_volatility(returns, period),
            'sharpe_ratio': self._calculate_sharpe_ratio(returns, period),
            'max_drawdown': self._calculate_max_drawdown(portfolio_values),
            'win_rate': self._calculate_win_rate(trades),
            'profit_factor': self._calculate_profit_factor(trades),
            'avg_win': self._calculate_avg_win(trades),
            'avg_loss': self._calculate_avg_loss(trades),
            'total_trades': len(trades),
            'winning_trades': self._count_winning_trades(trades),
            'losing_trades': self._count_losing_trades(trades)
        }
        
        return metrics
    
    def _calculate_returns(self, portfolio_values: List[float]) -> np.ndarray:
        """Calculate period-over-period returns."""
        values = np.array(portfolio_values)
        returns = np.diff(values) / values[:-1]
        return returns
    
    def _calculate_total_return(self, portfolio_values: List[float]) -> float:
        """Calculate total return from start to end."""
        if not portfolio_values or portfolio_values[0] == 0:
            return 0.0
        return ((portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]) * 100
    
    def _calculate_annualized_return(self, portfolio_values: List[float], period: str) -> float:
        """Calculate annualized return based on period."""
        if len(portfolio_values) < 2:
            return 0.0
            
        total_return = (portfolio_values[-1] / portfolio_values[0]) - 1
        num_periods = len(portfolio_values) - 1
        
        # Annualization factors
        periods_per_year = {
            'daily': 252,    # Trading days
            'weekly': 52,
            'monthly': 12
        }
        
        factor = periods_per_year.get(period, 52)
        years = num_periods / factor
        
        if years <= 0:
            return 0.0
            
        # Calculate annualized return
        annualized_return = (1 + total_return) ** (1 / years) - 1
        return annualized_return * 100
    
    def _calculate_volatility(self, returns: np.ndarray, period: str) -> float:
        """Calculate annualized volatility (standard deviation of returns)."""
        if len(returns) == 0:
            return 0.0
            
        # Annualization factors
        annualization_factor = {
            'daily': np.sqrt(252),
            'weekly': np.sqrt(52),
            'monthly': np.sqrt(12)
        }
        
        factor = annualization_factor.get(period, np.sqrt(52))
        volatility = np.std(returns) * factor
        return volatility * 100
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray, period: str) -> float:
        """
        Calculate Sharpe ratio (risk-adjusted returns).
        
        Sharpe = (Return - Risk Free Rate) / Volatility
        """
        if len(returns) == 0:
            return 0.0
            
        # Calculate average return and volatility
        periods_per_year = {'daily': 252, 'weekly': 52, 'monthly': 12}
        periods = periods_per_year.get(period, 52)
        
        avg_return = np.mean(returns) * periods  # Annualized
        volatility = np.std(returns) * np.sqrt(periods)  # Annualized
        
        if volatility == 0:
            return 0.0
            
        sharpe = (avg_return - self.risk_free_rate) / volatility
        return round(sharpe, 3)
    
    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """
        Calculate maximum drawdown (largest peak-to-trough loss).
        
        Returns:
            Maximum drawdown as a percentage (negative value)
        """
        if len(portfolio_values) < 2:
            return 0.0
            
        values = np.array(portfolio_values)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(values)
        
        # Calculate drawdown at each point
        drawdowns = (values - running_max) / running_max
        
        # Find maximum drawdown
        max_drawdown = np.min(drawdowns)
        
        return max_drawdown * 100
    
    def _calculate_win_rate(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate percentage of winning trades."""
        if not trades:
            return 0.0
            
        winning_trades = self._count_winning_trades(trades)
        return (winning_trades / len(trades)) * 100
    
    def _count_winning_trades(self, trades: List[Dict[str, Any]]) -> int:
        """Count number of winning trades (positive cash flow)."""
        return sum(1 for trade in trades if trade.get('cash_flow', 0) > 0)
    
    def _count_losing_trades(self, trades: List[Dict[str, Any]]) -> int:
        """Count number of losing trades (negative cash flow)."""
        return sum(1 for trade in trades if trade.get('cash_flow', 0) < 0)
    
    def _calculate_profit_factor(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate profit factor (gross profits / gross losses).
        
        A profit factor > 1 indicates profitable strategy.
        """
        gross_profits = sum(trade['cash_flow'] for trade in trades if trade.get('cash_flow', 0) > 0)
        gross_losses = abs(sum(trade['cash_flow'] for trade in trades if trade.get('cash_flow', 0) < 0))
        
        if gross_losses == 0:
            return float('inf') if gross_profits > 0 else 0.0
            
        return round(gross_profits / gross_losses, 2)
    
    def _calculate_avg_win(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate average winning trade amount."""
        winning_trades = [trade['cash_flow'] for trade in trades if trade.get('cash_flow', 0) > 0]
        
        if not winning_trades:
            return 0.0
            
        return round(np.mean(winning_trades), 2)
    
    def _calculate_avg_loss(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate average losing trade amount."""
        losing_trades = [trade['cash_flow'] for trade in trades if trade.get('cash_flow', 0) < 0]
        
        if not losing_trades:
            return 0.0
            
        return round(np.mean(losing_trades), 2)
    
    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics dictionary when insufficient data."""
        return {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'volatility': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }
    
    def format_metrics_report(self, metrics: Dict[str, float]) -> str:
        """Format metrics into a readable report."""
        report = []
        report.append("=== PERFORMANCE METRICS ===")
        report.append(f"Total Return: {metrics['total_return']:.2f}%")
        report.append(f"Annualized Return: {metrics['annualized_return']:.2f}%")
        report.append(f"Volatility: {metrics['volatility']:.2f}%")
        report.append(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        report.append(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        report.append("")
        report.append("=== TRADE STATISTICS ===")
        report.append(f"Total Trades: {metrics['total_trades']}")
        report.append(f"Win Rate: {metrics['win_rate']:.1f}%")
        report.append(f"Winning Trades: {metrics['winning_trades']}")
        report.append(f"Losing Trades: {metrics['losing_trades']}")
        report.append(f"Profit Factor: {metrics['profit_factor']:.2f}")
        report.append(f"Average Win: ${metrics['avg_win']:.2f}")
        report.append(f"Average Loss: ${metrics['avg_loss']:.2f}")
        
        return "\n".join(report)


def calculate_strategy_metrics(strategy_name: str, 
                             initial_capital: float,
                             final_capital: float,
                             trades: List[Dict[str, Any]],
                             portfolio_history: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Convenience function to calculate metrics for a strategy.
    
    Args:
        strategy_name: Name of the strategy
        initial_capital: Starting capital
        final_capital: Ending capital
        trades: List of trades
        portfolio_history: Optional list of portfolio values over time
        
    Returns:
        Dictionary containing strategy name and all metrics
    """
    calc = PerformanceMetrics()
    
    # If no portfolio history provided, create simple one from capital values
    if portfolio_history is None:
        portfolio_history = [initial_capital, final_capital]
    
    metrics = calc.calculate_all_metrics(portfolio_history, trades)
    
    # Add strategy-specific information
    metrics['strategy_name'] = strategy_name
    metrics['initial_capital'] = initial_capital
    metrics['final_capital'] = final_capital
    metrics['net_profit'] = final_capital - initial_capital
    
    return metrics