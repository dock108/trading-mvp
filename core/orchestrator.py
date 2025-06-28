"""
Trading strategy orchestrator.

This module handles:
- Strategy initialization and coordination
- Trade execution across multiple strategies
- Result collection and output formatting
- Integration with data sources and configuration
"""

import csv
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from strategies.wheel_strategy import WheelStrategy
from strategies.crypto_rotator_strategy import CryptoRotator
from data.price_fetcher import PriceFetcher
from data.database import get_database, log_trade_to_db
from core.config import ConfigManager

logger = logging.getLogger(__name__)


class OrchestrationError(Exception):
    """Exception raised for orchestration errors."""
    pass


class TradingOrchestrator:
    """Coordinates execution of multiple trading strategies."""
    
    def __init__(self, config: Dict[str, Any], price_fetcher: Optional[PriceFetcher] = None):
        """Initialize orchestrator with configuration.
        
        Args:
            config: Configuration dictionary
            price_fetcher: Optional price fetcher instance
        """
        self.config = config
        self.price_fetcher = price_fetcher
        self.config_manager = ConfigManager()
        self.strategies = {}
        self.all_trades = []
        self.db = get_database()
        
        # Initialize strategies based on configuration
        self._initialize_strategies()
        
        logger.info(f"Orchestrator initialized with {len(self.strategies)} strategies")
    
    def _initialize_strategies(self) -> None:
        """Initialize enabled strategies with proper capital allocation."""
        enabled_strategies = self.config_manager.get_enabled_strategies(self.config)
        allocations = self.config_manager.calculate_strategy_allocation(self.config)
        initial_capital = self.config.get('initial_capital', 100000)
        
        logger.info(f"Initializing {len(enabled_strategies)} strategies")
        
        # Initialize wheel strategy
        if enabled_strategies.get('wheel', False):
            wheel_capital = initial_capital * allocations.get('wheel', 0.0)
            wheel_symbols = self.config.get('wheel_symbols', ['SPY', 'QQQ', 'IWM'])
            
            self.strategies['wheel'] = WheelStrategy(
                capital=wheel_capital,
                symbols=wheel_symbols,
                config=self.config,
                price_fetcher=self.price_fetcher
            )
            
            logger.info(f"Wheel strategy initialized with ${wheel_capital:,.2f} capital, "
                       f"symbols: {wheel_symbols}")
        
        # Initialize crypto rotator strategy
        if enabled_strategies.get('rotator', False):
            rotator_capital = initial_capital * allocations.get('rotator', 0.0)
            rotator_symbols = self.config.get('rotator_symbols', ['BTC', 'ETH', 'SOL'])
            
            self.strategies['rotator'] = CryptoRotator(
                capital=rotator_capital,
                coins=rotator_symbols,  # CryptoRotator uses 'coins' parameter
                config=self.config,
                price_fetcher=self.price_fetcher
            )
            
            logger.info(f"Crypto rotator initialized with ${rotator_capital:,.2f} capital, "
                       f"symbols: {rotator_symbols}")
        
        if not self.strategies:
            raise OrchestrationError("No strategies enabled in configuration")
    
    def execute_simulation(self, weeks: int = 52, start_week: int = 0) -> List[Dict[str, Any]]:
        """Execute trading simulation across all strategies.
        
        Args:
            weeks: Number of weeks to simulate (passed to strategies)
            start_week: Starting week number (not used by current strategies)
            
        Returns:
            List of all trades executed across strategies
            
        Raises:
            OrchestrationError: If simulation fails
        """
        logger.info(f"Starting simulation with {len(self.strategies)} strategies")
        
        try:
            # Generate run ID for database tracking
            run_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Start strategy run tracking
            strategy_names = list(self.strategies.keys())
            self.db.start_strategy_run(run_id, self.config, strategy_names)
            
            all_trades = []
            
            # Execute each strategy
            for strategy_name, strategy in self.strategies.items():
                try:
                    logger.info(f"Executing {strategy_name} strategy...")
                    
                    # Call strategy's run method (strategies manage their own simulation loop)
                    strategy_trades = strategy.run(backtest=True)
                    
                    # Add strategy name to each trade
                    for trade in strategy_trades:
                        trade['strategy'] = strategy_name
                        
                        # Log to database
                        try:
                            log_trade_to_db(trade)
                        except Exception as e:
                            logger.warning(f"Failed to log trade to database: {e}")
                    
                    all_trades.extend(strategy_trades)
                    logger.info(f"{strategy_name} completed: {len(strategy_trades)} trades")
                    
                except Exception as e:
                    logger.error(f"Strategy {strategy_name} failed: {e}")
                    continue
            
            # Sort trades chronologically for output
            all_trades.sort(key=lambda t: (t.get('week', ''), t.get('timestamp', '')))
            
            # Calculate final portfolio value
            final_capital = self._calculate_total_portfolio_value()
            
            # Complete strategy run tracking
            self.db.complete_strategy_run(run_id, len(all_trades), final_capital)
            
            logger.info(f"Simulation completed: {len(all_trades)} trades, "
                       f"final value: ${final_capital:,.2f}")
            
            self.all_trades = all_trades
            return all_trades
            
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            # Record failed run
            try:
                self.db.complete_strategy_run(run_id, 0, 0, str(e))
            except:
                pass
            raise OrchestrationError(f"Simulation execution failed: {e}")
    
    def _execute_week(self, week: int) -> List[Dict[str, Any]]:
        """Execute trading for a single week across all strategies.
        
        Args:
            week: Week number
            
        Returns:
            List of trades executed this week
        """
        week_trades = []
        week_name = f"Week{week}"
        
        # Collect current prices for all symbols
        all_symbols = set()
        for strategy in self.strategies.values():
            if hasattr(strategy, 'symbols'):
                all_symbols.update(strategy.symbols)
            elif hasattr(strategy, 'coins'):
                all_symbols.update(strategy.coins)
        
        # Get current prices (mock or live data)
        current_prices = self._get_current_prices(all_symbols, week)
        
        # Execute each strategy
        for strategy_name, strategy in self.strategies.items():
            try:
                # Get strategy-specific prices
                strategy_symbols = getattr(strategy, 'symbols', None) or getattr(strategy, 'coins', [])
                strategy_prices = {
                    symbol: current_prices.get(symbol, 0.0) 
                    for symbol in strategy_symbols
                }
                
                # Execute strategy for this week
                if hasattr(strategy, 'execute_week'):
                    trades = strategy.execute_week(week, strategy_prices)
                else:
                    trades = strategy.execute(week_name, strategy_prices)
                
                # Add strategy name and standardize format
                for trade in trades:
                    trade['strategy'] = strategy_name
                    trade['week'] = week_name
                    
                    # Log to database
                    try:
                        log_trade_to_db(trade)
                    except Exception as e:
                        logger.warning(f"Failed to log trade to database: {e}")
                
                week_trades.extend(trades)
                
                logger.debug(f"Week {week}, {strategy_name}: {len(trades)} trades")
                
            except Exception as e:
                logger.error(f"Strategy {strategy_name} failed in week {week}: {e}")
                continue
        
        return week_trades
    
    def _get_current_prices(self, symbols: set, week: int) -> Dict[str, float]:
        """Get current prices for all symbols.
        
        Args:
            symbols: Set of symbols to fetch prices for
            week: Current week (for mock data)
            
        Returns:
            Dictionary mapping symbols to prices
        """
        current_prices = {}
        
        for symbol in symbols:
            try:
                if self.price_fetcher:
                    # Use live data source
                    if symbol in ['BTC', 'ETH', 'SOL']:
                        # Crypto symbol - convert to CoinGecko format
                        crypto_map = {'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana'}
                        crypto_id = crypto_map.get(symbol, symbol.lower())
                        price = self.price_fetcher.get_crypto_price(crypto_id)
                    else:
                        # ETF symbol
                        price = self.price_fetcher.get_etf_price(symbol)
                    
                    if price is not None:
                        current_prices[symbol] = price
                    else:
                        # Fallback to mock data
                        current_prices[symbol] = self._get_mock_price(symbol, week)
                else:
                    # Use mock data
                    current_prices[symbol] = self._get_mock_price(symbol, week)
                    
            except Exception as e:
                logger.warning(f"Failed to get price for {symbol}: {e}")
                current_prices[symbol] = self._get_mock_price(symbol, week)
        
        return current_prices
    
    def _get_mock_price(self, symbol: str, week: int) -> float:
        """Generate mock price data for testing.
        
        Args:
            symbol: Symbol to generate price for
            week: Current week
            
        Returns:
            Mock price
        """
        # Base prices for deterministic mock data
        base_prices = {
            'SPY': 450.0,
            'QQQ': 380.0,
            'IWM': 200.0,
            'BTC': 50000.0,
            'ETH': 3000.0,
            'SOL': 100.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Add weekly variation for realistic simulation
        import math
        weekly_variation = math.sin(week * 0.1) * 0.05  # ±5% variation
        price = base_price * (1 + weekly_variation)
        
        return round(price, 2)
    
    def _calculate_total_portfolio_value(self) -> float:
        """Calculate total portfolio value across all strategies.
        
        Returns:
            Total portfolio value
        """
        total_value = 0.0
        
        for strategy_name, strategy in self.strategies.items():
            try:
                if hasattr(strategy, 'get_current_portfolio_value'):
                    value = strategy.get_current_portfolio_value()
                elif hasattr(strategy, 'capital'):
                    value = strategy.capital
                else:
                    logger.warning(f"Cannot determine portfolio value for {strategy_name}")
                    continue
                
                total_value += value
                logger.debug(f"{strategy_name} portfolio value: ${value:,.2f}")
                
            except Exception as e:
                logger.error(f"Error calculating portfolio value for {strategy_name}: {e}")
        
        return total_value
    
    def save_trades_to_files(self, trades: List[Dict[str, Any]], 
                           output_files: Dict[str, str]) -> None:
        """Save trades to multiple CSV formats.
        
        Args:
            trades: List of trade dictionaries
            output_files: Dictionary mapping format names to file paths
        """
        if not trades:
            logger.warning("No trades to save")
            return
        
        # Standard format (compatible with existing analysis tools)
        if 'standard' in output_files:
            self._write_standard_csv(trades, output_files['standard'])
        
        # Detailed format with additional fields
        if 'detailed' in output_files:
            self._write_detailed_csv(trades, output_files['detailed'])
        
        # Consolidated format with strategy names
        if 'consolidated' in output_files:
            self._write_consolidated_csv(trades, output_files['consolidated'])
        
        logger.info(f"Trade data saved to {len(output_files)} files")
    
    def _write_standard_csv(self, trades: List[Dict[str, Any]], filename: str) -> None:
        """Write trades in standard CSV format.
        
        Args:
            trades: Trade data
            filename: Output filename
        """
        fieldnames = ['Week', 'Strategy', 'Asset', 'Action', 'Quantity', 'Price', 'Amount']
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for trade in trades:
                writer.writerow({
                    'Week': trade.get('week', ''),
                    'Strategy': trade.get('strategy', '').title(),
                    'Asset': trade.get('symbol', ''),
                    'Action': trade.get('action', ''),
                    'Quantity': trade.get('quantity', 0),
                    'Price': trade.get('price', 0),
                    'Amount': trade.get('cash_flow', 0)
                })
        
        logger.debug(f"Standard CSV written: {filename}")
    
    def _write_detailed_csv(self, trades: List[Dict[str, Any]], filename: str) -> None:
        """Write trades in detailed CSV format.
        
        Args:
            trades: Trade data
            filename: Output filename
        """
        # Include all available fields
        all_fields = set()
        for trade in trades:
            all_fields.update(trade.keys())
        
        fieldnames = sorted(all_fields)
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(trades)
        
        logger.debug(f"Detailed CSV written: {filename}")
    
    def _write_consolidated_csv(self, trades: List[Dict[str, Any]], filename: str) -> None:
        """Write trades in consolidated format with strategy names.
        
        Args:
            trades: Trade data
            filename: Output filename
        """
        fieldnames = ['Week', 'Strategy', 'Asset', 'Action', 'Quantity', 'Price', 'Amount', 'strategy_name']
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for trade in trades:
                writer.writerow({
                    'Week': trade.get('week', ''),
                    'Strategy': trade.get('strategy', '').title(),
                    'Asset': trade.get('symbol', ''),
                    'Action': trade.get('action', ''),
                    'Quantity': trade.get('quantity', 0),
                    'Price': trade.get('price', 0),
                    'Amount': trade.get('cash_flow', 0),
                    'strategy_name': trade.get('strategy', '')
                })
        
        logger.debug(f"Consolidated CSV written: {filename}")
    
    def get_strategy_summary(self) -> str:
        """Get summary of strategy performance.
        
        Returns:
            Strategy performance summary
        """
        summary_lines = []
        total_value = 0.0
        
        for strategy_name, strategy in self.strategies.items():
            try:
                if hasattr(strategy, 'get_current_portfolio_value'):
                    value = strategy.get_current_portfolio_value()
                elif hasattr(strategy, 'capital'):
                    value = strategy.capital
                else:
                    value = 0.0
                
                initial_capital = getattr(strategy, 'initial_capital', 0.0)
                pnl = value - initial_capital
                pnl_pct = (pnl / initial_capital * 100) if initial_capital > 0 else 0.0
                
                summary_lines.append(
                    f"{strategy_name.title()}: ${value:,.2f} "
                    f"(P&L: ${pnl:+,.2f}, {pnl_pct:+.1f}%)"
                )
                
                total_value += value
                
            except Exception as e:
                summary_lines.append(f"{strategy_name.title()}: Error calculating value - {e}")
        
        initial_total = self.config.get('initial_capital', 0.0)
        total_pnl = total_value - initial_total
        total_pnl_pct = (total_pnl / initial_total * 100) if initial_total > 0 else 0.0
        
        summary_lines.append("")
        summary_lines.append(
            f"Total Portfolio: ${total_value:,.2f} "
            f"(P&L: ${total_pnl:+,.2f}, {total_pnl_pct:+.1f}%)"
        )
        
        return "\n".join(summary_lines)
    
    def perform_health_check(self) -> Dict[str, str]:
        """Perform health check on data sources and strategies.
        
        Returns:
            Health check results
        """
        results = {}
        
        # Check price fetcher
        if self.price_fetcher:
            try:
                health = self.price_fetcher.health_check()
                results.update(health)
            except Exception as e:
                results['price_fetcher'] = f"❌ Error: {e}"
        else:
            results['price_fetcher'] = "⚠️  Using mock data"
        
        # Check database
        try:
            stats = self.db.get_database_stats()
            results['database'] = f"✅ Connected ({stats.get('trades_count', 0)} trades)"
        except Exception as e:
            results['database'] = f"❌ Error: {e}"
        
        # Check strategies
        for strategy_name, strategy in self.strategies.items():
            try:
                # Basic strategy health check
                if hasattr(strategy, 'capital') and strategy.capital > 0:
                    results[f'strategy_{strategy_name}'] = "✅ Initialized"
                else:
                    results[f'strategy_{strategy_name}'] = "⚠️  No capital"
            except Exception as e:
                results[f'strategy_{strategy_name}'] = f"❌ Error: {e}"
        
        return results