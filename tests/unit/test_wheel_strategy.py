"""
Unit tests for the Wheel Strategy implementation.

Tests cover:
- State machine transitions
- Trade execution logic
- Capital management
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, patch
from strategies.wheel_strategy import WheelStrategy, WheelState
from tests.conftest import MockPriceFetcher


class TestWheelStrategy:
    """Test suite for WheelStrategy class."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.initial_capital = 50000
        self.symbols = ['SPY', 'QQQ']
        self.mock_fetcher = Mock()
        
        # Create strategy instance
        self.strategy = WheelStrategy(
            symbols=self.symbols,
            initial_capital=self.initial_capital,
            price_fetcher=self.mock_fetcher
        )

    def test_initialization(self):
        """Test strategy initialization with correct parameters."""
        assert self.strategy.symbols == self.symbols
        assert self.strategy.initial_capital == self.initial_capital
        assert self.strategy.available_capital == self.initial_capital
        assert len(self.strategy.positions) == len(self.symbols)
        
        # Check initial state for each symbol
        for symbol in self.symbols:
            assert symbol in self.strategy.positions
            assert self.strategy.positions[symbol]['state'] == WheelState.READY

    def test_state_transitions_cash_secured_put(self):
        """Test state transition from READY to PUT_SOLD."""
        symbol = 'SPY'
        mock_price = 450.0
        self.mock_fetcher.get_current_price.return_value = mock_price
        
        # Execute first step (should sell put)
        trades = self.strategy.execute_week(0, {symbol: mock_price})
        
        # Verify trade was executed
        assert len(trades) == 1
        trade = trades[0]
        assert trade['symbol'] == symbol
        assert trade['action'] == 'SELL_PUT'
        assert trade['cash_flow'] > 0  # Premium received
        
        # Verify state transition
        assert self.strategy.positions[symbol]['state'] == WheelState.PUT_SOLD

    def test_assignment_scenario(self):
        """Test assignment scenario when put is in-the-money."""
        symbol = 'SPY'
        initial_price = 450.0
        assignment_price = 440.0  # Lower than strike, triggering assignment
        
        # First, sell a put
        self.mock_fetcher.get_current_price.return_value = initial_price
        trades1 = self.strategy.execute_week(0, {symbol: initial_price})
        
        # Simulate assignment scenario
        self.mock_fetcher.get_current_price.return_value = assignment_price
        trades2 = self.strategy.execute_week(1, {symbol: assignment_price})
        
        # Should have assignment trade
        assignment_trade = next(
            (t for t in trades2 if t['action'] == 'BUY_SHARES'), None
        )
        assert assignment_trade is not None
        assert assignment_trade['symbol'] == symbol
        assert assignment_trade['cash_flow'] < 0  # Money spent on shares
        
        # State should transition to SHARES_OWNED
        assert self.strategy.positions[symbol]['state'] == WheelState.SHARES_OWNED

    def test_covered_call_scenario(self):
        """Test covered call after owning shares."""
        symbol = 'SPY'
        
        # Set up position with owned shares
        self.strategy.positions[symbol] = {
            'state': WheelState.SHARES_OWNED,
            'shares': 100,
            'cost_basis': 440.0,
            'option_premium': 0
        }
        
        current_price = 445.0
        self.mock_fetcher.get_current_price.return_value = current_price
        
        trades = self.strategy.execute_week(2, {symbol: current_price})
        
        # Should sell covered call
        call_trade = next(
            (t for t in trades if t['action'] == 'SELL_CALL'), None
        )
        assert call_trade is not None
        assert call_trade['cash_flow'] > 0  # Premium received
        
        # State should transition to CALL_SOLD
        assert self.strategy.positions[symbol]['state'] == WheelState.CALL_SOLD

    def test_capital_management(self):
        """Test that capital is properly managed across trades."""
        symbol = 'SPY'
        initial_available = self.strategy.available_capital
        
        # Mock price and execute trade
        self.mock_fetcher.get_current_price.return_value = 450.0
        trades = self.strategy.execute_week(0, {symbol: 450.0})
        
        if trades:
            # Available capital should be updated
            assert self.strategy.available_capital != initial_available
            
            # Cash flow should be accounted for
            total_cash_flow = sum(trade['cash_flow'] for trade in trades)
            expected_capital = initial_available + total_cash_flow
            assert abs(self.strategy.available_capital - expected_capital) < 0.01

    def test_multiple_symbols_execution(self):
        """Test execution with multiple symbols."""
        prices = {'SPY': 450.0, 'QQQ': 380.0}
        
        self.mock_fetcher.get_current_price.side_effect = lambda symbol: prices[symbol]
        
        trades = self.strategy.execute_week(0, prices)
        
        # Should have trades for both symbols (if capital allows)
        symbols_traded = {trade['symbol'] for trade in trades}
        assert len(symbols_traded) >= 1  # At least one symbol should trade

    def test_insufficient_capital_scenario(self):
        """Test behavior when insufficient capital for trades."""
        # Reduce available capital significantly
        self.strategy.available_capital = 1000  # Very low
        
        symbol = 'SPY'
        self.mock_fetcher.get_current_price.return_value = 450.0
        
        trades = self.strategy.execute_week(0, {symbol: 450.0})
        
        # Should handle gracefully - either no trades or appropriate sizing
        for trade in trades:
            # Any executed trade should not exceed available capital
            if trade['cash_flow'] < 0:  # Outflow
                assert abs(trade['cash_flow']) <= self.strategy.available_capital + 100

    def test_get_current_portfolio_value(self):
        """Test portfolio value calculation."""
        # Set up a position with shares
        symbol = 'SPY'
        shares = 100
        current_price = 450.0
        
        self.strategy.positions[symbol] = {
            'state': WheelState.SHARES_OWNED,
            'shares': shares,
            'cost_basis': 440.0,
            'option_premium': 0
        }
        
        self.mock_fetcher.get_current_price.return_value = current_price
        
        portfolio_value = self.strategy.get_current_portfolio_value({symbol: current_price})
        
        # Should include cash + share value
        expected_value = self.strategy.available_capital + (shares * current_price)
        assert abs(portfolio_value - expected_value) < 0.01

    def test_error_handling_missing_price(self):
        """Test error handling when price data is missing."""
        symbol = 'SPY'
        
        # Mock fetcher to raise exception
        self.mock_fetcher.get_current_price.side_effect = Exception("Price not available")
        
        # Should handle gracefully without crashing
        try:
            trades = self.strategy.execute_week(0, {})
            # If it returns, should be empty or handle the error
            assert isinstance(trades, list)
        except Exception as e:
            # If it raises, should be a meaningful error
            assert "Price not available" in str(e) or "price" in str(e).lower()

    def test_deterministic_behavior(self):
        """Test that strategy behavior is deterministic given same inputs."""
        symbol = 'SPY'
        price = 450.0
        week = 0
        
        self.mock_fetcher.get_current_price.return_value = price
        
        # Execute same scenario twice
        strategy2 = WheelStrategy(
            symbols=self.symbols,
            initial_capital=self.initial_capital,
            price_fetcher=self.mock_fetcher
        )
        
        trades1 = self.strategy.execute_week(week, {symbol: price})
        trades2 = strategy2.execute_week(week, {symbol: price})
        
        # Results should be identical
        assert len(trades1) == len(trades2)
        for t1, t2 in zip(trades1, trades2):
            assert t1['action'] == t2['action']
            assert t1['symbol'] == t2['symbol']
            assert abs(t1['cash_flow'] - t2['cash_flow']) < 0.01

    @pytest.mark.parametrize("state", [
        WheelState.CASH_SECURED_PUT,
        WheelState.HOLDING_SHARES,
        WheelState.COVERED_CALL
    ])
    def test_all_state_transitions(self, state):
        """Test behavior from all possible states."""
        symbol = 'SPY'
        price = 450.0
        
        # Set up specific state
        if state == WheelState.HOLDING_SHARES:
            self.strategy.positions[symbol] = {
                'state': state,
                'shares': 100,
                'cost_basis': 440.0,
                'option_premium': 0
            }
        elif state == WheelState.COVERED_CALL:
            self.strategy.positions[symbol] = {
                'state': state,
                'shares': 100,
                'cost_basis': 440.0,
                'call_strike': 450.0,
                'option_premium': 5.0
            }
        else:
            self.strategy.positions[symbol]['state'] = state
        
        self.mock_fetcher.get_current_price.return_value = price
        
        # Should handle any state without crashing
        trades = self.strategy.execute_week(0, {symbol: price})
        assert isinstance(trades, list)