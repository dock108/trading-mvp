"""
Command-line interface for trading MVP.

This module handles:
- CLI argument parsing
- Help text and documentation
- Command validation
- Integration with configuration management
"""

import argparse
import sys
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default output filenames
STANDARD_TRADES_CSV = "trades.csv"
DETAILED_TRADES_CSV = "detailed_trades.csv"
CONSOLIDATED_TRADES_CSV = "consolidated_trades.csv"


class CLIError(Exception):
    """Exception raised for CLI errors."""
    pass


class TradingCLI:
    """Command-line interface for trading MVP."""
    
    def __init__(self, prog_name: str = "Trading MVP"):
        """Initialize CLI parser.
        
        Args:
            prog_name: Program name for help text
        """
        self.prog_name = prog_name
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all options.
        
        Returns:
            argparse.ArgumentParser: Configured parser
        """
        parser = argparse.ArgumentParser(
            description=f'{self.prog_name} - Multi-strategy trading simulation with live data support',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_examples_text()
        )
        
        # Main execution mode
        parser.add_argument(
            '--backtest',
            action='store_true',
            help='Run in backtest mode with deterministic mock data for reproducible results'
        )
        
        # Configuration options
        parser.add_argument(
            '--config',
            type=str,
            default='config/config.yaml',
            help='Path to configuration file (default: config/config.yaml)'
        )
        
        # Strategy control options
        strategy_group = parser.add_argument_group(
            'Strategy Control',
            'Override which strategies to run (overrides config file settings)'
        )
        
        strategy_group.add_argument(
            '--wheel',
            dest='wheel',
            action='store_true',
            help='Force enable options wheel strategy (overrides config file). '
                 'Trades SPY, QQQ, IWM using cash-secured puts and covered calls'
        )
        
        strategy_group.add_argument(
            '--no-wheel',
            dest='wheel',
            action='store_false',
            help='Force disable options wheel strategy (overrides config file)'
        )
        
        strategy_group.add_argument(
            '--rotator',
            dest='rotator',
            action='store_true',
            help='Force enable crypto rotator strategy (overrides config file). '
                 'Rotates between BTC, ETH, SOL based on weekly performance'
        )
        
        strategy_group.add_argument(
            '--no-rotator',
            dest='rotator',
            action='store_false',
            help='Force disable crypto rotator strategy (overrides config file)'
        )
        
        # Output options
        output_group = parser.add_argument_group(
            'Output Options',
            'Control output format and file destinations'
        )
        
        output_group.add_argument(
            '--output',
            type=str,
            default=STANDARD_TRADES_CSV,
            help=f'Primary output file for trade results (default: {STANDARD_TRADES_CSV})'
        )
        
        output_group.add_argument(
            '--detailed-output',
            type=str,
            default=DETAILED_TRADES_CSV,
            help=f'Detailed output file with additional fields (default: {DETAILED_TRADES_CSV})'
        )
        
        output_group.add_argument(
            '--consolidated-output',
            type=str,
            default=CONSOLIDATED_TRADES_CSV,
            help=f'Consolidated output with strategy names (default: {CONSOLIDATED_TRADES_CSV})'
        )
        
        output_group.add_argument(
            '--no-detailed',
            action='store_true',
            help='Skip generating detailed output file'
        )
        
        output_group.add_argument(
            '--no-consolidated',
            action='store_true',
            help='Skip generating consolidated output file'
        )
        
        # Logging and debugging options
        debug_group = parser.add_argument_group(
            'Debugging & Logging',
            'Control logging level and debug output'
        )
        
        debug_group.add_argument(
            '--verbose', '-v',
            action='count',
            default=0,
            help='Increase verbosity level (use -v, -vv, or -vvv)'
        )
        
        debug_group.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress all output except errors'
        )
        
        debug_group.add_argument(
            '--log-file',
            type=str,
            help='Write logs to specified file in addition to console'
        )
        
        # Data source options
        data_group = parser.add_argument_group(
            'Data Sources',
            'Control market data sources and behavior'
        )
        
        data_group.add_argument(
            '--data-mode',
            choices=['mock', 'live', 'hybrid'],
            help='Override data mode from config (mock=deterministic, live=real APIs, hybrid=fallback)'
        )
        
        data_group.add_argument(
            '--health-check',
            action='store_true',
            help='Perform health check on data sources and exit'
        )
        
        data_group.add_argument(
            '--skip-health-check',
            action='store_true',
            help='Skip health check of data sources before execution'
        )
        
        # Simulation options
        sim_group = parser.add_argument_group(
            'Simulation Parameters',
            'Control simulation behavior and parameters'
        )
        
        sim_group.add_argument(
            '--weeks',
            type=int,
            default=52,
            help='Number of weeks to simulate (default: 52)'
        )
        
        sim_group.add_argument(
            '--initial-capital',
            type=float,
            help='Override initial capital from config file'
        )
        
        sim_group.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate configuration and show execution plan without running'
        )
        
        # Set defaults to None for strategy flags so unspecified flags don't override config
        parser.set_defaults(wheel=None, rotator=None)
        
        return parser
    
    def parse_args(self, args: Optional[list] = None) -> Any:
        """Parse command line arguments.
        
        Args:
            args: Arguments to parse (defaults to sys.argv)
            
        Returns:
            Parsed arguments namespace
            
        Raises:
            CLIError: If argument parsing fails
        """
        try:
            parsed_args = self.parser.parse_args(args)
            self._validate_args(parsed_args)
            return parsed_args
        except SystemExit as e:
            if e.code != 0:
                raise CLIError(f"Argument parsing failed with code {e.code}")
            raise  # Re-raise for --help
        except Exception as e:
            raise CLIError(f"Error parsing arguments: {e}")
    
    def _validate_args(self, args: Any) -> None:
        """Validate parsed arguments for consistency.
        
        Args:
            args: Parsed arguments
            
        Raises:
            CLIError: If validation fails
        """
        # Validate verbosity and quiet flags
        if args.quiet and args.verbose > 0:
            raise CLIError("Cannot use both --quiet and --verbose flags")
        
        # Validate weeks parameter
        if hasattr(args, 'weeks') and args.weeks is not None:
            if args.weeks <= 0:
                raise CLIError("Number of weeks must be positive")
            if args.weeks > 1000:
                raise CLIError("Number of weeks seems unreasonably large (max: 1000)")
        
        # Validate initial capital
        if hasattr(args, 'initial_capital') and args.initial_capital is not None:
            if args.initial_capital <= 0:
                raise CLIError("Initial capital must be positive")
        
        # Validate conflicting strategy flags
        if hasattr(args, 'wheel') and hasattr(args, 'rotator'):
            if args.wheel is False and args.rotator is False:
                raise CLIError("Cannot disable all strategies")
    
    def configure_logging(self, args: Any) -> None:
        """Configure logging based on CLI arguments.
        
        Args:
            args: Parsed arguments
        """
        # Determine log level
        if args.quiet:
            log_level = logging.ERROR
        elif args.verbose == 1:
            log_level = logging.DEBUG
        elif args.verbose >= 2:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        
        # Configure format
        if args.verbose >= 2:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        else:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=log_format,
            force=True  # Override any existing configuration
        )
        
        # Add file handler if specified
        if hasattr(args, 'log_file') and args.log_file:
            try:
                file_handler = logging.FileHandler(args.log_file)
                file_handler.setLevel(log_level)
                file_handler.setFormatter(logging.Formatter(log_format))
                logging.getLogger().addHandler(file_handler)
                logger.info(f"Logging to file: {args.log_file}")
            except Exception as e:
                logger.warning(f"Could not set up file logging: {e}")
    
    def _get_examples_text(self) -> str:
        """Get examples text for help output.
        
        Returns:
            str: Examples section text
        """
        return """
