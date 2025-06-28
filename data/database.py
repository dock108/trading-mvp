"""
SQLite Database Module for Trading MVP

This module provides structured data persistence for:
- Trade execution logs
- Price data caching
- Strategy run metadata
- Portfolio snapshots

Features:
- Automatic table creation and migration
- Thread-safe operations
- Data validation and integrity checks
- Efficient querying for dashboard and analysis
"""

import sqlite3
import logging
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class TradingDatabase:
    """
    SQLite database interface for trading data persistence.
    
    Provides thread-safe operations for storing and retrieving:
    - Trade execution records
    - Price data cache
    - Strategy run metadata
    - Portfolio snapshots
    """
    
    def __init__(self, db_path: Union[str, Path] = "trading.db"):
        """
        Initialize database connection and ensure tables exist.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread-safe connection handling
        self._local = threading.local()
        
        # Initialize database schema
        self._initialize_database()
        
        logger.info(f"TradingDatabase initialized at {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable foreign keys and WAL mode for better performance
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            self._local.connection.execute("PRAGMA journal_mode = WAL")
        
        return self._local.connection
    
    @contextmanager
    def _transaction(self):
        """Context manager for database transactions."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise DatabaseError(f"Transaction failed: {e}") from e
    
    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self._transaction() as conn:
            # Trades table - stores all trade executions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    week TEXT,
                    strategy TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    cash_flow REAL NOT NULL,
                    strike REAL,
                    notes TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes separately
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            
            # Price cache table - stores fetched price data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp, source)
                )
            """)
            
            # Create indexes for price cache
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_cache_symbol ON price_cache(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_cache_timestamp ON price_cache(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_cache_source ON price_cache(source)")
            
            # Strategy runs table - metadata about strategy executions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    config TEXT NOT NULL,
                    strategies TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    error_message TEXT,
                    total_trades INTEGER DEFAULT 0,
                    final_capital REAL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for strategy runs
            conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy_runs_run_id ON strategy_runs(run_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy_runs_start_time ON strategy_runs(start_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_strategy_runs_status ON strategy_runs(status)")
            
            # Portfolio snapshots table - periodic portfolio state
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    total_value REAL NOT NULL,
                    cash_balance REAL NOT NULL,
                    positions TEXT NOT NULL,  -- JSON string
                    unrealized_pnl REAL,
                    realized_pnl REAL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for portfolio snapshots
            conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_timestamp ON portfolio_snapshots(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_strategy ON portfolio_snapshots(strategy)")
        
        logger.info("Database schema initialized successfully")
    
    def insert_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Insert a trade record into the database.
        
        Args:
            trade_data: Dictionary containing trade information
            
        Returns:
            int: ID of inserted trade record
        """
        required_fields = ['strategy', 'symbol', 'action', 'quantity', 'price', 'cash_flow']
        
        # Validate required fields
        for field in required_fields:
            if field not in trade_data:
                raise DatabaseError(f"Missing required field: {field}")
        
        # Add timestamp if not provided
        if 'timestamp' not in trade_data:
            trade_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        with self._transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO trades (
                    timestamp, week, strategy, symbol, action, 
                    quantity, price, cash_flow, strike, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data['timestamp'],
                trade_data.get('week'),
                trade_data['strategy'],
                trade_data['symbol'],
                trade_data['action'],
                trade_data['quantity'],
                trade_data['price'],
                trade_data['cash_flow'],
                trade_data.get('strike'),
                trade_data.get('notes')
            ))
            
            trade_id = cursor.lastrowid
            logger.debug(f"Inserted trade {trade_id}: {trade_data['action']} {trade_data['symbol']}")
            return trade_id
    
    def insert_price_data(self, symbol: str, timestamp: str, price: float, 
                         volume: Optional[float] = None, source: str = "unknown") -> int:
        """
        Insert price data into cache.
        
        Args:
            symbol: Asset symbol
            timestamp: Price timestamp
            price: Asset price
            volume: Trading volume (optional)
            source: Data source name
            
        Returns:
            int: ID of inserted price record
        """
        with self._transaction() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO price_cache (
                    symbol, timestamp, price, volume, source
                ) VALUES (?, ?, ?, ?, ?)
            """, (symbol, timestamp, price, volume, source))
            
            return cursor.lastrowid
    
    def get_trades(self, strategy: Optional[str] = None, symbol: Optional[str] = None,
                   start_date: Optional[str] = None, end_date: Optional[str] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve trade records with optional filtering.
        
        Args:
            strategy: Filter by strategy name
            symbol: Filter by symbol
            start_date: Filter trades after this date
            end_date: Filter trades before this date
            limit: Maximum number of records to return
            
        Returns:
            List of trade dictionaries
        """
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        conn = self._get_connection()
        cursor = conn.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_price_data(self, symbol: str, start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve cached price data.
        
        Args:
            symbol: Asset symbol
            start_date: Filter prices after this date
            end_date: Filter prices before this date
            
        Returns:
            List of price data dictionaries
        """
        query = "SELECT * FROM price_cache WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp ASC"
        
        conn = self._get_connection()
        cursor = conn.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def start_strategy_run(self, run_id: str, config: Dict[str, Any], 
                          strategies: List[str]) -> int:
        """
        Record the start of a strategy run.
        
        Args:
            run_id: Unique identifier for this run
            config: Strategy configuration
            strategies: List of strategies being executed
            
        Returns:
            int: ID of strategy run record
        """
        import json
        
        with self._transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO strategy_runs (
                    run_id, start_time, config, strategies, status
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                run_id,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(config),
                json.dumps(strategies),
                'running'
            ))
            
            return cursor.lastrowid
    
    def complete_strategy_run(self, run_id: str, total_trades: int, 
                             final_capital: float, error_message: Optional[str] = None):
        """
        Mark a strategy run as completed.
        
        Args:
            run_id: Unique identifier for the run
            total_trades: Number of trades executed
            final_capital: Final portfolio value
            error_message: Error message if run failed
        """
        status = 'failed' if error_message else 'completed'
        
        with self._transaction() as conn:
            conn.execute("""
                UPDATE strategy_runs 
                SET end_time = ?, status = ?, total_trades = ?, 
                    final_capital = ?, error_message = ?
                WHERE run_id = ?
            """, (
                datetime.now(timezone.utc).isoformat(),
                status,
                total_trades,
                final_capital,
                error_message,
                run_id
            ))
    
    def save_portfolio_snapshot(self, strategy: str, total_value: float,
                               cash_balance: float, positions: Dict[str, Any],
                               unrealized_pnl: Optional[float] = None,
                               realized_pnl: Optional[float] = None):
        """
        Save a portfolio snapshot.
        
        Args:
            strategy: Strategy name
            total_value: Total portfolio value
            cash_balance: Available cash
            positions: Current positions (serialized as JSON)
            unrealized_pnl: Unrealized profit/loss
            realized_pnl: Realized profit/loss
        """
        import json
        
        with self._transaction() as conn:
            conn.execute("""
                INSERT INTO portfolio_snapshots (
                    timestamp, strategy, total_value, cash_balance, 
                    positions, unrealized_pnl, realized_pnl
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(timezone.utc).isoformat(),
                strategy,
                total_value,
                cash_balance,
                json.dumps(positions),
                unrealized_pnl,
                realized_pnl
            ))
    
    def get_strategy_performance(self, strategy: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get performance summary by strategy.
        
        Args:
            strategy: Filter by strategy name (optional)
            
        Returns:
            List of performance dictionaries
        """
        query = """
            SELECT 
                strategy,
                COUNT(*) as total_trades,
                SUM(cash_flow) as total_cash_flow,
                AVG(cash_flow) as avg_trade_value,
                MIN(timestamp) as first_trade,
                MAX(timestamp) as last_trade
            FROM trades 
            WHERE 1=1
        """
        params = []
        
        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)
        
        query += " GROUP BY strategy ORDER BY total_cash_flow DESC"
        
        conn = self._get_connection()
        cursor = conn.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old data to prevent database growth.
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        cutoff_date = (datetime.now(timezone.utc) - 
                      timedelta(days=days_to_keep)).isoformat()
        
        with self._transaction() as conn:
            # Clean old price cache data
            cursor = conn.execute(
                "DELETE FROM price_cache WHERE created_at < ?", 
                (cutoff_date,)
            )
            price_deleted = cursor.rowcount
            
            # Clean old completed strategy runs (keep recent ones for analysis)
            cursor = conn.execute("""
                DELETE FROM strategy_runs 
                WHERE created_at < ? AND status = 'completed'
            """, (cutoff_date,))
            runs_deleted = cursor.rowcount
            
            logger.info(f"Cleaned up {price_deleted} price records and "
                       f"{runs_deleted} strategy runs older than {days_to_keep} days")
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        conn = self._get_connection()
        
        stats = {}
        tables = ['trades', 'price_cache', 'strategy_runs', 'portfolio_snapshots']
        
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Close database connections."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')


# Global database instance
_db_instance: Optional[TradingDatabase] = None


def get_database(db_path: Union[str, Path] = "trading.db") -> TradingDatabase:
    """
    Get or create global database instance.
    
    Args:
        db_path: Path to database file
        
    Returns:
        TradingDatabase instance
    """
    global _db_instance
    
    if _db_instance is None:
        _db_instance = TradingDatabase(db_path)
    
    return _db_instance


def log_trade_to_db(trade_data: Dict[str, Any], db_path: Union[str, Path] = "trading.db"):
    """
    Convenience function to log a trade to the database.
    
    Args:
        trade_data: Trade information dictionary
        db_path: Path to database file
    """
    db = get_database(db_path)
    return db.insert_trade(trade_data)


def log_price_to_db(symbol: str, price: float, timestamp: Optional[str] = None,
                   volume: Optional[float] = None, source: str = "unknown",
                   db_path: Union[str, Path] = "trading.db"):
    """
    Convenience function to log price data to the database.
    
    Args:
        symbol: Asset symbol
        price: Asset price
        timestamp: Price timestamp (defaults to now)
        volume: Trading volume
        source: Data source name
        db_path: Path to database file
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    
    db = get_database(db_path)
    return db.insert_price_data(symbol, timestamp, price, volume, source)