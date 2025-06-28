#!/usr/bin/env python3
"""
Test alternative stock APIs that might work
"""

import requests
import json
from datetime import datetime, timedelta

def test_stock_apis():
    """Test free stock APIs"""
    
    print("=== Testing Alternative Stock APIs ===\n")
    
    # 1. Test marketstack (free tier)
    print("1. Testing Marketstack API:")
    try:
        url = "http://api.marketstack.com/v1/eod"
        params = {
            "access_key": "demo",  # Free demo
            "symbols": "SPY",
            "limit": 5
        }
        response = requests.get(url, params=params, timeout=10)
        print(f"Marketstack response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Marketstack success: {data}")
        else:
            print(f"❌ Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # 2. Test IEX Cloud (has free tier)
    print("2. Testing IEX Cloud:")
    try:
        url = "https://cloud.iexapis.com/stable/stock/SPY/quote"
        params = {"token": "demo"}  # This won't work but let's see
        response = requests.get(url, params=params, timeout=10)
        print(f"IEX response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ IEX success: {data}")
        else:
            print(f"❌ IEX Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # 3. Test Finnhub (free tier)
    print("3. Testing Finnhub (free tier):")
    try:
        url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": "SPY",
            "token": "demo"  # This won't work
        }
        response = requests.get(url, params=params, timeout=10)
        print(f"Finnhub response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Finnhub success: {data}")
        else:
            print(f"❌ Finnhub Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # 4. Test using different yfinance approach
    print("4. Testing yfinance with different parameters:")
    try:
        import yfinance as yf
        
        # Try different approaches
        ticker = yf.Ticker("SPY")
        
        # Try with progress=False and different period
        print("  Trying 5d period...")
        data1 = ticker.history(period="5d", progress=False, auto_adjust=False)
        print(f"  5d result: shape={data1.shape}, empty={data1.empty}")
        
        print("  Trying max period...")
        data2 = ticker.history(period="max", progress=False)
        print(f"  max result: shape={data2.shape}, empty={data2.empty}")
        
        if not data2.empty:
            recent = data2.tail(5)['Close'].tolist()
            print(f"  ✅ Recent prices: {recent}")
        
    except Exception as e:
        print(f"❌ yfinance Error: {e}")

if __name__ == "__main__":
    test_stock_apis()