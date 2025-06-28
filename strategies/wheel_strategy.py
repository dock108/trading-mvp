"""
Options Wheel Strategy implementation.

This module simulates an options wheel strategy on stock ETFs (SPY, QQQ, IWM).
The wheel strategy involves selling cash-secured puts and covered calls.
"""

import csv
import pandas as pd
from datetime import datetime
from enum import Enum
import random

class WheelState(Enum):
    """Wheel strategy states for each symbol."""
    CASH_SECURED_PUT = "csp"
    HOLDING_SHARES = "holding"
    COVERED_CALL = "cc"

class WheelStrategy:
    """Options Wheel Strategy for stock ETFs."""
    
    def __init__(self, capital, symbols, config=None):
        """Initialize the wheel strategy.
        
        Args:
            capital (float): Capital allocated to this strategy
            symbols (list): List of ETF symbols (e.g., ['SPY', 'QQQ', 'IWM'])
            config (dict): Additional configuration parameters
        """
        self.initial_capital = capital
        self.capital = capital
        self.available_capital = capital
        self.symbols = symbols
        self.config = config or {}
        self.trades = []
        
        # P&L tracking
        self.total_premiums_collected = 0.0
        self.realized_gains = 0.0
        self.unrealized_pnl = 0.0
        
        # Mock price data for 8 weeks of simulation
        self.prices = self._generate_mock_prices()
        self.current_week = 0
        
        # Position tracking for each symbol
        self.positions = {}
        for symbol in symbols:
            self.positions[symbol] = {
                'state': WheelState.CASH_SECURED_PUT,
                'shares': 0,
                'cost_basis': 0.0,
                'option_premium_collected': 0.0,
                'current_strike': None,
                'expiration_date': None
            }
    
    def _generate_mock_prices(self):
        """Generate mock price data for 8 weeks of simulation.
        
        Returns:
            dict: Weekly prices for each symbol
        """
        # Starting prices based on realistic ETF values
        base_prices = {
            "SPY": 450,
            "QQQ": 370, 
            "IWM": 210
        }
        
        prices = {}
        
        # Use test mode for deterministic full cycle demonstration
        if self.config.get('test_mode', False):
            # Create deterministic price sequence to force full wheel cycle
            for symbol in self.symbols:
                base_price = base_prices.get(symbol, 400)
                # Week 0: Start at base price
                # Week 1: Drop below put strike to force assignment
                # Week 2-3: Stay low while holding shares
                # Week 4: Rise above call strike to force exercise
                # Week 5-7: Continue varied movements
                prices[symbol] = [
                    base_price,          # Week 0: $450
                    base_price * 0.92,   # Week 1: $414 (below put strike ~$427.50)
                    base_price * 0.94,   # Week 2: $423 (still holding)
                    base_price * 0.96,   # Week 3: $432 (still holding)
                    base_price * 1.08,   # Week 4: $486 (above call strike ~$434.70)
                    base_price * 1.02,   # Week 5: $459
                    base_price * 0.98,   # Week 6: $441
                    base_price * 1.01,   # Week 7: $454.50
                    base_price * 0.99    # Week 8: $445.50
                ]
        else:
            # Original random generation for production use
            random.seed(42)  # For reproducible results
            
            for symbol in self.symbols:
                base_price = base_prices.get(symbol, 400)
                weekly_prices = [base_price]
                
                # Generate 8 weeks of price movements (-3% to +3% weekly)
                for week in range(8):
                    price_change = random.uniform(-0.03, 0.03)
                    new_price = weekly_prices[-1] * (1 + price_change)
                    weekly_prices.append(round(new_price, 2))
                
                prices[symbol] = weekly_prices
            
        return prices
    
    def get_current_price(self, symbol):
        """Get current price for a symbol.
        
        Args:
            symbol (str): ETF symbol
            
        Returns:
            float: Current price
        """
        if symbol in self.prices and self.current_week < len(self.prices[symbol]):
            return self.prices[symbol][self.current_week]
        return 0.0
    
    def advance_week(self):
        """Advance to the next week in the simulation."""
        self.current_week += 1
        print(f"\n--- Week {self.current_week} ---")
        for symbol in self.symbols:
            price = self.get_current_price(symbol)
            print(f"{symbol}: ${price}")
        
    def get_position_info(self, symbol):
        """Get current position information for a symbol.
        
        Args:
            symbol (str): ETF symbol
            
        Returns:
            dict: Position information
        """
        return self.positions.get(symbol, {})
    
    def update_capital(self, amount, description=""):
        """Update capital and available capital.
        
        Args:
            amount (float): Amount to add (positive) or subtract (negative)
            description (str): Description of the capital change
        """
        self.capital += amount
        self.update_available_capital()
        if description:
            print(f"  Capital updated: {'+' if amount >= 0 else ''}${amount:.2f} ({description})")
    
    def update_available_capital(self):
        """Update available capital based on current positions."""
        tied_up_capital = 0
        for symbol, pos in self.positions.items():
            if pos['state'] == WheelState.CASH_SECURED_PUT and pos['current_strike']:
                # Capital tied up for cash-secured put
                tied_up_capital += pos['current_strike'] * 100  # 100 shares per contract
            elif pos['shares'] > 0:
                # Capital tied up in shares
                tied_up_capital += pos['shares'] * pos['cost_basis']
        
        self.available_capital = self.capital - tied_up_capital
    
    def calculate_unrealized_pnl(self):
        """Calculate unrealized P&L for current holdings."""
        unrealized = 0.0
        for symbol, pos in self.positions.items():
            if pos['shares'] > 0:
                current_price = self.get_current_price(symbol)
                market_value = pos['shares'] * current_price
                book_value = pos['shares'] * pos['cost_basis']
                unrealized += (market_value - book_value)
        
        self.unrealized_pnl = unrealized
        return unrealized
    
    def get_total_pnl(self):
        """Get total P&L (realized + unrealized + premiums).
        
        Returns:
            dict: Breakdown of P&L components
        """
        unrealized = self.calculate_unrealized_pnl()
        
        return {
            'total_premiums': self.total_premiums_collected,
            'realized_gains': self.realized_gains,
            'unrealized_pnl': unrealized,
            'total_pnl': self.total_premiums_collected + self.realized_gains + unrealized,
            'total_return_pct': ((self.capital + unrealized - self.initial_capital) / self.initial_capital) * 100
        }
        
    def run(self, backtest=True):
        """Run the wheel strategy simulation.
        
        Args:
            backtest (bool): Whether to run in backtest mode with deterministic data
            
        Returns:
            list: List of trade records
        """
        print(f"Executing Wheel Strategy with ${self.capital:,.2f}")
        print(f"Trading symbols: {self.symbols}")
        print(f"Available capital: ${self.available_capital:,.2f}")
        
        # Display initial prices
        print(f"\n--- Week {self.current_week} (Start) ---")
        for symbol in self.symbols:
            price = self.get_current_price(symbol)
            print(f"{symbol}: ${price}")
        
        # Display current positions
        print("\nInitial Positions:")
        for symbol in self.symbols:
            pos = self.positions[symbol]
            print(f"{symbol}: State={pos['state'].value}, Shares={pos['shares']}")
        
        # Run simulation for 8 weeks
        for week in range(8):
            if week > 0:
                self.advance_week()
            
            # Process each symbol independently
            for symbol in self.symbols:
                self._process_wheel_for_symbol(symbol)
            
            self.update_available_capital()
            
            # Show weekly P&L summary
            pnl = self.get_total_pnl()
            print(f"Week {self.current_week} P&L: Total=${pnl['total_pnl']:.2f} (Premiums=${pnl['total_premiums']:.2f}, Unrealized=${pnl['unrealized_pnl']:.2f})")
        
        # Final summary
        final_pnl = self.get_total_pnl()
        print(f"\n=== SIMULATION COMPLETE ===")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Capital: ${self.capital:,.2f}")
        print(f"Available Capital: ${self.available_capital:,.2f}")
        print(f"Total Trades: {len(self.trades)}")
        print(f"\nP&L BREAKDOWN:")
        print(f"  Premiums Collected: ${final_pnl['total_premiums']:.2f}")
        print(f"  Realized Gains: ${final_pnl['realized_gains']:.2f}")
        print(f"  Unrealized P&L: ${final_pnl['unrealized_pnl']:.2f}")
        print(f"  Total P&L: ${final_pnl['total_pnl']:.2f}")
        print(f"  Total Return: {final_pnl['total_return_pct']:.2f}%")
        
        # Print trades summary and export to CSV
        self.print_trades_summary()
        self.export_trades_to_csv()
        
        # Return trade list for main coordination
        return self.trades
    
    def _process_wheel_for_symbol(self, symbol):
        """Process wheel strategy for a single symbol for current week.
        
        Args:
            symbol (str): ETF symbol to process
        """
        pos = self.positions[symbol]
        current_price = self.get_current_price(symbol)
        
        if pos['state'] == WheelState.CASH_SECURED_PUT:
            self._handle_cash_secured_put(symbol, current_price)
        elif pos['state'] == WheelState.HOLDING_SHARES:
            self._handle_covered_call(symbol, current_price)
    
    def _handle_cash_secured_put(self, symbol, current_price):
        """Handle cash-secured put logic.
        
        Args:
            symbol (str): ETF symbol
            current_price (float): Current price of the ETF
        """
        pos = self.positions[symbol]
        
        # If no current position, sell a new put
        if pos['current_strike'] is None:
            # Set strike price slightly below current price (95% of current)
            strike_price = round(current_price * 0.95, 2)
            premium = round(strike_price * 0.02, 2)  # 2% premium
            
            # Check if we have enough capital for cash-secured put
            required_capital = strike_price * 100  # 100 shares per contract
            
            if self.available_capital >= required_capital:
                # Sell the put
                pos['current_strike'] = strike_price
                pos['expiration_date'] = self.current_week + 1
                pos['option_premium_collected'] += premium
                
                # Update capital with premium received
                self.update_capital(premium, "Put premium collected")
                self.total_premiums_collected += premium
                
                # Log the put sale
                self.log_trade({
                    'symbol': symbol,
                    'action': 'SELL_PUT',
                    'quantity': 1,  # 1 contract
                    'price': premium,
                    'strike': strike_price,
                    'total_value': premium,
                    'notes': f'Sold put with strike ${strike_price}'
                })
                
                print(f"{symbol}: Sold put with strike ${strike_price}, premium ${premium}")
        
        # Check for assignment at expiration
        elif self.current_week >= pos['expiration_date']:
            next_week_price = self._get_next_week_price(symbol)
            
            if next_week_price < pos['current_strike']:
                # Put is assigned - buy shares
                self._assign_put(symbol)
            else:
                # Put expires worthless - reset for next cycle
                print(f"{symbol}: Put expired worthless, keeping premium ${pos['option_premium_collected']}")
                pos['current_strike'] = None
                pos['expiration_date'] = None
    
    def _assign_put(self, symbol):
        """Handle put assignment - buy shares at strike price.
        
        Args:
            symbol (str): ETF symbol
        """
        pos = self.positions[symbol]
        strike_price = pos['current_strike']
        cost = strike_price * 100  # 100 shares
        
        # Buy the shares
        pos['shares'] = 100
        pos['cost_basis'] = strike_price
        pos['state'] = WheelState.HOLDING_SHARES
        pos['current_strike'] = None
        pos['expiration_date'] = None
        
        # Update capital - subtract share cost
        self.update_capital(-cost, "Share purchase (put assignment)")
        
        # Log the share purchase
        self.log_trade({
            'symbol': symbol,
            'action': 'BUY_SHARES',
            'quantity': 100,
            'price': strike_price,
            'total_value': -cost,  # Negative for cash outflow
            'notes': f'Put assigned, bought 100 shares at ${strike_price}'
        })
        
        print(f"{symbol}: Put assigned! Bought 100 shares at ${strike_price}")
    
    def _handle_covered_call(self, symbol, current_price):
        """Handle covered call logic.
        
        Args:
            symbol (str): ETF symbol
            current_price (float): Current price of the ETF
        """
        pos = self.positions[symbol]
        
        # If no current call position, sell a new call
        if pos['current_strike'] is None:
            # Set strike price slightly above current price (105% of current)
            strike_price = round(current_price * 1.05, 2)
            premium = round(strike_price * 0.015, 2)  # 1.5% premium
            
            # Sell the call
            pos['current_strike'] = strike_price
            pos['expiration_date'] = self.current_week + 1
            pos['option_premium_collected'] += premium
            
            # Update capital with premium received
            self.update_capital(premium, "Call premium collected")
            self.total_premiums_collected += premium
            
            # Log the call sale
            self.log_trade({
                'symbol': symbol,
                'action': 'SELL_CALL',
                'quantity': 1,  # 1 contract
                'price': premium,
                'strike': strike_price,
                'total_value': premium,
                'notes': f'Sold call with strike ${strike_price}'
            })
            
            print(f"{symbol}: Sold call with strike ${strike_price}, premium ${premium}")
        
        # Check for exercise at expiration
        elif self.current_week >= pos['expiration_date']:
            next_week_price = self._get_next_week_price(symbol)
            
            if next_week_price > pos['current_strike']:
                # Call is exercised - sell shares
                self._exercise_call(symbol)
            else:
                # Call expires worthless - reset for next cycle
                print(f"{symbol}: Call expired worthless, keeping premium")
                pos['current_strike'] = None
                pos['expiration_date'] = None
    
    def _exercise_call(self, symbol):
        """Handle call exercise - sell shares at strike price.
        
        Args:
            symbol (str): ETF symbol
        """
        pos = self.positions[symbol]
        strike_price = pos['current_strike']
        proceeds = strike_price * 100  # 100 shares
        
        # Calculate profit/loss
        total_cost = pos['cost_basis'] * 100
        capital_gain = proceeds - total_cost
        total_premiums = pos['option_premium_collected']
        
        # Update capital - add proceeds from share sale
        self.update_capital(proceeds, "Share sale (call exercise)")
        
        # Track realized gains
        self.realized_gains += capital_gain
        
        # Sell the shares
        pos['shares'] = 0
        pos['cost_basis'] = 0.0
        pos['state'] = WheelState.CASH_SECURED_PUT  # Reset to CSP state
        pos['current_strike'] = None
        pos['expiration_date'] = None
        
        # Log the share sale
        self.log_trade({
            'symbol': symbol,
            'action': 'SELL_SHARES',
            'quantity': 100,
            'price': strike_price,
            'total_value': proceeds,
            'notes': f'Call exercised, sold 100 shares at ${strike_price}. Capital gain: ${capital_gain:.2f}, Total premiums: ${total_premiums:.2f}'
        })
        
        print(f"{symbol}: Call exercised! Sold 100 shares at ${strike_price}")
        print(f"  Capital gain: ${capital_gain:.2f}, Total premiums: ${total_premiums:.2f}")
        
        # Reset premium tracking for next wheel cycle
        pos['option_premium_collected'] = 0.0
    
    def _get_next_week_price(self, symbol):
        """Get next week's price for assignment/exercise checking.
        
        Args:
            symbol (str): ETF symbol
            
        Returns:
            float: Next week's price
        """
        next_week = self.current_week + 1
        if symbol in self.prices and next_week < len(self.prices[symbol]):
            return self.prices[symbol][next_week]
        return self.get_current_price(symbol)  # Fallback to current price
        
    def log_trade(self, trade_data):
        """Log a trade to the trades list with standardized format.
        
        Args:
            trade_data (dict): Trade information
        """
        # Standardized trade record structure
        trade_record = {
            'week': f"Week{self.current_week}",
            'strategy': 'Wheel',
            'symbol': trade_data.get('symbol', ''),
            'action': trade_data.get('action', ''),
            'quantity': trade_data.get('quantity', 0),
            'price': trade_data.get('price', 0.0),
            'strike': trade_data.get('strike', ''),
            'cash_flow': trade_data.get('total_value', 0.0),
            'notes': trade_data.get('notes', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        self.trades.append(trade_record)
    
    def export_trades_to_csv(self, filename='trades.csv'):
        """Export trades to CSV file.
        
        Args:
            filename (str): CSV filename
        """
        if not self.trades:
            print("No trades to export.")
            return
        
        fieldnames = ['week', 'strategy', 'symbol', 'action', 'quantity', 'price', 'strike', 'cash_flow', 'notes', 'timestamp']
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.trades)
        
        print(f"Exported {len(self.trades)} trades to {filename}")
    
    def print_trades_summary(self):
        """Print a summary of all trades."""
        if not self.trades:
            print("No trades recorded.")
            return
        
        print(f"\n=== TRADES SUMMARY ({len(self.trades)} trades) ===")
        for trade in self.trades:
            cash_flow_str = f"${trade['cash_flow']:+.2f}" if trade['cash_flow'] != 0 else ""
            strike_str = f" @ ${trade['strike']}" if trade['strike'] else ""
            print(f"{trade['week']}: {trade['action']} {trade['quantity']} {trade['symbol']}{strike_str} - {cash_flow_str}")
            if trade['notes']:
                print(f"    Note: {trade['notes']}")
        
        # Summary by action type
        actions = {}
        total_cash_flow = 0
        for trade in self.trades:
            action = trade['action']
            actions[action] = actions.get(action, 0) + 1
            total_cash_flow += trade['cash_flow']
        
        print(f"\nACTION SUMMARY:")
        for action, count in actions.items():
            print(f"  {action}: {count}")
        print(f"Net Cash Flow: ${total_cash_flow:.2f}")


if __name__ == "__main__":
    """Self-test module for wheel strategy."""
    print("="*60)
    print("WHEEL STRATEGY SELF-TEST")
    print("="*60)
    
    # Test configuration
    test_capital = 50000  # $50k for testing
    test_symbols = ["SPY"]  # Test with single symbol first
    
    print(f"Testing with ${test_capital:,} capital on {test_symbols}")
    
    # Create and run strategy
    strategy = WheelStrategy(
        capital=test_capital,
        symbols=test_symbols,
        config={'test_mode': True}
    )
    
    # Display initial mock prices for verification
    print(f"\nGenerated Mock Prices for {test_symbols[0]}:")
    for week, price in enumerate(strategy.prices[test_symbols[0]]):
        print(f"  Week {week}: ${price}")
    
    # Execute strategy
    print(f"\n" + "="*40)
    print("EXECUTING STRATEGY")
    print("="*40)
    trades = strategy.run(backtest=True)
    print(f"Strategy returned {len(trades)} trades")
    
    print(f"\n" + "="*40)
    print("SELF-TEST COMPLETE")
    print("="*40)