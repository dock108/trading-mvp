#!/usr/bin/env python3
"""
Main CLI script to run trading strategies with live data support.

Features:
- Live market data integration via PriceFetcher
- Environment variable loading for API keys
- Comprehensive error handling and fallbacks
- Multiple data source support
"""

import os
import yaml
import argparse
import csv
import logging
from datetime import datetime
from dotenv import load_dotenv

from strategies.wheel_strategy import WheelStrategy
from strategies.crypto_rotator_strategy import CryptoRotator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
ALLOCATION_TOLERANCE = 0.01  # Allow small floating point errors in allocation percentages
DEFAULT_INITIAL_CAPITAL = 100000
DEFAULT_CONFIG_PATH = "config/config.yaml"

# Default output filenames
STANDARD_TRADES_CSV = "trades.csv"
DETAILED_TRADES_CSV = "detailed_trades.csv"
CONSOLIDATED_TRADES_CSV = "consolidated_trades.csv"

def initialize_price_fetcher(config):
    """Initialize PriceFetcher for live data mode."""
    data_mode = config.get('data_mode', 'mock')
    
    if data_mode != 'live':
        logger.info(f"Data mode is '{data_mode}', PriceFetcher not needed")
        return None
    
    try:
        # Import PriceFetcher only when needed to avoid dependency issues in mock mode
        from data.price_fetcher import PriceFetcher
        
        logger.info("Initializing PriceFetcher for live data mode")
        price_fetcher = PriceFetcher()
        
        # Perform health check
        logger.info("Performing data source health check...")
        health_status = price_fetcher.health_check()
        
        working_sources = sum(1 for status in health_status.values() if status is True)
        total_sources = len([s for s in health_status.values() if s is not None])
        
        if working_sources == 0:
            logger.error("No data sources are working! Check your API keys and network connection.")
            logger.info("Available fallback: mock data mode")
            return None
        elif working_sources < total_sources:
            logger.warning(f"Only {working_sources}/{total_sources} data sources are working")
            logger.info("Some fallback mechanisms may be used")
        else:
            logger.info(f"All {working_sources} data sources are healthy")
        
        # Log data source status
        for source, status in health_status.items():
            if status is True:
                logger.info(f"  ✅ {source}: Working")
            elif status is False:
                logger.warning(f"  ❌ {source}: Failed")
            else:
                logger.info(f"  ⚠️ {source}: Not configured")
        
        return price_fetcher
        
    except ImportError as e:
        logger.error(f"Failed to import PriceFetcher: {e}")
        logger.info("Install required dependencies: pip install -r requirements.txt")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize PriceFetcher: {e}")
        logger.info("Falling back to mock data mode")
        return None

def validate_data_mode_config(config):
    """Validate data mode configuration and provide helpful guidance."""
    data_mode = config.get('data_mode', 'mock')
    
    if data_mode == 'live':
        # Check for required environment variables
        required_vars = ['COINGECKO_API_KEY']  # CoinGecko is our primary crypto source
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing environment variables for live mode: {missing_vars}")
            logger.info("Live mode will use free API tiers or fall back to mock data")
            logger.info("For best results, sign up for API keys at:")
            logger.info("  - CoinGecko: https://coingecko.com/api")
            logger.info("  - Alpha Vantage: https://alphavantage.co/support/#api-key")
        
        # Check .env file exists
        if not os.path.exists('.env'):
            logger.warning(".env file not found")
            logger.info("Create .env file from .env.example template for API key management")
    
    logger.info(f"Data mode: {data_mode}")
    return data_mode

