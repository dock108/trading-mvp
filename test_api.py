#!/usr/bin/env python3
"""
Test script for the FastAPI backend
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Health check: {response.status_code}")
    print(f"Response: {response.json()}")

def test_config():
    """Test config endpoint"""
    response = requests.get(f"{BASE_URL}/api/config")
    print(f"Config: {response.status_code}")
    if response.status_code == 200:
        config = response.json()
        print(f"Data mode: {config.get('data_mode')}")
        print(f"Strategies: {config.get('strategies')}")
    else:
        print(f"Error: {response.text}")

def test_run_strategies():
    """Test strategy execution"""
    payload = {
        "strategies": ["wheel"],
        "backtest": True
    }
    
    print(f"Testing strategy execution...")
    response = requests.post(
        f"{BASE_URL}/api/run",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")

if __name__ == "__main__":
    test_health()
    print()
    test_config()
    print()
    test_run_strategies()