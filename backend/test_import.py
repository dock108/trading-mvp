#!/usr/bin/env python3
"""
Test importing strategy modules from the backend context
"""

import sys
import os

# Add parent directories to Python path to import trading modules
# __file__ is in backend/test_import.py
# We want to get to trading_mvp/ directory
current_dir = os.path.dirname(__file__)  # backend/
trading_mvp_dir = os.path.dirname(current_dir)  # trading_mvp/
sys.path.insert(0, trading_mvp_dir)

print(f"Current dir: {current_dir}")
print(f"Trading MVP dir: {trading_mvp_dir}")
print(f"Python path: {sys.path[:3]}")

try:
    from strategies.wheel_strategy import WheelStrategy
    print("✅ WheelStrategy import successful")
    
    # Test initialization
    config = {
        'data_mode': 'mock',
        'backtest_mode': True,
        'test_mode': True,
        'allocation': {'wheel': 0.5},
        'initial_capital': 100000
    }
    
    strategy = WheelStrategy(
        capital=50000,
        symbols=['SPY'],
        config=config,
        price_fetcher=None
    )
    print("✅ WheelStrategy initialization successful")
    
    # Test run
    trades = strategy.run(backtest=True)
    print(f"✅ WheelStrategy run successful: {len(trades)} trades")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()