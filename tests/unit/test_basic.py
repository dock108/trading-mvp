"""
Basic tests to verify the testing infrastructure is working correctly.
"""

import pytest
import sys
import os


def test_basic_assertions():
    """Test basic assertions work."""
    assert True
    assert 1 + 1 == 2
    assert "hello" == "hello"


def test_imports():
    """Test that we can import our modules."""
    # Test importing strategies
    try:
        from strategies import wheel_strategy, crypto_rotator_strategy
        assert wheel_strategy is not None
        assert crypto_rotator_strategy is not None
    except ImportError as e:
        pytest.fail(f"Failed to import strategies: {e}")
    
    # Test importing data modules
    try:
        from data import price_fetcher
        assert price_fetcher is not None
    except ImportError as e:
        pytest.fail(f"Failed to import data modules: {e}")


def test_fixtures(sample_config, mock_price_data):
    """Test that fixtures are working correctly."""
    assert sample_config is not None
    assert isinstance(sample_config, dict)
    assert 'initial_capital' in sample_config
    
    assert mock_price_data is not None
    assert isinstance(mock_price_data, dict)
    assert 'SPY' in mock_price_data


def test_temp_db_fixture(temp_db):
    """Test that temporary database fixture works."""
    import sqlite3
    
    # Should be able to connect to the temp database
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Check that tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_names = [table[0] for table in tables]
    
    assert 'trades' in table_names
    assert 'prices' in table_names
    
    conn.close()


@pytest.mark.parametrize("symbol,expected_type", [
    ('SPY', str),
    ('BTC', str),
    ('QQQ', str),
])
def test_parametrized_test(symbol, expected_type):
    """Test parametrized testing works."""
    assert isinstance(symbol, expected_type)


def test_environment_setup():
    """Test that the test environment is set up correctly."""
    # Check Python version
    assert sys.version_info >= (3, 8)
    
    # Check that we're in the right directory
    cwd = os.getcwd()
    assert 'trading_mvp' in cwd


class TestClassExample:
    """Example test class to verify class-based testing works."""
    
    def test_class_method(self):
        """Test method within a class."""
        assert True
    
    def test_class_with_fixture(self, sample_config):
        """Test that fixtures work within test classes."""
        assert sample_config['initial_capital'] == 100000