def parse_arguments():
    """Parse command-line arguments with detailed help descriptions."""
    parser = argparse.ArgumentParser(
        description="Run personal trading MVP strategies (Options Wheel + Crypto Rotator)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python main.py --backtest                    # Run both strategies in backtest mode
  python main.py --wheel --no-rotator         # Run only options wheel strategy
  python main.py --config my_config.yaml      # Use custom configuration file
  python main.py --backtest --rotator         # Run only crypto rotator in backtest mode
        """
    )
    
    # Config file path option
    parser.add_argument("--config", "-c", 
                       metavar="FILE",
                       help="Path to YAML configuration file containing strategy settings, "
                            "capital allocation, and symbol lists (default: config/config.yaml)", 
                       default=DEFAULT_CONFIG_PATH)
    
    # Backtest mode flag
    parser.add_argument("--backtest", "-b", 
                       action="store_true", 
                       help="Run simulation using deterministic mock historical data for "
                            "reproducible results. Without this flag, strategies would use "
                            "real market data (not implemented)")
    
    # Strategy toggle flags (optional overrides)
    parser.add_argument("--wheel", 
                       dest="wheel", 
                       action="store_true", 
                       help="Force enable options wheel strategy (overrides config file). "
                            "Trades SPY, QQQ, IWM using cash-secured puts and covered calls")
    parser.add_argument("--no-wheel", 
                       dest="wheel", 
                       action="store_false", 
                       help="Force disable options wheel strategy (overrides config file)")
    parser.add_argument("--rotator", 
                       dest="rotator", 
                       action="store_true", 
                       help="Force enable crypto rotator strategy (overrides config file). "
                            "Rotates between BTC, ETH, SOL based on weekly performance")
    parser.add_argument("--no-rotator", 
                       dest="rotator", 
                       action="store_false", 
                       help="Force disable crypto rotator strategy (overrides config file)")
    
    # Set defaults to None so unspecified flags don't override config
    parser.set_defaults(wheel=None, rotator=None)
    
    return parser.parse_args()

def load_config(config_path='config/config.yaml'):
    """Load configuration from YAML file with validation and defaults."""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        exit(1)
    
    # Validate and apply defaults for required fields
    config = validate_and_apply_defaults(config)
    return config

def get_default_config():
    """Get default configuration values.
    
    Returns:
        dict: Default configuration
    """
    return {
        'initial_capital': DEFAULT_INITIAL_CAPITAL,
        'strategies': {
            'wheel': True,
            'rotator': True
        },
        'allocation': {
            'wheel': 0.5,
            'rotator': 0.5
        },
        'wheel_symbols': ['SPY', 'QQQ', 'IWM'],
        'rotator_symbols': ['BTC', 'ETH', 'SOL']
    }

def apply_config_defaults(config, defaults):
    """Apply default values to missing configuration keys.
    
    Args:
        config (dict): Configuration to modify
        defaults (dict): Default values to apply
        
    Returns:
        dict: Modified configuration
    """
    if config is None:
        config = {}
    
    # Merge defaults with loaded config
    for key, default_value in defaults.items():
        if key not in config:
            config[key] = default_value
            print(f"Config default applied: {key} = {default_value}")
        elif isinstance(default_value, dict) and isinstance(config[key], dict):
            # Handle nested dictionaries
            for sub_key, sub_default in default_value.items():
                if sub_key not in config[key]:
                    config[key][sub_key] = sub_default
                    print(f"Config default applied: {key}.{sub_key} = {sub_default}")
    
    return config

def validate_required_fields(config):
    """Validate that all required configuration fields are present.
    
    Args:
        config (dict): Configuration to validate
        
    Raises:
        SystemExit: If required fields are missing
    """
    required_fields = [
        'initial_capital',
        'strategies.wheel',
        'strategies.rotator', 
        'allocation.wheel',
        'allocation.rotator'
    ]
    
    for field in required_fields:
        if '.' in field:
            # Nested field validation
            keys = field.split('.')
            current = config
            for key in keys:
                if key not in current:
                    print(f"Error: Required config field '{field}' is missing.")
                    exit(1)
                current = current[key]
        else:
            if field not in config:
                print(f"Error: Required config field '{field}' is missing.")
                exit(1)

def normalize_allocation_percentages(config):
    """Normalize allocation percentages to sum to 1.0.
    
    Args:
        config (dict): Configuration to modify
        
    Returns:
        dict: Modified configuration
    """
    total_allocation = config['allocation']['wheel'] + config['allocation']['rotator']
    if abs(total_allocation - 1.0) > ALLOCATION_TOLERANCE:
        print(f"Warning: Allocation percentages sum to {total_allocation:.2f}, not 1.0")
        print("Normalizing allocations...")
        config['allocation']['wheel'] /= total_allocation
        config['allocation']['rotator'] /= total_allocation
    
    return config

def validate_and_apply_defaults(config):
    """Validate configuration and apply defaults for missing keys.
    
    Args:
        config (dict): Raw configuration from file
        
    Returns:
        dict: Validated and normalized configuration
    """
    # Get default values
    defaults = get_default_config()
    
    # Apply defaults to missing keys
    config = apply_config_defaults(config, defaults)
    
    # Validate required fields
    validate_required_fields(config)
    
    # Normalize allocation percentages
    config = normalize_allocation_percentages(config)
    
    return config

def apply_cli_overrides(config, args):
    """Apply command-line argument overrides to config with validation."""
    # Store original values for comparison
    original_wheel = config['strategies']['wheel']
    original_rotator = config['strategies']['rotator']
    
    # Override strategy enables if specified
    if args.wheel is not None:
        config['strategies']['wheel'] = args.wheel
        print(f"CLI override: Wheel strategy {'enabled' if args.wheel else 'disabled'} (was {'enabled' if original_wheel else 'disabled'})")
    
    if args.rotator is not None:
        config['strategies']['rotator'] = args.rotator
        print(f"CLI override: Rotator strategy {'enabled' if args.rotator else 'disabled'} (was {'enabled' if original_rotator else 'disabled'})")
    
    # Apply backtest mode settings
    if args.backtest:
        config['backtest_mode'] = True
        config['test_mode'] = True  # Use deterministic data for backtesting
        print("CLI override: Backtest mode enabled (deterministic test data)")
    else:
        config['backtest_mode'] = False
        config['test_mode'] = False
    
    # Validate that at least one strategy is enabled
    if not config['strategies']['wheel'] and not config['strategies']['rotator']:
        print("Error: At least one strategy must be enabled.")
        print("Use --wheel or --rotator to enable a strategy.")
        exit(1)
    
    # Extract individual config values for easier access
    initial_capital = config.get('initial_capital', 100000)
    wheel_enabled = config['strategies'].get('wheel', True)
    rotator_enabled = config['strategies'].get('rotator', True)
    wheel_allocation = config['allocation'].get('wheel', 0.5)
    rotator_allocation = config['allocation'].get('rotator', 0.5)
    
    # Store extracted values back in config for convenience
    config['_extracted'] = {
        'initial_capital': initial_capital,
        'wheel_enabled': wheel_enabled,
        'rotator_enabled': rotator_enabled,
        'wheel_allocation': wheel_allocation,
        'rotator_allocation': rotator_allocation
    }
    
    return config

def calculate_capital_allocation(config):
    """Calculate capital allocation for enabled strategies.
    
    Single strategy gets 100% of capital regardless of config allocation.
    Multiple strategies use configured allocation percentages.
    
    Returns:
        dict: Capital allocation per strategy
    """
    initial_capital = config['initial_capital']
    wheel_enabled = config['strategies']['wheel']
    rotator_enabled = config['strategies']['rotator']
    
    # Count enabled strategies to determine allocation logic
    enabled_count = sum([wheel_enabled, rotator_enabled])
    
    if enabled_count == 0:
        return {}
    elif enabled_count == 1:
        # Single strategy gets full capital (ignore config allocation percentages)
        if wheel_enabled:
            return {'wheel': initial_capital, 'rotator': 0}
        else:
            return {'wheel': 0, 'rotator': initial_capital}
    else:
        # Multiple strategies: split capital using allocation percentages
        wheel_allocation = config['allocation']['wheel']
        rotator_allocation = config['allocation']['rotator']
        
        wheel_capital = initial_capital * wheel_allocation
        rotator_capital = initial_capital * rotator_allocation
        
        print(f"\nCapital Allocation:")
        print(f"  Total Capital: ${initial_capital:,.2f}")
        print(f"  Wheel ({wheel_allocation:.1%}): ${wheel_capital:,.2f}")
        print(f"  Rotator ({rotator_allocation:.1%}): ${rotator_capital:,.2f}")
        
        return {'wheel': wheel_capital, 'rotator': rotator_capital}

def initialize_strategies(config, price_fetcher=None):
    """Initialize enabled strategies with proper capital allocation.
    
    Args:
        config (dict): Configuration dictionary
        price_fetcher: PriceFetcher instance for live data (optional)
        
    Returns:
        dict: Dictionary of initialized strategy instances
    """
    strategies = {}
    
    # Calculate capital allocation
    allocation = calculate_capital_allocation(config)
    
    # Show data source information
    data_mode = config.get('data_mode', 'mock')
    print(f"\nData Source Configuration:")
    print(f"  Mode: {data_mode}")
    if price_fetcher:
        print(f"  Live data: Available via PriceFetcher")
    else:
        print(f"  Live data: Not available (using mock/simulated data)")
    
    # Initialize wheel strategy if enabled
    if config['strategies']['wheel'] and allocation['wheel'] > 0:
        wheel_symbols = config.get('wheel_symbols', ['SPY', 'QQQ', 'IWM'])
        
        print(f"\nInitializing Wheel Strategy:")
        print(f"  Capital: ${allocation['wheel']:,.2f}")
        print(f"  Symbols: {wheel_symbols}")
        
        strategies['wheel'] = WheelStrategy(
            capital=allocation['wheel'],
            symbols=wheel_symbols,
            config=config,
            price_fetcher=price_fetcher
        )
        
        # Display data source info
        data_info = strategies['wheel'].get_data_source_info()
        print(f"  Data Source: {data_info['data_source']}")
    
    # Initialize rotator strategy if enabled
    if config['strategies']['rotator'] and allocation['rotator'] > 0:
        rotator_symbols = config.get('rotator_symbols', ['BTC', 'ETH', 'SOL'])
        
        print(f"\nInitializing Crypto Rotator Strategy:")
        print(f"  Capital: ${allocation['rotator']:,.2f}")
        print(f"  Symbols: {rotator_symbols}")
        
        strategies['rotator'] = CryptoRotator(
            capital=allocation['rotator'],
            coins=rotator_symbols,
            config=config,
            price_fetcher=price_fetcher
        )
        
        # Display data source info
        data_info = strategies['rotator'].get_data_source_info()
        print(f"  Data Source: {data_info['data_source']}")
        if data_info.get('symbol_mapping'):
            print(f"  Symbol Mapping: {data_info['symbol_mapping']}")
    
    return strategies

def execute_strategies(strategies, backtest=True):
    """Execute all initialized strategies and collect trade results.
    
    Args:
        strategies (dict): Dictionary of strategy instances
        backtest (bool): Whether to run in backtest mode
        
    Returns:
        dict: Dictionary of trade lists by strategy name
    """
    if not strategies:
        print("No strategies to execute.")
        return {}
    
    print(f"\nExecuting {len(strategies)} strategy(ies)...")
    
    # Collect trade results from each strategy
    all_trades = {}
    
    # Execute wheel strategy
    if 'wheel' in strategies:
        print("\n" + "="*50)
        print("EXECUTING OPTIONS WHEEL STRATEGY")
        print("="*50)
        wheel_trades = strategies['wheel'].run(backtest=backtest)
        all_trades['wheel'] = wheel_trades
    
    # Execute rotator strategy  
    if 'rotator' in strategies:
        print("\n" + "="*50)
        print("EXECUTING CRYPTO ROTATOR STRATEGY")
        print("="*50)
        rotator_trades = strategies['rotator'].run(backtest=backtest)
        all_trades['rotator'] = rotator_trades
    
    # Final summary across all strategies
    print("\n" + "="*50)
    print("MULTI-STRATEGY EXECUTION COMPLETE")
    print("="*50)
    
    total_trades = 0
    for strategy_name, trade_list in all_trades.items():
        trade_count = len(trade_list)
        total_trades += trade_count
        print(f"{strategy_name.title()} Strategy: {trade_count} trades")
    
    print(f"Total Trades Across All Strategies: {total_trades}")
    print("All trades have been exported to trades.csv")
    
    return all_trades

def combine_trade_logs(all_trades):
    """Combine trade logs from multiple strategies into a single chronological list.
    
    Args:
        all_trades (dict): Dictionary of trade lists by strategy name
        
    Returns:
        list: Combined and sorted list of all trades
    """
    combined_trades = []
    
    # Flatten trades from all strategies, preserving strategy identity
    for strategy_name, trade_list in all_trades.items():
        for trade in trade_list:
            # Create copy to avoid modifying original trade data
            trade_copy = trade.copy()
            trade_copy['strategy_name'] = strategy_name
            combined_trades.append(trade_copy)
    
    # Sort by timestamp for chronological order across strategies
    # This is important for weekly allocation analysis in summary reports
    combined_trades.sort(key=lambda x: x.get('timestamp', ''))
    
    return combined_trades

def export_consolidated_trades(combined_trades, filename=CONSOLIDATED_TRADES_CSV):
    """Export combined trades to a consolidated CSV file.
    
    Args:
        combined_trades (list): Combined list of all trades
        filename (str): Output filename
    """
    if not combined_trades:
        print("No trades to export to consolidated file.")
        return
    
    fieldnames = ['week', 'strategy', 'symbol', 'action', 'quantity', 'price', 'strike', 
                  'cash_flow', 'notes', 'timestamp', 'strategy_name']
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_trades)
    
    print(f"\nExported {len(combined_trades)} combined trades to {filename}")

def analyze_strategy_performance(all_trades):
    """Analyze performance for each strategy individually.
    
    Args:
        all_trades (dict): Dictionary of trade lists by strategy
        
    Returns:
        tuple: (total_cash_flow, strategy_summaries)
    """
    total_cash_flow = 0
    strategy_summaries = []
    
    for strategy_name, trade_list in all_trades.items():
        if not trade_list:
            continue
            
        strategy_cash_flow = sum(trade.get('cash_flow', 0) for trade in trade_list)
        total_cash_flow += strategy_cash_flow
        
        # Action breakdown
        actions = {}
        for trade in trade_list:
            action = trade.get('action', 'UNKNOWN')
            actions[action] = actions.get(action, 0) + 1
        
        strategy_summaries.append({
            'name': strategy_name,
            'trade_count': len(trade_list),
            'cash_flow': strategy_cash_flow,
            'actions': actions
        })
    
    return total_cash_flow, strategy_summaries

def analyze_weekly_distribution(combined_trades):
    """Analyze trade distribution by week.
    
    Args:
        combined_trades (list): Combined list of all trades
        
    Returns:
        dict: Weekly distribution of trades
    """
    weekly_distribution = {}
    for trade in combined_trades:
        week = trade.get('week', 'Unknown')
        weekly_distribution[week] = weekly_distribution.get(week, 0) + 1
    return weekly_distribution

def analyze_symbol_performance(combined_trades):
    """Analyze performance by symbol and strategy.
    
    Args:
        combined_trades (list): Combined list of all trades
        
    Returns:
        dict: Symbol analysis data
    """
    symbol_analysis = {}
    for trade in combined_trades:
        symbol = trade.get('symbol', 'Unknown')
        strategy = trade.get('strategy', 'Unknown')
        key = f"{symbol} ({strategy})"
        
        if key not in symbol_analysis:
            symbol_analysis[key] = {'trades': 0, 'cash_flow': 0}
        
        symbol_analysis[key]['trades'] += 1
        symbol_analysis[key]['cash_flow'] += trade.get('cash_flow', 0)
    
    return symbol_analysis

def get_timeline_summary(combined_trades):
    """Get first and last trade information.
    
    Args:
        combined_trades (list): Combined list of all trades
        
    Returns:
        tuple: (first_trade, last_trade) or (None, None) if no trades
    """
    if not combined_trades:
        return None, None
    return combined_trades[0], combined_trades[-1]

def print_trade_analysis(all_trades, combined_trades):
    """Print comprehensive analysis of all trades across strategies.
    
    Args:
        all_trades (dict): Dictionary of trade lists by strategy
        combined_trades (list): Combined list of all trades
    """
    print(f"\n" + "="*60)
    print("COMPREHENSIVE TRADE ANALYSIS")
    print("="*60)
    
    # Strategy-specific analysis
    total_cash_flow, strategy_summaries = analyze_strategy_performance(all_trades)
    
    for summary in strategy_summaries:
        print(f"\n{summary['name'].upper()} STRATEGY:")
        print(f"  Total Trades: {summary['trade_count']}")
        print(f"  Net Cash Flow: ${summary['cash_flow']:+,.2f}")
        print(f"  Action Breakdown:")
        for action, count in sorted(summary['actions'].items()):
            print(f"    {action}: {count}")
    
    # Combined analysis
    print(f"\nCOMBINED ANALYSIS:")
    print(f"  Total Trades Across All Strategies: {len(combined_trades)}")
    print(f"  Combined Net Cash Flow: ${total_cash_flow:+,.2f}")
    
    # Weekly trade distribution
    weekly_distribution = analyze_weekly_distribution(combined_trades)
    print(f"\nWEEKLY TRADE DISTRIBUTION:")
    for week in sorted(weekly_distribution.keys()):
        count = weekly_distribution[week]
        print(f"  {week}: {count} trades")
    
    # Symbol analysis
    symbol_analysis = analyze_symbol_performance(combined_trades)
    print(f"\nSYMBOL ANALYSIS:")
    for symbol_key in sorted(symbol_analysis.keys()):
        data = symbol_analysis[symbol_key]
        print(f"  {symbol_key}: {data['trades']} trades, ${data['cash_flow']:+,.2f} cash flow")
    
    # Timeline analysis
    first_trade, last_trade = get_timeline_summary(combined_trades)
    if first_trade and last_trade:
        print(f"\nTIMELINE ANALYSIS:")
        print(f"  First Trade: {first_trade.get('week', 'Unknown')} - {first_trade.get('action', 'Unknown')} {first_trade.get('symbol', 'Unknown')} ({first_trade.get('strategy', 'Unknown')})")
        print(f"  Last Trade: {last_trade.get('week', 'Unknown')} - {last_trade.get('action', 'Unknown')} {last_trade.get('symbol', 'Unknown')} ({last_trade.get('strategy', 'Unknown')})")

def write_trades_to_csv(all_trades, filename=STANDARD_TRADES_CSV):
    """Write all trades to CSV file using standardized format.
    
    This is the primary CSV format used by summary_report.py for analysis.
    Format: Week,Strategy,Asset,Action,Quantity,Price,Amount
    
    Args:
        all_trades (dict): Dictionary of trade lists by strategy name
        filename (str): Output CSV filename
    """
    # Flatten all trades into a single list with standardized columns
    flattened_trades = []
    for strategy_name, trade_list in all_trades.items():
        for trade in trade_list:
            # Convert trade record to standardized CSV format (7 columns exactly)
            csv_row = [
                trade.get('week', ''),
                trade.get('strategy', ''),
                trade.get('symbol', ''),
                trade.get('action', ''),
                trade.get('quantity', 0),
                trade.get('price', 0.0),
                trade.get('cash_flow', 0.0)  # Amount column for P&L tracking
            ]
            flattened_trades.append(csv_row)
    
    # Write using csv.writer() as specified for summary_report.py compatibility
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Header must match exactly what summary_report.py expects
        writer.writerow(["Week", "Strategy", "Asset", "Action", "Quantity", "Price", "Amount"])
        for trade in flattened_trades:
            writer.writerow(trade)
    
    print(f"\nWrote {len(flattened_trades)} trades to {filename} (standardized CSV format)")

def write_detailed_trades_to_csv(all_trades, filename=DETAILED_TRADES_CSV):
    """Write all trades to CSV file with full detailed format.
    
    Args:
        all_trades (dict): Dictionary of trade lists by strategy name
        filename (str): Output CSV filename
    """
    # Flatten all trades into a single list with full details
    flattened_trades = []
    for strategy_name, trade_list in all_trades.items():
        flattened_trades.extend(trade_list)
    
    if not flattened_trades:
        print(f"No trades to write to {filename}")
        return
    
    # Use DictWriter for full trade details
    fieldnames = ['week', 'strategy', 'symbol', 'action', 'quantity', 'price', 'strike', 
                  'cash_flow', 'notes', 'timestamp']
    
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_trades)
    
    print(f"\nWrote {len(flattened_trades)} detailed trades to {filename}")

def get_trade_counts(config, all_trades):
    """Calculate trade counts for each strategy.
    
    Args:
        config (dict): Configuration dictionary
        all_trades (dict): Dictionary of trade lists by strategy
        
    Returns:
        dict: Trade count information
    """
    return {
        'total': sum(len(trade_list) for trade_list in all_trades.values()),
        'wheel': len(all_trades.get('wheel', [])),
        'rotator': len(all_trades.get('rotator', [])),
        'wheel_enabled': config['strategies']['wheel'],
        'rotator_enabled': config['strategies']['rotator']
    }

def print_execution_status(config, args, trade_counts):
    """Print basic execution status and mode information.
    
    Args:
        config (dict): Configuration dictionary
        args: Command line arguments
        trade_counts (dict): Trade count information
    """
    print(f"Simulation complete. Trades logged to trades.csv. Ran Wheel: {trade_counts['wheel_enabled']}, Rotator: {trade_counts['rotator_enabled']}.")
    
    # Backtest mode information
    if args.backtest:
        print("Backtest mode: used mock historical data for simulation.")
    else:
        print("Live mode: strategies would use real market data (not implemented).")

def print_trade_summary(trade_counts):
    """Print trade summary and file outputs.
    
    Args:
        trade_counts (dict): Trade count information
    """
    total_trades = trade_counts['total']
    
    if total_trades > 0:
        print(f"\nTrade Summary:")
        print(f"  Total Trades: {total_trades}")
        if trade_counts['wheel_enabled']:
            print(f"  Wheel Strategy Trades: {trade_counts['wheel']}")
        if trade_counts['rotator_enabled']:
            print(f"  Rotator Strategy Trades: {trade_counts['rotator']}")
        
        # File outputs  
        print(f"\nFiles Generated:")
        print(f"  trades.csv - Standardized format ({total_trades} trades)")
        print(f"  detailed_trades.csv - Full details ({total_trades} trades)")
        print(f"  consolidated_trades.csv - Combined analysis ({total_trades} trades)")
    else:
        print(f"\nNo trades were executed.")

def print_capital_allocation_summary(config):
    """Print capital allocation summary.
    
    Args:
        config (dict): Configuration dictionary
    """
    initial_capital = config['initial_capital']
    wheel_enabled = config['strategies']['wheel']
    rotator_enabled = config['strategies']['rotator']
    
    print(f"\nCapital Allocation:")
    print(f"  Initial Capital: ${initial_capital:,}")
    
    if wheel_enabled and rotator_enabled:
        wheel_allocation = config['allocation']['wheel']
        rotator_allocation = config['allocation']['rotator']
        print(f"  Wheel Strategy: ${initial_capital * wheel_allocation:,.2f} ({wheel_allocation:.1%})")
        print(f"  Rotator Strategy: ${initial_capital * rotator_allocation:,.2f} ({rotator_allocation:.1%})")
    elif wheel_enabled:
        print(f"  Wheel Strategy: ${initial_capital:,} (100%)")
    elif rotator_enabled:
        print(f"  Rotator Strategy: ${initial_capital:,} (100%)")

def print_simulation_summary(config, args, all_trades):
    """Print final simulation summary with key information.
    
    Args:
        config (dict): Configuration dictionary
        args: Command line arguments
        all_trades (dict): Dictionary of trade lists by strategy
    """
    print(f"\n" + "="*60)
    print("SIMULATION SUMMARY")
    print("="*60)
    
    # Get trade counts
    trade_counts = get_trade_counts(config, all_trades)
    
    # Print execution status
    print_execution_status(config, args, trade_counts)
    
    # Print trade summary
    print_trade_summary(trade_counts)
    
    # Print capital allocation
    print_capital_allocation_summary(config)
    
    # Configuration info
    if config.get('backtest_mode'):
        print(f"\nConfiguration: Deterministic test data enabled for reproducible results")
    
    print(f"\nSimulation completed successfully!")
    print(f"\nTo view a detailed summary report with weekly allocations and performance metrics:")
    print(f"  python summary_report.py")

def main():
    """Main entry point for the trading MVP with live data support."""
    # Parse command-line arguments
    args = parse_arguments()
    
    print("Trading MVP - Weekend Sprint 2: Live Data Integration")
    print(f"Config file: {args.config}")
    
    # Load configuration
    config = load_config(args.config)
    
    # Apply CLI overrides
    config = apply_cli_overrides(config, args)
    
    # Validate data mode and provide guidance
    data_mode = validate_data_mode_config(config)
    
    # Initialize PriceFetcher for live data if needed
    price_fetcher = initialize_price_fetcher(config)
    
    print(f"\nConfiguration Summary:")
    print(f"  Initial capital: ${config['initial_capital']:,}")
    print(f"  Data mode: {data_mode}")
    print(f"  Backtest mode: {'Yes' if args.backtest else 'No'}")
    print(f"  Wheel strategy: {'Enabled' if config['strategies']['wheel'] else 'Disabled'}")
    print(f"  Rotator strategy: {'Enabled' if config['strategies']['rotator'] else 'Disabled'}")
    
    # Initialize enabled strategies with proper capital allocation and data source
    strategies = initialize_strategies(config, price_fetcher)
    
    # Execute strategies and collect trade results
    all_trades = execute_strategies(strategies, backtest=args.backtest)
    
    # Combine and analyze trade logs
    if all_trades:
        combined_trades = combine_trade_logs(all_trades)
        
        # Write trades to CSV files in multiple formats
        write_trades_to_csv(all_trades)  # Standardized format
        write_detailed_trades_to_csv(all_trades)  # Full details
        export_consolidated_trades(combined_trades)  # With strategy_name
        
        # Print comprehensive analysis
        print_trade_analysis(all_trades, combined_trades)
        
        # Print final simulation summary
        print_simulation_summary(config, args, all_trades)
    else:
        # Handle case where no trades were executed
        print_simulation_summary(config, args, {})

if __name__ == "__main__":
    main()