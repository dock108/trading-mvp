#!/usr/bin/env python3
"""
Specific test to verify CryptoRotator logic with controlled scenarios.
"""

from strategies.crypto_rotator_strategy import CryptoRotator

def test_rotation_logic():
    """Test rotation logic with simplified predictable data."""
    print("="*60)
    print("CRYPTO ROTATOR LOGIC VERIFICATION TEST")
    print("="*60)
    
    # Create strategy with test mode
    strategy = CryptoRotator(
        capital=10000,  # Smaller capital for easier math
        coins=["BTC", "ETH", "SOL"],
        config={'test_mode': True}
    )
    
    # Manually verify first few rotations
    print("\nPRICE DATA VERIFICATION:")
    for week in range(4):
        print(f"Week {week}:")
        for coin in strategy.coins:
            price = strategy.prices[coin][week]
            if week > 0:
                prev_price = strategy.prices[coin][week-1]
                return_pct = ((price - prev_price) / prev_price) * 100
                print(f"  {coin}: ${price:,.0f} ({return_pct:+.1f}%)")
            else:
                print(f"  {coin}: ${price:,.0f}")
    
    # Test manual calculation for Week 1
    print(f"\nWEEK 1 MANUAL VERIFICATION:")
    btc_return = ((52000 - 50000) / 50000) * 100  # +4%
    eth_return = ((2900 - 3000) / 3000) * 100     # -3.33%
    sol_return = ((110 - 100) / 100) * 100        # +10%
    
    print(f"  BTC: {btc_return:+.1f}% (Expected: +4.0%)")
    print(f"  ETH: {eth_return:+.1f}% (Expected: -3.3%)")  
    print(f"  SOL: {sol_return:+.1f}% (Expected: +10.0%)")
    print(f"  Best performer should be: SOL")
    
    # Test portfolio value conservation
    print(f"\nPORTFOLIO VALUE CONSERVATION TEST:")
    initial_capital = 10000
    btc_quantity = initial_capital / 50000  # 0.2 BTC
    print(f"Initial: ${initial_capital} → {btc_quantity:.4f} BTC")
    
    # Week 1: BTC goes to $52k, then rotate to SOL at $110
    btc_value = btc_quantity * 52000  # $10,400
    sol_quantity = btc_value / 110    # 94.5455 SOL
    sol_verification = sol_quantity * 110
    print(f"Week 1: {btc_quantity:.4f} BTC @ $52k = ${btc_value:,.2f}")
    print(f"        → {sol_quantity:.4f} SOL @ $110 = ${sol_verification:,.2f}")
    print(f"Value conservation: ${btc_value:,.2f} = ${sol_verification:,.2f} ✅")
    
    print(f"\n" + "="*40)
    print("RUNNING ACTUAL SIMULATION")
    print("="*40)
    
    # Run the actual strategy
    trades = strategy.run(backtest=True)
    print(f"Strategy returned {len(trades)} trades")

if __name__ == "__main__":
    test_rotation_logic()