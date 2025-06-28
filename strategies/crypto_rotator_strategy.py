"""
Crypto Rotator Strategy implementation.

This module simulates a cryptocurrency rotation strategy on BTC, ETH, SOL.
The strategy rotates between cryptocurrencies based on performance metrics.
"""

import csv
import pandas as pd
from datetime import datetime
import random

class CryptoRotator:
    """Crypto Rotator Strategy for cryptocurrencies."""
    
    def __init__(self, capital, coins, config=None):
        """Initialize the crypto rotator strategy.
        
        Args:
            capital (float): Capital allocated to this strategy
            coins (list): List of crypto symbols (e.g., ['BTC', 'ETH', 'SOL'])
            config (dict): Additional configuration parameters
        """
        self.initial_capital = capital
        self.capital = capital
        self.coins = coins
        self.config = config or {}
        self.trades = []
        
        # Current holding tracking
        self.current_holding = None  # Which crypto we currently hold
        self.current_quantity = 0.0  # How much of that crypto we own
        self.current_value = 0.0     # Current USD value of holdings
        
        # Mock price data for simulation
        self.prices = self._generate_mock_prices()
        self.current_week = 0
        
        # Performance tracking
        self.weekly_returns = {}  # Track weekly returns for each coin
        self.total_return = 0.0
        self.portfolio_history = []  # Track portfolio value over time
        self.realized_pnl = 0.0      # Track realized gains/losses from trades
    
    def _generate_mock_prices(self):
        """Generate mock price data for crypto simulation.
        
        Returns:
            dict: Weekly prices for each crypto
        """
        # Use test mode for deterministic rotation demonstration
        if self.config.get('test_mode', False):
            # Create deterministic price sequences to force rotations
            prices = {
                "BTC": [50000, 52000, 48000, 51000, 49000, 53000, 47000, 55000, 50000],  # 9 weeks
                "ETH": [3000, 2900, 3200, 3100, 3400, 3000, 3500, 3200, 3300],
                "SOL": [100, 110, 95, 105, 120, 90, 115, 105, 125]
            }
            
            # Ensure all coins have same length
            for coin in self.coins:
                if coin not in prices:
                    prices[coin] = [1000] * 9  # Default fallback
            
            return prices
        else:
            # Starting prices based on realistic crypto values
            base_prices = {
                "BTC": 50000,   # Bitcoin around $50k
                "ETH": 3000,    # Ethereum around $3k  
                "SOL": 100      # Solana around $100
            }
            
            prices = {}
            random.seed(123)  # Different seed than wheel strategy
            
            for coin in self.coins:
                base_price = base_prices.get(coin, 1000)
                weekly_prices = [base_price]
                
                # Generate 8 weeks of price movements (-10% to +15% weekly for crypto volatility)
                for week in range(8):
                    price_change = random.uniform(-0.10, 0.15)
                    new_price = weekly_prices[-1] * (1 + price_change)
                    weekly_prices.append(round(new_price, 2))
                
                prices[coin] = weekly_prices
                
            return prices
    
    def get_current_price(self, coin):
        """Get current price for a coin.
        
        Args:
            coin (str): Crypto symbol
            
        Returns:
            float: Current price
        """
        if coin in self.prices and self.current_week < len(self.prices[coin]):
            return self.prices[coin][self.current_week]
        return 0.0
    
    def get_current_portfolio_value(self):
        """Get current portfolio value in USD.
        
        Returns:
            float: Current portfolio value
        """
        if self.current_holding is None:
            return self.capital  # All in cash
        
        current_price = self.get_current_price(self.current_holding)
        self.current_value = self.current_quantity * current_price
        return self.current_value
    
    def update_portfolio_value(self):
        """Update portfolio value based on current holdings and prices."""
        previous_value = self.current_value if hasattr(self, 'current_value') else self.initial_capital
        current_value = self.get_current_portfolio_value()
        
        # Track value change
        value_change = current_value - previous_value if previous_value > 0 else 0
        
        # Record portfolio history
        self.portfolio_history.append({
            'week': self.current_week,
            'holding': self.current_holding,
            'quantity': self.current_quantity,
            'price': self.get_current_price(self.current_holding) if self.current_holding else 0,
            'value': current_value,
            'change': value_change
        })
        
        return current_value
    
    def get_unrealized_pnl(self):
        """Calculate unrealized P&L for current holdings.
        
        Returns:
            float: Unrealized profit/loss
        """
        if self.current_holding is None:
            return 0.0
        
        current_value = self.get_current_portfolio_value()
        # Find the cost basis (last purchase amount)
        for trade in reversed(self.trades):
            if trade['action'] == 'BUY_CRYPTO' and trade['symbol'] == self.current_holding:
                cost_basis = abs(trade['cash_flow'])
                return current_value - cost_basis
        
        return 0.0
    
    def calculate_weekly_returns(self):
        """Calculate weekly returns for all coins for current week.
        
        Returns:
            dict: Weekly returns for each coin {coin: return_pct}
        """
        if self.current_week == 0:
            # No prior week for comparison
            return {coin: 0.0 for coin in self.coins}
        
        weekly_returns = {}
        for coin in self.coins:
            current_price = self.get_current_price(coin)
            prev_price = self.prices[coin][self.current_week - 1]
            
            if prev_price > 0:
                weekly_return = (current_price - prev_price) / prev_price
                weekly_returns[coin] = weekly_return
            else:
                weekly_returns[coin] = 0.0
        
        self.weekly_returns = weekly_returns
        return weekly_returns
    
    def get_best_performer(self):
        """Identify the best performing coin from last week's returns.
        
        Returns:
            str: Symbol of best performing coin
        """
        if not self.weekly_returns:
            # First week - choose first coin as default
            return self.coins[0]
        
        # Find coin with highest return
        best_coin = max(self.weekly_returns.items(), key=lambda x: x[1])
        return best_coin[0]
    
    def advance_week(self):
        """Advance to the next week in the simulation."""
        self.current_week += 1
        print(f"\n--- Week {self.current_week} ---")
        
        # Display current prices
        for coin in self.coins:
            price = self.get_current_price(coin)
            print(f"{coin}: ${price:,.2f}")
        
        # Calculate and display weekly returns
        if self.current_week > 0:
            returns = self.calculate_weekly_returns()
            print("Weekly Returns:")
            for coin, return_pct in returns.items():
                print(f"  {coin}: {return_pct:+.2%}")
            
            best_performer = self.get_best_performer()
            print(f"Best Performer: {best_performer} ({returns[best_performer]:+.2%})")
    
    def run(self, backtest=True):
        """Run the crypto rotator strategy simulation.
        
        Args:
            backtest (bool): Whether to run in backtest mode with deterministic data
            
        Returns:
            list: List of trade records
        """
        print(f"Executing Crypto Rotator Strategy with ${self.capital:,.2f}")
        print(f"Trading coins: {self.coins}")
        
        # Display initial prices
        print(f"\n--- Week {self.current_week} (Start) ---")
        for coin in self.coins:
            price = self.get_current_price(coin)
            print(f"{coin}: ${price:,.2f}")
        
        print(f"Initial Portfolio: ${self.get_current_portfolio_value():,.2f}")
        
        # Run simulation for 8 weeks
        for week in range(8):
            if week > 0:
                self.advance_week()
            
            # Process rotation logic
            self._process_weekly_rotation()
            
            # Update portfolio value and track changes
            current_value = self.update_portfolio_value()
            unrealized_pnl = self.get_unrealized_pnl()
            
            if self.current_holding:
                print(f"Portfolio: {self.current_quantity:.4f} {self.current_holding} = ${current_value:,.2f} (Unrealized P&L: ${unrealized_pnl:+,.2f})")
            else:
                print(f"Portfolio Value: ${current_value:,.2f} (Cash)")
        
        # Final summary
        final_value = self.get_current_portfolio_value()
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
        final_unrealized = self.get_unrealized_pnl()
        
        print(f"\n=== ROTATOR SIMULATION COMPLETE ===")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Portfolio Value: ${final_value:,.2f}")
        print(f"Total Return: {total_return:+.2f}%")
        print(f"Realized P&L: ${self.realized_pnl:+,.2f}")
        print(f"Unrealized P&L: ${final_unrealized:+,.2f}")
        print(f"Total Trades: {len(self.trades)}")
        
        # Print portfolio evolution
        self._print_portfolio_summary()
        
        # Print trades summary and export to CSV
        self.print_trades_summary()
        self.export_trades_to_csv()
        
        # Return trade list for main coordination
        return self.trades
    
    def _print_portfolio_summary(self):
        """Print a summary of portfolio value evolution."""
        print(f"\n=== PORTFOLIO EVOLUTION ===")
        for entry in self.portfolio_history:
            if entry['holding']:
                change_str = f" ({entry['change']:+,.2f})" if entry['change'] != 0 else ""
                print(f"Week {entry['week']}: {entry['quantity']:.4f} {entry['holding']} @ ${entry['price']:.2f} = ${entry['value']:,.2f}{change_str}")
            else:
                print(f"Week {entry['week']}: Cash = ${entry['value']:,.2f}")
        
        # Show best and worst weeks
        if len(self.portfolio_history) > 1:
            best_week = max(self.portfolio_history[1:], key=lambda x: x['change'])
            worst_week = min(self.portfolio_history[1:], key=lambda x: x['change'])
            print(f"\nBest Week: Week {best_week['week']} (+${best_week['change']:,.2f})")
            print(f"Worst Week: Week {worst_week['week']} ({worst_week['change']:+,.2f})")
    
    def _process_weekly_rotation(self):
        """Process weekly rotation logic based on performance."""
        if self.current_week == 0:
            # First week - make initial allocation to first coin (no performance data yet)
            initial_coin = self.coins[0]  # Default to BTC
            self._buy_crypto(initial_coin)
        else:
            # Calculate performance and identify best performer
            returns = self.calculate_weekly_returns()
            best_performer = self.get_best_performer()
            
            if self.current_holding is None:
                # No current holding, buy best performer
                self._buy_crypto(best_performer)
            elif self.current_holding != best_performer:
                # Rotate: sell current holding and buy best performer
                print(f"Rotating from {self.current_holding} to {best_performer}")
                self._sell_crypto()
                self._buy_crypto(best_performer)
            else:
                # Stay with current holding
                print(f"Staying with {self.current_holding} (still top performer)")
    
    def _buy_crypto(self, coin):
        """Buy crypto with all available capital.
        
        Args:
            coin (str): Crypto symbol to buy
        """
        price = self.get_current_price(coin)
        if price <= 0:
            print(f"Error: Invalid price for {coin}")
            return
        
        # Use all available capital to buy
        available_capital = self.capital if self.current_holding is None else self.current_value
        quantity = available_capital / price
        
        # Update holdings
        self.current_holding = coin
        self.current_quantity = quantity
        self.current_value = available_capital
        
        # Log the trade
        self.log_trade({
            'symbol': coin,
            'action': 'BUY_CRYPTO',
            'quantity': quantity,
            'price': price,
            'total_value': -available_capital,  # Negative for cash outflow
            'notes': f'Bought {quantity:.4f} {coin} @ ${price:.2f}'
        })
        
        print(f"Bought {quantity:.4f} {coin} @ ${price:.2f} (${available_capital:,.2f})")
    
    def _sell_crypto(self):
        """Sell all current crypto holdings."""
        if self.current_holding is None or self.current_quantity <= 0:
            print("No crypto to sell")
            return
        
        coin = self.current_holding
        price = self.get_current_price(coin)
        quantity = self.current_quantity
        proceeds = quantity * price
        
        # Log the trade
        self.log_trade({
            'symbol': coin,
            'action': 'SELL_CRYPTO',
            'quantity': quantity,
            'price': price,
            'total_value': proceeds,  # Positive for cash inflow
            'notes': f'Sold {quantity:.4f} {coin} @ ${price:.2f}'
        })
        
        print(f"Sold {quantity:.4f} {coin} @ ${price:.2f} (${proceeds:,.2f})")
        
        # Calculate realized P&L from this trade
        # Find the corresponding buy trade for this holding
        for trade in reversed(self.trades):
            if trade['action'] == 'BUY_CRYPTO' and trade['symbol'] == coin:
                cost_basis = abs(trade['cash_flow'])
                realized_gain = proceeds - cost_basis
                self.realized_pnl += realized_gain
                print(f"Realized P&L: ${realized_gain:+,.2f} (Cost: ${cost_basis:,.2f}, Proceeds: ${proceeds:,.2f})")
                break
        
        # Update holdings - convert to cash
        self.capital = proceeds
        self.current_holding = None
        self.current_quantity = 0.0
        self.current_value = proceeds
        
    def log_trade(self, trade_data):
        """Log a trade to the trades list with standardized format.
        
        Args:
            trade_data (dict): Trade information
        """
        # Standardized trade record structure
        trade_record = {
            'week': f"Week{self.current_week}",
            'strategy': 'Rotator',
            'symbol': trade_data.get('symbol', ''),
            'action': trade_data.get('action', ''),
            'quantity': trade_data.get('quantity', 0),
            'price': trade_data.get('price', 0.0),
            'strike': '',  # Not applicable for crypto
            'cash_flow': trade_data.get('total_value', 0.0),
            'notes': trade_data.get('notes', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        self.trades.append(trade_record)
    
    def export_trades_to_csv(self, filename='trades.csv'):
        """Export trades to CSV file (append mode for multi-strategy).
        
        Args:
            filename (str): CSV filename
        """
        if not self.trades:
            print("No rotator trades to export.")
            return
        
        fieldnames = ['week', 'strategy', 'symbol', 'action', 'quantity', 'price', 'strike', 'cash_flow', 'notes', 'timestamp']
        
        # Append to existing trades.csv (wheel strategy may have created it)
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Only write header if file is empty/new
            csvfile.seek(0, 2)  # Go to end of file
            if csvfile.tell() == 0:
                writer.writeheader()
            
            writer.writerows(self.trades)
        
        print(f"Exported {len(self.trades)} rotator trades to {filename}")
    
    def print_trades_summary(self):
        """Print a summary of all rotator trades."""
        if not self.trades:
            print("No rotator trades recorded.")
            return
        
        print(f"\n=== ROTATOR TRADES SUMMARY ({len(self.trades)} trades) ===")
        for trade in self.trades:
            cash_flow_str = f"${trade['cash_flow']:+.2f}" if trade['cash_flow'] != 0 else ""
            print(f"{trade['week']}: {trade['action']} {trade['quantity']:.4f} {trade['symbol']} @ ${trade['price']:.2f} - {cash_flow_str}")
            if trade['notes']:
                print(f"    Note: {trade['notes']}")
        
        # Summary by action type
        actions = {}
        total_cash_flow = 0
        for trade in self.trades:
            action = trade['action']
            actions[action] = actions.get(action, 0) + 1
            total_cash_flow += trade['cash_flow']
        
        print(f"\nROTATOR ACTION SUMMARY:")
        for action, count in actions.items():
            print(f"  {action}: {count}")
        print(f"Net Cash Flow: ${total_cash_flow:.2f}")


# For backward compatibility with old import
CryptoRotatorStrategy = CryptoRotator


if __name__ == "__main__":
    """Self-test module for crypto rotator strategy."""
    print("="*60)
    print("CRYPTO ROTATOR STRATEGY SELF-TEST")
    print("="*60)
    
    # Test configuration
    test_capital = 50000  # $50k for testing
    test_coins = ["BTC", "ETH", "SOL"]
    
    print(f"Testing with ${test_capital:,} capital on {test_coins}")
    
    # Create and run strategy
    strategy = CryptoRotator(
        capital=test_capital,
        coins=test_coins,
        config={'test_mode': True}
    )
    
    # Display initial mock prices for verification
    print(f"\nGenerated Mock Prices:")
    for coin in test_coins:
        prices_str = ", ".join([f"${p:,.0f}" for p in strategy.prices[coin]])
        print(f"  {coin}: {prices_str}")
    
    # Execute strategy
    print(f"\n" + "="*40)
    print("EXECUTING STRATEGY")
    print("="*40)
    trades = strategy.run(backtest=True)
    print(f"Strategy returned {len(trades)} trades")
    
    print(f"\n" + "="*40)
    print("SELF-TEST COMPLETE")
    print("="*40)