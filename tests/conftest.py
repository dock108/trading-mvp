"""
Pytest configuration and shared fixtures for the test suite.

This module provides common fixtures and test utilities used across
unit and integration tests.
"""

import os
import sqlite3
import tempfile
import pytest
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Initialize database
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            strategy TEXT NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            cash_flow REAL NOT NULL,
            notes TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            volume REAL,
            source TEXT
        )
    ''')
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Provide a sample configuration for testing."""
    return {
        'initial_capital': 100000,
        'data_mode': 'mock',
        'strategies': {
            'wheel': True,
            'rotator': True
        },
        'allocation': {
            'wheel': 0.5,
            'rotator': 0.5
        },
        'wheel_symbols': ['SPY', 'QQQ', 'IWM'],
        'rotator_symbols': ['BTC', 'ETH', 'SOL'],
        'simulation': {
            'weeks_to_simulate': 4,
            'enable_deterministic_mode': True
        }
    }


@pytest.fixture
def temp_config_file(sample_config, tmp_path):
    """Create a temporary YAML config file."""
    import yaml
    
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(sample_config, f)
    
    return str(config_file)


@pytest.fixture
def mock_price_data():
    """Provide mock price data for testing."""
    return {
        'SPY': [450.0, 452.0, 448.0, 455.0, 453.0],
        'QQQ': [380.0, 382.0, 378.0, 385.0, 383.0],
        'IWM': [200.0, 202.0, 198.0, 205.0, 203.0],
        'BTC': [50000.0, 51000.0, 49000.0, 52000.0, 51500.0],
        'ETH': [3000.0, 3100.0, 2900.0, 3200.0, 3150.0],
        'SOL': [100.0, 105.0, 95.0, 110.0, 108.0]
    }


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_file = tmp_path / "test_trades.csv"
    # Create empty CSV with headers
    csv_file.write_text("Week,Strategy,Asset,Action,Quantity,Price,Amount\n")
    return str(csv_file)


class MockPriceFetcher:
    """Mock price fetcher for testing."""
    
    def __init__(self, mock_data):
        self.mock_data = mock_data
        self.call_count = 0
    
    def get_price(self, symbol: str) -> float:
        """Get mock price for symbol."""
        self.call_count += 1
        if symbol in self.mock_data:
            # Return different prices based on call count for time series
            prices = self.mock_data[symbol]
            return prices[self.call_count % len(prices)]
        return 100.0  # Default price
    
    async def get_price_async(self, symbol: str) -> float:
        """Async version of get_price."""
        return self.get_price(symbol)


@pytest.fixture
def mock_price_fetcher(mock_price_data):
    """Provide a mock price fetcher instance."""
    return MockPriceFetcher(mock_price_data)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "async_test: mark test as requiring async support"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow-running"
    )