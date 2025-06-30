"""
Strategy Execution Routes

API endpoints for running trading strategies and retrieving results.
"""

import os
import sys
import csv
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Add parent directories to Python path to import trading modules
# __file__ is in backend/app/routes/strategies.py
# We want to get to trading_mvp/ directory
current_dir = os.path.dirname(__file__)  # backend/app/routes/
app_dir = os.path.dirname(current_dir)   # backend/app/
backend_dir = os.path.dirname(app_dir)   # backend/
trading_mvp_dir = os.path.dirname(backend_dir)  # trading_mvp/
sys.path.insert(0, trading_mvp_dir)

from .config import load_config, save_config

router = APIRouter()

class StrategyRunRequest(BaseModel):
    """Model for strategy run requests"""
    strategies: List[str]  # ["wheel", "rotator"]
    config_overrides: Optional[Dict[str, Any]] = None
    backtest: Optional[bool] = True  # Always run in backtest mode for safety

class TradeRecord(BaseModel):
    """Model for individual trade records"""
    week: str
    strategy: str
    symbol: str
    action: str
    quantity: float
    price: float
    strike: Optional[float] = None
    cash_flow: float
    notes: str
    timestamp: str

class StrategyResult(BaseModel):
    """Model for strategy execution results"""
    trades: List[TradeRecord]
    summary: Dict[str, Any]
    strategy_name: str
    execution_time: float

class RunResponse(BaseModel):
    """Model for run response"""
    results: Dict[str, StrategyResult]
    status: str
    ran_at: str
    total_trades: int
    combined_summary: Dict[str, Any]

def parse_trades_csv(file_path: str) -> List[Dict[str, Any]]:
    """Parse trades from CSV file"""
    trades = []
    if not os.path.exists(file_path):
        return trades
    
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Convert numeric fields
                try:
                    row['quantity'] = float(row['quantity']) if row['quantity'] else 0.0
                    row['price'] = float(row['price']) if row['price'] else 0.0
                    row['cash_flow'] = float(row['cash_flow']) if row['cash_flow'] else 0.0
                    if row.get('strike'):
                        row['strike'] = float(row['strike'])
                except (ValueError, TypeError):
                    pass  # Keep original value if conversion fails
                
                trades.append(row)
    except Exception as e:
        print(f"Error parsing trades CSV: {e}")
    
    return trades

