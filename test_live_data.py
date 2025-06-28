#!/usr/bin/env python3
"""
Test script to verify live data sources and create a working implementation
"""

import requests
import json
from datetime import datetime, timedelta

def test_free_apis():
    """Test free APIs that don't require keys"""
    
    print("=== Testing Free Financial APIs ===\n")
    
    # 1. Test Yahoo Finance alternative - Financial Modeling Prep (free tier)
    print("1. Testing Financial Modeling Prep (free tier):")
    try:
        url = "https://financialmodelingprep.com/api/v3/historical-price-full/SPY"
        params = {"apikey": "demo"}  # Free demo key
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'historical' in data and len(data['historical']) > 0:
                recent_prices = data['historical'][:5]
                print(f"✅ Success! Got {len(data['historical'])} historical prices for SPY")
                print(f"Recent prices: {[p['close'] for p in recent_prices]}")
            else:
                print("❌ Empty response")
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # 2. Test Alpha Vantage demo
    print("2. Testing Alpha Vantage (demo):")
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": "SPY",
            "apikey": "demo",
            "outputsize": "compact"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                recent_date = list(time_series.keys())[0]
                recent_price = float(time_series[recent_date]['4. close'])
                print(f"✅ Success! Recent SPY price: ${recent_price}")
            else:
                print(f"❌ Unexpected response: {list(data.keys())}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # 3. Test free crypto API
    print("3. Testing CoinGecko (no key required):")
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,solana",
            "vs_currencies": "usd"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Current crypto prices:")
            for coin, price_data in data.items():
                print(f"  {coin}: ${price_data['usd']:,.2f}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # 4. Test polygon.io free tier
    print("4. Testing Polygon.io (free tier):")
    try:
        # Note: Polygon free tier is quite limited, but let's try
        url = "https://api.polygon.io/v2/aggs/ticker/SPY/prev"
        params = {"apikey": "demo"}  # This won't work but let's see the error
        response = requests.get(url, params=params, timeout=10)
        print(f"Polygon response code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Polygon success: {data}")
        else:
            print(f"❌ Polygon requires paid API key")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_free_apis()