Examples:
  # Run with default configuration
  python main.py --backtest
  
  # Run only wheel strategy with live data
  python main.py --wheel --no-rotator --data-mode live
  
  # Run with custom configuration and verbose output
  python main.py --config custom.yaml --backtest -vv
  
  # Check data source health
  python main.py --health-check
  
  # Dry run to validate configuration
  python main.py --dry-run --config config/config.yaml
  
  # Run with custom capital and output files
  python main.py --backtest --initial-capital 250000 --output my_trades.csv
  
  # Run specific strategies for different durations
  python main.py --backtest --wheel --weeks 26 --verbose
  
Configuration:
  Edit config/config.yaml to customize:
  - Strategy parameters and allocations
  - Market data sources and API keys
  - Symbol lists and trading parameters
  
Data Modes:
  - mock: Uses deterministic mock data for reproducible testing
  - live: Fetches real market data from configured APIs
  - hybrid: Falls back to mock data when APIs are unavailable
  
Environment Variables:
  Set API keys in .env file:
  - COINGECKO_API_KEY: For cryptocurrency data
  - ALPHA_VANTAGE_API_KEY: For backup ETF data
  
For more information, see documentation in README.md
        """.strip()
    
    def print_version(self) -> None:
        """Print version information."""
        print(f"{self.prog_name} v1.0.0")
        print("Multi-strategy trading simulation with live market data support")
    
    def print_config_help(self) -> None:
        """Print configuration help."""
        print("Configuration Help:")
        print("==================")
        print()
        print("The configuration file (config/config.yaml) supports these sections:")
        print()
        print("Basic Settings:")
        print("  initial_capital: 100000")
        print("  data_mode: 'mock'  # or 'live', 'hybrid'")
        print()
        print("Strategy Configuration:")
        print("  strategies:")
        print("    wheel: true")
        print("    rotator: true")
        print()
        print("Capital Allocation:")
        print("  allocation:")
        print("    wheel: 0.5")
        print("    rotator: 0.5")
        print()
        print("Symbol Lists:")
        print("  wheel_symbols: ['SPY', 'QQQ', 'IWM']")
        print("  rotator_symbols: ['BTC', 'ETH', 'SOL']")
        print()
        print("For full configuration reference, see config/config.yaml")


# Global CLI instance
cli = TradingCLI()


def parse_args(args: Optional[list] = None) -> Any:
    """Convenience function to parse arguments.
    
    Args:
        args: Arguments to parse
        
    Returns:
        Parsed arguments
    """
    return cli.parse_args(args)


def configure_logging(args: Any) -> None:
    """Convenience function to configure logging.
    
    Args:
        args: Parsed arguments
    """
    return cli.configure_logging(args)