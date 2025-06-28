"""
Unit tests for the Database module.

Tests cover:
- Database initialization and schema creation
- Trade logging and retrieval
- Price data caching
- Strategy run tracking
- Data integrity and validation
"""

import pytest
import tempfile
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from data.database import TradingDatabase, DatabaseError, get_database, log_trade_to_db


class TestTradingDatabase:
    """Test suite for TradingDatabase class."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Create temporary database for each test
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_trading.db"
        self.db = TradingDatabase(self.db_path)

    def teardown_method(self):
        """Clean up after each test."""
        self.db.close()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_database_initialization(self):
        """Test that database initializes correctly with proper schema."""
        # Database file should exist
        assert self.db_path.exists()
        
        # Should be able to get connection
        conn = self.db._get_connection()
        assert conn is not None
        
        # Check that all required tables exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {'trades', 'price_cache', 'strategy_runs', 'portfolio_snapshots'}
        assert expected_tables.issubset(tables)

    def test_insert_trade_success(self):
        """Test successful trade insertion."""
        trade_data = {
            'strategy': 'wheel',
            'symbol': 'SPY',
            'action': 'SELL_PUT',
            'quantity': 1.0,
            'price': 450.0,
            'cash_flow': 5.50,
            'week': 'Week0',
            'notes': 'Test trade'
        }
        
        trade_id = self.db.insert_trade(trade_data)
        assert isinstance(trade_id, int)
        assert trade_id > 0

    def test_insert_trade_missing_required_field(self):
        """Test trade insertion with missing required field."""
        incomplete_trade = {
            'strategy': 'wheel',
            'symbol': 'SPY',
            # Missing required fields: action, quantity, price, cash_flow
        }
        
        with pytest.raises(DatabaseError, match="Missing required field"):
            self.db.insert_trade(incomplete_trade)

    def test_insert_trade_auto_timestamp(self):
        """Test that timestamp is automatically added if not provided."""
        trade_data = {
            'strategy': 'wheel',
            'symbol': 'SPY',
            'action': 'SELL_PUT',
            'quantity': 1.0,
            'price': 450.0,
            'cash_flow': 5.50
        }
        
        before_time = datetime.now(timezone.utc)
        trade_id = self.db.insert_trade(trade_data)
        after_time = datetime.now(timezone.utc)
        
        # Retrieve the trade and check timestamp
        trades = self.db.get_trades(limit=1)
        assert len(trades) == 1
        
        trade_timestamp = datetime.fromisoformat(trades[0]['timestamp'])
        assert before_time <= trade_timestamp <= after_time

    def test_get_trades_no_filter(self):
        """Test retrieving all trades without filters."""
        # Insert multiple trades
        trades_data = [
            {
                'strategy': 'wheel',
                'symbol': 'SPY',
                'action': 'SELL_PUT',
                'quantity': 1.0,
                'price': 450.0,
                'cash_flow': 5.50
            },
            {
                'strategy': 'rotator',
                'symbol': 'BTC',
                'action': 'BUY_CRYPTO',
                'quantity': 0.5,
                'price': 50000.0,
                'cash_flow': -25000.0
            }
        ]
        
        for trade_data in trades_data:
            self.db.insert_trade(trade_data)
        
        # Retrieve all trades
        all_trades = self.db.get_trades()
        assert len(all_trades) == 2

    def test_get_trades_with_filters(self):
        """Test retrieving trades with various filters."""
        # Insert test trades
        wheel_trade = {
            'strategy': 'wheel',
            'symbol': 'SPY',
            'action': 'SELL_PUT',
            'quantity': 1.0,
            'price': 450.0,
            'cash_flow': 5.50,
            'timestamp': '2023-01-01T10:00:00+00:00'
        }
        
        rotator_trade = {
            'strategy': 'rotator',
            'symbol': 'BTC',
            'action': 'BUY_CRYPTO',
            'quantity': 0.5,
            'price': 50000.0,
            'cash_flow': -25000.0,
            'timestamp': '2023-01-02T10:00:00+00:00'
        }
        
        self.db.insert_trade(wheel_trade)
        self.db.insert_trade(rotator_trade)
        
        # Test strategy filter
        wheel_trades = self.db.get_trades(strategy='wheel')
        assert len(wheel_trades) == 1
        assert wheel_trades[0]['strategy'] == 'wheel'
        
        # Test symbol filter
        spy_trades = self.db.get_trades(symbol='SPY')
        assert len(spy_trades) == 1
        assert spy_trades[0]['symbol'] == 'SPY'
        
        # Test date range filter
        filtered_trades = self.db.get_trades(
            start_date='2023-01-01T00:00:00+00:00',
            end_date='2023-01-01T23:59:59+00:00'
        )
        assert len(filtered_trades) == 1
        assert filtered_trades[0]['strategy'] == 'wheel'
        
        # Test limit
        limited_trades = self.db.get_trades(limit=1)
        assert len(limited_trades) == 1

    def test_insert_price_data(self):
        """Test price data insertion."""
        price_id = self.db.insert_price_data(
            symbol='SPY',
            timestamp='2023-01-01T10:00:00+00:00',
            price=450.0,
            volume=1000000,
            source='yfinance'
        )
        
        assert isinstance(price_id, int)
        assert price_id > 0

    def test_get_price_data(self):
        """Test price data retrieval."""
        # Insert test price data
        test_prices = [
            ('SPY', '2023-01-01T10:00:00+00:00', 450.0),
            ('SPY', '2023-01-02T10:00:00+00:00', 452.0),
            ('QQQ', '2023-01-01T10:00:00+00:00', 380.0)
        ]
        
        for symbol, timestamp, price in test_prices:
            self.db.insert_price_data(symbol, timestamp, price, source='test')
        
        # Test retrieving all SPY prices
        spy_prices = self.db.get_price_data('SPY')
        assert len(spy_prices) == 2
        
        # Test date range filter
        filtered_prices = self.db.get_price_data(
            'SPY',
            start_date='2023-01-01T00:00:00+00:00',
            end_date='2023-01-01T23:59:59+00:00'
        )
        assert len(filtered_prices) == 1

    def test_strategy_run_tracking(self):
        """Test strategy run start and completion tracking."""
        run_id = "test_run_123"
        config = {"initial_capital": 100000, "strategies": {"wheel": True}}
        strategies = ["wheel"]
        
        # Start strategy run
        run_record_id = self.db.start_strategy_run(run_id, config, strategies)
        assert isinstance(run_record_id, int)
        
        # Complete strategy run
        self.db.complete_strategy_run(
            run_id=run_id,
            total_trades=5,
            final_capital=105000.0
        )
        
        # Verify the run was recorded correctly
        conn = self.db._get_connection()
        cursor = conn.execute(
            "SELECT * FROM strategy_runs WHERE run_id = ?", 
            (run_id,)
        )
        run_record = cursor.fetchone()
        
        assert run_record is not None
        assert run_record['run_id'] == run_id
        assert run_record['status'] == 'completed'
        assert run_record['total_trades'] == 5
        assert run_record['final_capital'] == 105000.0
        
        # Verify config was stored as JSON
        stored_config = json.loads(run_record['config'])
        assert stored_config['initial_capital'] == 100000

    def test_strategy_run_with_error(self):
        """Test strategy run completion with error."""
        run_id = "test_run_error"
        config = {"initial_capital": 100000}
        strategies = ["wheel"]
        
        # Start and fail strategy run
        self.db.start_strategy_run(run_id, config, strategies)
        self.db.complete_strategy_run(
            run_id=run_id,
            total_trades=0,
            final_capital=100000.0,
            error_message="Test error"
        )
        
        # Verify error was recorded
        conn = self.db._get_connection()
        cursor = conn.execute(
            "SELECT status, error_message FROM strategy_runs WHERE run_id = ?",
            (run_id,)
        )
        run_record = cursor.fetchone()
        
        assert run_record['status'] == 'failed'
        assert run_record['error_message'] == 'Test error'

    def test_portfolio_snapshot(self):
        """Test portfolio snapshot functionality."""
        positions = {
            'SPY': {'shares': 100, 'cost_basis': 450.0},
            'cash': 50000.0
        }
        
        self.db.save_portfolio_snapshot(
            strategy='wheel',
            total_value=95000.0,
            cash_balance=50000.0,
            positions=positions,
            unrealized_pnl=-5000.0,
            realized_pnl=1000.0
        )
        
        # Verify snapshot was saved
        conn = self.db._get_connection()
        cursor = conn.execute("SELECT * FROM portfolio_snapshots")
        snapshot = cursor.fetchone()
        
        assert snapshot is not None
        assert snapshot['strategy'] == 'wheel'
        assert snapshot['total_value'] == 95000.0
        assert snapshot['unrealized_pnl'] == -5000.0
        
        # Verify positions were stored as JSON
        stored_positions = json.loads(snapshot['positions'])
        assert stored_positions['SPY']['shares'] == 100

    def test_strategy_performance(self):
        """Test strategy performance summary."""
        # Insert trades for different strategies
        trades = [
            {'strategy': 'wheel', 'symbol': 'SPY', 'action': 'SELL_PUT', 
             'quantity': 1, 'price': 450, 'cash_flow': 5.5},
            {'strategy': 'wheel', 'symbol': 'SPY', 'action': 'BUY_SHARES', 
             'quantity': 100, 'price': 445, 'cash_flow': -44500},
            {'strategy': 'rotator', 'symbol': 'BTC', 'action': 'BUY_CRYPTO', 
             'quantity': 0.5, 'price': 50000, 'cash_flow': -25000}
        ]
        
        for trade in trades:
            self.db.insert_trade(trade)
        
        # Get performance summary
        performance = self.db.get_strategy_performance()
        assert len(performance) == 2
        
        # Should be sorted by total cash flow descending
        rotator_perf = next(p for p in performance if p['strategy'] == 'rotator')
        wheel_perf = next(p for p in performance if p['strategy'] == 'wheel')
        
        assert rotator_perf['total_trades'] == 1
        assert rotator_perf['total_cash_flow'] == -25000
        
        assert wheel_perf['total_trades'] == 2
        assert wheel_perf['total_cash_flow'] == -44494.5

    def test_database_stats(self):
        """Test database statistics."""
        # Insert some test data
        self.db.insert_trade({
            'strategy': 'wheel', 'symbol': 'SPY', 'action': 'SELL_PUT',
            'quantity': 1, 'price': 450, 'cash_flow': 5.5
        })
        
        self.db.insert_price_data('SPY', '2023-01-01T10:00:00+00:00', 450.0)
        
        stats = self.db.get_database_stats()
        
        assert 'trades_count' in stats
        assert 'price_cache_count' in stats
        assert 'strategy_runs_count' in stats
        assert 'portfolio_snapshots_count' in stats
        
        assert stats['trades_count'] == 1
        assert stats['price_cache_count'] == 1

    def test_transaction_rollback_on_error(self):
        """Test that transactions are rolled back on error."""
        # Try to insert invalid data that should cause rollback
        with pytest.raises(DatabaseError):
            # This should fail and rollback
            self.db.insert_trade({
                'strategy': 'wheel',
                'symbol': 'SPY',
                # Missing required fields to trigger error
            })
        
        # Verify no data was inserted
        trades = self.db.get_trades()
        assert len(trades) == 0

    def test_thread_safety(self):
        """Test that database operations are thread-safe."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def insert_trade(trade_num):
            try:
                trade_id = self.db.insert_trade({
                    'strategy': 'test',
                    'symbol': f'SYM{trade_num}',
                    'action': 'BUY',
                    'quantity': 1,
                    'price': 100 + trade_num,
                    'cash_flow': -100 - trade_num
                })
                results.put(('success', trade_id))
            except Exception as e:
                results.put(('error', str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=insert_trade, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            status, result = results.get()
            if status == 'success':
                success_count += 1
        
        assert success_count == 5
        
        # Verify all trades were inserted
        all_trades = self.db.get_trades()
        assert len(all_trades) == 5


class TestDatabaseUtilityFunctions:
    """Test utility functions for database operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_trading.db"

    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_get_database_singleton(self):
        """Test that get_database returns the same instance."""
        db1 = get_database(self.db_path)
        db2 = get_database(self.db_path)
        
        # Should return the same instance
        assert db1 is db2

    def test_log_trade_to_db_convenience(self):
        """Test convenience function for logging trades."""
        trade_data = {
            'strategy': 'wheel',
            'symbol': 'SPY',
            'action': 'SELL_PUT',
            'quantity': 1.0,
            'price': 450.0,
            'cash_flow': 5.50
        }
        
        trade_id = log_trade_to_db(trade_data, self.db_path)
        assert isinstance(trade_id, int)
        assert trade_id > 0
        
        # Verify trade was inserted
        db = get_database(self.db_path)
        trades = db.get_trades()
        assert len(trades) == 1
        assert trades[0]['strategy'] == 'wheel'