def run_wheel_strategy(config: Dict[str, Any], price_fetcher=None) -> Dict[str, Any]:
    """Execute wheel strategy and return results"""
    try:
        from strategies.wheel_strategy import WheelStrategy
        
        # Calculate capital allocation
        allocation = config.get('allocation', {})
        wheel_allocation = allocation.get('wheel', 0.5)
        initial_capital = config.get('initial_capital', 100000)
        wheel_capital = initial_capital * wheel_allocation
        
        # Get wheel symbols
        wheel_symbols = config.get('wheel_symbols', ['SPY', 'QQQ', 'IWM'])
        
        # Initialize strategy
        strategy = WheelStrategy(
            capital=wheel_capital,
            symbols=wheel_symbols,
            config=config,
            price_fetcher=price_fetcher
        )
        
        # Run strategy (always in backtest mode for safety)
        start_time = datetime.now()
        trades = strategy.run(backtest=True)
        end_time = datetime.now()
        
        # Calculate execution time
        execution_time = (end_time - start_time).total_seconds()
        
        # Get summary metrics from strategy
        summary = {
            "total_trades": len(trades),
            "initial_capital": wheel_capital,
            "final_capital": getattr(strategy, 'available_capital', wheel_capital),
            "total_return": getattr(strategy, 'total_return', 0.0),
            "execution_time": execution_time
        }
        
        # Clean trade data for API response - convert empty strikes to None
        cleaned_trades = []
        for trade in trades:
            trade_dict = trade.copy() if isinstance(trade, dict) else trade
            if isinstance(trade_dict, dict):
                # Convert empty strike values to None
                if 'strike' in trade_dict and (trade_dict['strike'] == '' or trade_dict['strike'] == 'None'):
                    trade_dict['strike'] = None
                cleaned_trades.append(trade_dict)
        
        return {
            "trades": cleaned_trades,
            "summary": summary,
            "strategy_name": "wheel",
            "execution_time": execution_time
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Wheel strategy error: {error_details}")
        return {
            "error": str(e),
            "trades": [],
            "summary": {},
            "strategy_name": "wheel",
            "execution_time": 0.0
        }

def run_rotator_strategy(config: Dict[str, Any], price_fetcher=None) -> Dict[str, Any]:
    """Execute crypto rotator strategy and return results"""
    try:
        from strategies.crypto_rotator_strategy import CryptoRotator
        
        # Calculate capital allocation
        allocation = config.get('allocation', {})
        rotator_allocation = allocation.get('rotator', 0.5)
        initial_capital = config.get('initial_capital', 100000)
        rotator_capital = initial_capital * rotator_allocation
        
        # Get rotator symbols
        rotator_symbols = config.get('rotator_symbols', ['BTC', 'ETH', 'SOL'])
        
        # Initialize strategy
        strategy = CryptoRotator(
            capital=rotator_capital,
            coins=rotator_symbols,
            config=config,
            price_fetcher=price_fetcher
        )
        
        # Run strategy (always in backtest mode for safety)
        start_time = datetime.now()
        trades = strategy.run(backtest=True)
        end_time = datetime.now()
        
        # Calculate execution time
        execution_time = (end_time - start_time).total_seconds()
        
        # Get summary metrics from strategy - use actual portfolio value
        final_portfolio_value = strategy.get_current_portfolio_value()
        total_return = ((final_portfolio_value - rotator_capital) / rotator_capital) * 100 if rotator_capital > 0 else 0.0
        
        summary = {
            "total_trades": len(trades),
            "initial_capital": rotator_capital,
            "final_capital": final_portfolio_value,
            "total_return": total_return,
            "execution_time": execution_time,
            "realized_pnl": getattr(strategy, 'realized_pnl', 0.0),
            "unrealized_pnl": strategy.get_unrealized_pnl()
        }
        
        # Clean trade data for API response - convert empty strikes to None
        cleaned_trades = []
        for trade in trades:
            trade_dict = trade.copy() if isinstance(trade, dict) else trade
            if isinstance(trade_dict, dict):
                # Convert empty strike values to None
                if 'strike' in trade_dict and (trade_dict['strike'] == '' or trade_dict['strike'] == 'None'):
                    trade_dict['strike'] = None
                cleaned_trades.append(trade_dict)
        
        return {
            "trades": cleaned_trades,
            "summary": summary,
            "strategy_name": "rotator",
            "execution_time": execution_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running rotator strategy: {str(e)}")

@router.post("/run", response_model=RunResponse)
async def run_strategies(request: StrategyRunRequest):
    """
    Execute selected trading strategies using TradingOrchestrator
    
    Runs one or both strategies based on request and returns results.
    Always runs in simulation/backtest mode for safety.
    """
    try:
        # Load current configuration
        config = load_config()
        
        # Apply any configuration overrides
        if request.config_overrides:
            for key, value in request.config_overrides.items():
                if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                    config[key].update(value)
                else:
                    config[key] = value
        
        # Force backtest mode for safety
        config['backtest_mode'] = True
        config['test_mode'] = True
        
        # Override enabled strategies based on request
        config['strategies'] = {
            'wheel': 'wheel' in request.strategies,
            'rotator': 'rotator' in request.strategies
        }
        
        # Initialize price fetcher if needed
        price_fetcher = None
        data_mode = config.get('data_mode', 'mock')
        if data_mode == 'live':
            try:
                from data.price_fetcher import PriceFetcher
                price_fetcher = PriceFetcher()
            except Exception as e:
                print(f"Failed to initialize PriceFetcher: {e}")
                print("Falling back to mock data mode")
        
        # Import and initialize TradingOrchestrator
        from core.orchestrator import TradingOrchestrator
        from core.performance_metrics import calculate_strategy_metrics
        
        start_time = datetime.now()
        
        # Create orchestrator
        orchestrator = TradingOrchestrator(config, price_fetcher)
        
        # Get simulation parameters
        weeks_to_simulate = config.get('simulation', {}).get('weeks_to_simulate', 8)  # Default to 8 for API
        
        # Execute simulation
        all_trades = orchestrator.execute_simulation(weeks=weeks_to_simulate)
        
        end_time = datetime.now()
        
        # Calculate results for each strategy
        results = {}
        total_trades = len(all_trades)
        combined_cash_flow = sum(trade.get('cash_flow', 0) for trade in all_trades)
        
        for strategy_name in request.strategies:
            if strategy_name in orchestrator.strategies:
                strategy = orchestrator.strategies[strategy_name]
                strategy_trades = [t for t in all_trades if t.get('strategy') == strategy_name]
                
                # Calculate performance metrics
                initial_capital = getattr(strategy, 'initial_capital', 0)
                final_capital = getattr(strategy, 'capital', initial_capital)
                if hasattr(strategy, 'get_current_portfolio_value'):
                    final_capital = strategy.get_current_portfolio_value()
                
                execution_time = (end_time - start_time).total_seconds()
                
                # Calculate return
                total_return = ((final_capital - initial_capital) / initial_capital) * 100 if initial_capital > 0 else 0.0
                
                results[strategy_name] = {
                    "trades": strategy_trades,
                    "summary": {
                        "total_trades": len(strategy_trades),
                        "initial_capital": initial_capital,
                        "final_capital": final_capital,
                        "total_return": total_return,
                        "execution_time": execution_time
                    },
                    "strategy_name": strategy_name,
                    "execution_time": execution_time
                }
        
        # Calculate combined summary
        total_execution_time = (end_time - start_time).total_seconds()
        combined_summary = {
            "total_execution_time": total_execution_time,
            "total_strategies_run": len(results),
            "combined_cash_flow": combined_cash_flow,
            "strategies_requested": request.strategies,
            "data_mode": data_mode,
            "weeks_simulated": weeks_to_simulate
        }
        
        return RunResponse(
            results=results,
            status="success" if results else "no_strategies_run",
            ran_at=end_time.isoformat(),
            total_trades=total_trades,
            combined_summary=combined_summary
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Strategy execution error: {error_details}")
        
        # Return error response
        return RunResponse(
            results={},
            status="error",
            ran_at=datetime.now().isoformat(),
            total_trades=0,
            combined_summary={
                "error": str(e),
                "strategies_requested": request.strategies
            }
        )

@router.get("/trades")
async def get_latest_trades():
    """
    Get latest trade results
    
    Returns trades from the most recent strategy execution.
    """
    # Try to read from the trades CSV files
    detailed_trades_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "detailed_trades.csv")
    trades = parse_trades_csv(detailed_trades_path)
    
    return {
        "trades": trades,
        "count": len(trades),
        "source": "detailed_trades.csv"
    }

@router.get("/summary")
async def get_summary():
    """
    Get strategy performance summary
    
    Returns summary metrics from the most recent run.
    """
    # For now, return a basic summary
    # This could be enhanced to read from a summary file or database
    return {
        "message": "Summary endpoint - to be enhanced with persistent storage",
        "last_run": None
    }