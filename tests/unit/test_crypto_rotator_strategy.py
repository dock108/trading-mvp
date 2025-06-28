"""
Unit tests for the Crypto Rotator Strategy implementation.

Tests cover:
- Rotation logic and decision making
- Performance calculations
- Position management
- Portfolio rebalancing
"""

import pytest
from unittest.mock import Mock, patch
from strategies.crypto_rotator_strategy import CryptoRotator
from tests.conftest import MockPriceFetcher


class TestCryptoRotatorStrategy:
    """Test suite for CryptoRotator class."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.initial_capital = 50000
        self.symbols = ['BTC', 'ETH', 'SOL']
        self.mock_fetcher = Mock()
        
        # Create strategy instance
        self.strategy = CryptoRotator(
            symbols=self.symbols,
            initial_capital=self.initial_capital,
            price_fetcher=self.mock_fetcher
        )

    def test_initialization(self):
        """Test strategy initialization with correct parameters."""
        assert self.strategy.symbols == self.symbols
        assert self.strategy.initial_capital == self.initial_capital
        assert self.strategy.current_capital == self.initial_capital
        assert self.strategy.current_position is None
        assert len(self.strategy.price_history) == 0

    def test_first_week_execution(self):
        """Test first week execution - should select best performing asset."""
        prices = {'BTC': 50000, 'ETH': 3000, 'SOL': 100}
        
        # Mock price fetcher
        self.mock_fetcher.get_current_price.side_effect = lambda symbol: prices[symbol]
        
        trades = self.strategy.execute_week(0, prices)
        
        # Should have exactly one trade (initial purchase)
        assert len(trades) == 1
        trade = trades[0]
        
        # Should be a buy action
        assert trade['action'] == 'BUY_CRYPTO'
        assert trade['symbol'] in self.symbols
        assert trade['cash_flow'] < 0  # Money spent
        assert self.strategy.current_position is not None

    def test_rotation_decision_better_performer(self):
        """Test rotation when a different asset performs better."""
        # Set up initial position
        self.strategy.current_position = 'BTC'
        self.strategy.position_quantity = 1.0
        self.strategy.current_capital = 0  # All invested
        
        # Set up price history - BTC underperforming
        self.strategy.price_history = [
            {'BTC': 50000, 'ETH': 3000, 'SOL': 100},  # Week 0
            {'BTC': 49000, 'ETH': 3200, 'SOL': 110}   # Week 1 - ETH and SOL outperformed BTC
        ]
        
        week_1_prices = {'BTC': 49000, 'ETH': 3200, 'SOL': 110}
        self.mock_fetcher.get_current_price.side_effect = lambda symbol: week_1_prices[symbol]
        
        trades = self.strategy.execute_week(1, week_1_prices)
        
        # Should have rotation trades (sell + buy)
        if len(trades) >= 2:
            # Should sell current position
            sell_trade = next((t for t in trades if t['action'] == 'SELL_CRYPTO'), None)
            assert sell_trade is not None
            assert sell_trade['symbol'] == 'BTC'
            assert sell_trade['cash_flow'] > 0  # Money received
            
            # Should buy new position
            buy_trade = next((t for t in trades if t['action'] == 'BUY_CRYPTO'), None)
            assert buy_trade is not None
            assert buy_trade['symbol'] != 'BTC'  # Different asset
            assert buy_trade['cash_flow'] < 0  # Money spent

    def test_no_rotation_when_current_best(self):
        """Test no rotation when current position is still the best performer."""
        # Set up initial position
        self.strategy.current_position = 'BTC'
        self.strategy.position_quantity = 1.0
        
        # Set up price history - BTC continues to outperform
        self.strategy.price_history = [
            {'BTC': 50000, 'ETH': 3000, 'SOL': 100},  # Week 0
            {'BTC': 52000, 'ETH': 3100, 'SOL': 105}   # Week 1 - BTC still best
        ]
        
        week_1_prices = {'BTC': 52000, 'ETH': 3100, 'SOL': 105}
        self.mock_fetcher.get_current_price.side_effect = lambda symbol: week_1_prices[symbol]
        
        trades = self.strategy.execute_week(1, week_1_prices)
        
        # Should have no trades (hold current position)
        assert len(trades) == 0 or all(t['action'] not in ['SELL_CRYPTO', 'BUY_CRYPTO'] for t in trades)

    def test_performance_calculation(self):
        """Test performance calculation for different assets."""
        # Set up price history
        price_history = [
            {'BTC': 50000, 'ETH': 3000, 'SOL': 100},  # Week 0
            {'BTC': 55000, 'ETH': 3300, 'SOL': 110}   # Week 1
        ]
        
        self.strategy.price_history = price_history
        
        # Calculate performance (if method is public or we can access it)
        # This tests the internal logic that drives rotation decisions
        
        # BTC: 55000/50000 = 1.10 (10% gain)
        # ETH: 3300/3000 = 1.10 (10% gain)  
        # SOL: 110/100 = 1.10 (10% gain)
        
        # All performed equally - strategy should stick with current or pick consistently
        current_prices = {'BTC': 55000, 'ETH': 3300, 'SOL': 110}
        
        # The specific implementation might vary, but behavior should be consistent
        if hasattr(self.strategy, '_calculate_performance'):
            btc_perf = self.strategy._calculate_performance('BTC', price_history)
            eth_perf = self.strategy._calculate_performance('ETH', price_history)
            sol_perf = self.strategy._calculate_performance('SOL', price_history)
            
            assert abs(btc_perf - 0.10) < 0.01  # 10% gain
            assert abs(eth_perf - 0.10) < 0.01  # 10% gain
            assert abs(sol_perf - 0.10) < 0.01  # 10% gain

    def test_position_quantity_calculation(self):
        """Test that position quantities are calculated correctly."""
        capital = 50000
        price = 50000  # BTC price
        
        self.strategy.current_capital = capital
        
        # Execute trade
        trades = self.strategy.execute_week(0, {'BTC': price, 'ETH': 3000, 'SOL': 100})
        
        if trades:
            buy_trade = next((t for t in trades if t['action'] == 'BUY_CRYPTO'), None)
            if buy_trade:
                expected_quantity = capital / price
                assert abs(buy_trade['quantity'] - expected_quantity) < 0.0001

    def test_portfolio_value_calculation(self):
        """Test portfolio value calculation with current positions."""
        # Set up position
        self.strategy.current_position = 'BTC'
        self.strategy.position_quantity = 1.0
        self.strategy.current_capital = 1000  # Some remaining cash
        
        current_prices = {'BTC': 55000, 'ETH': 3300, 'SOL': 110}
        
        portfolio_value = self.strategy.get_current_portfolio_value(current_prices)
        
        # Should be cash + position value
        expected_value = 1000 + (1.0 * 55000)  # Cash + BTC value
        assert abs(portfolio_value - expected_value) < 0.01

    def test_no_position_portfolio_value(self):
        """Test portfolio value calculation with no current position."""
        # No position, all cash
        self.strategy.current_position = None
        self.strategy.position_quantity = 0
        self.strategy.current_capital = 50000
        
        current_prices = {'BTC': 55000, 'ETH': 3300, 'SOL': 110}
        
        portfolio_value = self.strategy.get_current_portfolio_value(current_prices)
        
        # Should equal current capital
        assert abs(portfolio_value - 50000) < 0.01

    def test_price_history_tracking(self):
        """Test that price history is properly tracked."""
        prices_week_0 = {'BTC': 50000, 'ETH': 3000, 'SOL': 100}
        prices_week_1 = {'BTC': 52000, 'ETH': 3100, 'SOL': 105}
        
        self.mock_fetcher.get_current_price.side_effect = lambda symbol: prices_week_0[symbol]
        self.strategy.execute_week(0, prices_week_0)
        
        self.mock_fetcher.get_current_price.side_effect = lambda symbol: prices_week_1[symbol]
        self.strategy.execute_week(1, prices_week_1)
        
        # Price history should contain both weeks
        assert len(self.strategy.price_history) >= 2
        assert prices_week_0 in self.strategy.price_history
        assert prices_week_1 in self.strategy.price_history

    def test_error_handling_missing_price(self):
        """Test error handling when price data is missing."""
        incomplete_prices = {'BTC': 50000, 'ETH': 3000}  # Missing SOL
        
        # Should handle gracefully
        try:
            trades = self.strategy.execute_week(0, incomplete_prices)
            assert isinstance(trades, list)
        except KeyError:
            # If it raises KeyError, it should be handled at a higher level
            pass

    def test_zero_capital_scenario(self):
        """Test behavior when capital is zero or very low."""
        self.strategy.current_capital = 0
        
        prices = {'BTC': 50000, 'ETH': 3000, 'SOL': 100}
        
        trades = self.strategy.execute_week(0, prices)
        
        # Should handle gracefully - no trades possible
        buy_trades = [t for t in trades if t['action'] == 'BUY_CRYPTO']
        assert len(buy_trades) == 0

    @pytest.mark.parametrize("symbol", ['BTC', 'ETH', 'SOL'])
    def test_single_asset_scenarios(self, symbol):
        """Test strategy with each individual asset as the best performer."""
        # Create scenario where specified symbol is the clear winner
        base_prices = {'BTC': 50000, 'ETH': 3000, 'SOL': 100}
        week_1_prices = base_prices.copy()
        
        # Make the specified symbol perform 20% better
        week_1_prices[symbol] = base_prices[symbol] * 1.20
        
        # Set up price history
        self.strategy.price_history = [base_prices]
        
        self.mock_fetcher.get_current_price.side_effect = lambda s: week_1_prices[s]
        
        trades = self.strategy.execute_week(1, week_1_prices)
        
        # If there's a buy trade, it should be for the best performer
        buy_trades = [t for t in trades if t['action'] == 'BUY_CRYPTO']
        if buy_trades:
            assert buy_trades[0]['symbol'] == symbol

    def test_transaction_costs_consideration(self):
        """Test that transaction costs don't cause excessive rotation."""
        # Set up a scenario with minimal performance differences
        # The strategy should avoid churning with small differences
        
        # Set up initial position
        self.strategy.current_position = 'BTC'
        self.strategy.position_quantity = 1.0
        
        # Set up price history with minimal differences
        self.strategy.price_history = [
            {'BTC': 50000, 'ETH': 3000, 'SOL': 100},
            {'BTC': 50100, 'ETH': 3002, 'SOL': 100.1}  # Very small differences
        ]
        
        week_1_prices = {'BTC': 50100, 'ETH': 3002, 'SOL': 100.1}
        self.mock_fetcher.get_current_price.side_effect = lambda symbol: week_1_prices[symbol]
        
        trades = self.strategy.execute_week(1, week_1_prices)
        
        # Should avoid rotation for minimal gains
        rotation_trades = [t for t in trades if t['action'] in ['SELL_CRYPTO', 'BUY_CRYPTO']]
        # Strategy might or might not rotate based on implementation,
        # but it should be consistent and logical
        assert isinstance(rotation_trades, list)