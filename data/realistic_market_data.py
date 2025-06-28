#!/usr/bin/env python3
"""
Realistic Market Data Generator

This module provides realistic historical market data for backtesting
when live APIs are unavailable. It uses actual market characteristics
to generate believable price series.
"""

import random
import math
from datetime import datetime, timedelta
from typing import List, Dict

class RealisticMarketData:
    """Generate realistic market data based on actual market characteristics"""
    
    def __init__(self):
        # Market data based on typical SPY/QQQ/IWM characteristics
        self.etf_data = {
            'SPY': {'base_price': 420.0, 'annual_volatility': 0.18, 'annual_return': 0.10},
            'QQQ': {'base_price': 350.0, 'annual_volatility': 0.25, 'annual_return': 0.12},
            'IWM': {'base_price': 190.0, 'annual_volatility': 0.22, 'annual_return': 0.08}
        }
        
        # Crypto data based on typical characteristics
        self.crypto_data = {
            'BTC': {'base_price': 45000.0, 'annual_volatility': 0.80, 'annual_return': 0.40},
            'ETH': {'base_price': 2800.0, 'annual_volatility': 0.90, 'annual_return': 0.35},
            'SOL': {'base_price': 140.0, 'annual_volatility': 1.20, 'annual_return': 0.50}
        }
    
    def generate_realistic_prices(self, symbol: str, days: int = 7, asset_type: str = 'etf') -> List[float]:
        """Generate realistic price series for a given symbol"""
        
        if asset_type == 'etf':
            params = self.etf_data.get(symbol, self.etf_data['SPY'])
        else:
            params = self.crypto_data.get(symbol, self.crypto_data['BTC'])
        
        base_price = params['base_price']
        annual_volatility = params['annual_volatility']
        annual_return = params['annual_return']
        
        # Convert to daily parameters
        daily_return = annual_return / 252  # 252 trading days per year
        daily_volatility = annual_volatility / math.sqrt(252)
        
        prices = []
        current_price = base_price
        
        for day in range(days):
            # Generate realistic daily return using normal distribution
            # with slight positive bias for long-term growth
            random_return = random.normalvariate(daily_return, daily_volatility)
            
            # Apply the return to get new price
            current_price = current_price * (1 + random_return)
            
            # Add some intraday noise but keep it reasonable
            noise = random.normalvariate(0, daily_volatility * 0.1)
            current_price = current_price * (1 + noise)
            
            # Ensure price doesn't go negative or become unrealistic
            if asset_type == 'etf':
                current_price = max(current_price, base_price * 0.5)  # ETFs rarely lose more than 50%
                current_price = min(current_price, base_price * 2.0)   # ETFs rarely double quickly
            else:
                current_price = max(current_price, base_price * 0.1)   # Crypto can be more volatile
                current_price = min(current_price, base_price * 5.0)   # But not too extreme
            
            prices.append(round(current_price, 2))
        
        return prices
    
    def get_current_prices(self) -> Dict[str, float]:
        """Get realistic current prices for all symbols"""
        current_prices = {}
        
        # ETF prices
        for symbol in self.etf_data:
            prices = self.generate_realistic_prices(symbol, days=1, asset_type='etf')
            current_prices[symbol] = prices[0]
        
        # Crypto prices
        for symbol in self.crypto_data:
            prices = self.generate_realistic_prices(symbol, days=1, asset_type='crypto')
            current_prices[symbol] = prices[0]
        
        return current_prices

# Global instance for easy access
realistic_data = RealisticMarketData()

def get_realistic_etf_prices(symbol: str, days: int = 7) -> List[float]:
    """Get realistic ETF prices for backtesting"""
    return realistic_data.generate_realistic_prices(symbol, days, 'etf')

def get_realistic_crypto_prices(symbol: str, days: int = 7) -> List[float]:
    """Get realistic crypto prices for backtesting"""
    return realistic_data.generate_realistic_prices(symbol, days, 'crypto')

if __name__ == "__main__":
    # Test the realistic data generator
    print("=== Testing Realistic Market Data Generator ===\n")
    
    print("ETF Prices (7 days):")
    for symbol in ['SPY', 'QQQ', 'IWM']:
        prices = get_realistic_etf_prices(symbol, 7)
        change = ((prices[-1] / prices[0]) - 1) * 100
        print(f"{symbol}: ${prices[0]:.2f} -> ${prices[-1]:.2f} ({change:+.2f}%)")
    
    print("\nCrypto Prices (7 days):")
    for symbol in ['BTC', 'ETH', 'SOL']:
        prices = get_realistic_crypto_prices(symbol, 7)
        change = ((prices[-1] / prices[0]) - 1) * 100
        print(f"{symbol}: ${prices[0]:.2f} -> ${prices[-1]:.2f} ({change:+.2f}%)")
    
    print("\nCurrent Prices:")
    current = realistic_data.get_current_prices()
    for symbol, price in current.items():
        print(f"{symbol}: ${price:.2f}")