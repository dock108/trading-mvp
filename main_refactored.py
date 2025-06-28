#!/usr/bin/env python3
"""
Main CLI script for trading MVP with refactored architecture.

This script demonstrates the improved separation of concerns:
- CLI handling in core.cli
- Configuration management in core.config  
- Orchestration logic in core.orchestrator
- Main script focuses only on high-level coordination
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.cli import parse_args, configure_logging, CLIError
from core.config import ConfigManager, ConfigError
from core.orchestrator import TradingOrchestrator, OrchestrationError
from data.price_fetcher import PriceFetcher, DataSourceError

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def initialize_price_fetcher(config):
    """Initialize PriceFetcher based on configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        PriceFetcher instance or None for mock mode
    """
    data_mode = config.get('data_mode', 'mock')
    
    if data_mode == 'mock':
        logger.info("Using mock data mode - no PriceFetcher needed")
        return None
    
    try:
        logger.info(f"Initializing PriceFetcher for {data_mode} data mode")
        
        # Initialize PriceFetcher (reads config from environment variables)
        price_fetcher = PriceFetcher()
        
        logger.info("PriceFetcher initialized successfully")
        return price_fetcher
        
    except Exception as e:
        logger.error(f"Failed to initialize PriceFetcher: {e}")
        if data_mode == 'live':
            raise DataSourceError(f"Cannot run in live mode without working PriceFetcher: {e}")
        
        logger.warning("Falling back to mock data mode")
        return None


def perform_health_check(orchestrator):
    """Perform and display health check results.
    
    Args:
        orchestrator: TradingOrchestrator instance
    """
    logger.info("Performing health check...")
    
    try:
        health_results = orchestrator.perform_health_check()
        
        print("\nHealth Check Results:")
        print("=" * 50)
        
        for component, status in health_results.items():
            component_name = component.replace('_', ' ').title()
            print(f"  {component_name}: {status}")
        
        print()
        
        # Check if any components failed
        failed_components = [
            comp for comp, status in health_results.items() 
            if '❌' in status
        ]
        
        if failed_components:
            logger.warning(f"Health check found issues with: {', '.join(failed_components)}")
            return False
        else:
            logger.info("All components healthy")
            return True
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False


def perform_dry_run(config, orchestrator):
    """Perform dry run to validate configuration and show execution plan.
    
    Args:
        config: Configuration dictionary
        orchestrator: TradingOrchestrator instance
    """
    print("\nDry Run - Execution Plan:")
    print("=" * 50)
    
    # Show configuration summary
    config_manager = ConfigManager()
    config_summary = config_manager.get_config_summary(config)
    print("\nConfiguration:")
    print(config_summary)
    
    # Show strategy summary
    print("\nStrategy Summary:")
    strategy_summary = orchestrator.get_strategy_summary()
    print(strategy_summary)
    
    # Show planned output files
    print("\nOutput Files:")
    print("  - trades.csv (standard format)")
    print("  - detailed_trades.csv (all fields)")
    print("  - consolidated_trades.csv (with strategy names)")
    
    print("\nDry run completed successfully!")


def main():
    """Main entry point."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Configure logging based on CLI arguments
        configure_logging(args)
        
        logger.info("Trading MVP starting...")
        
        # Load and validate configuration
        config_manager = ConfigManager()
        config = config_manager.load_config(args.config)
        
        # Apply CLI overrides
        config = config_manager.apply_cli_overrides(config, args)
        
        # Override data mode if specified
        if hasattr(args, 'data_mode') and args.data_mode:
            config['data_mode'] = args.data_mode
            logger.info(f"CLI override: data_mode = {args.data_mode}")
        
        # Override initial capital if specified
        if hasattr(args, 'initial_capital') and args.initial_capital:
            config['initial_capital'] = args.initial_capital
            logger.info(f"CLI override: initial_capital = ${args.initial_capital:,.2f}")
        
        # Show configuration summary
        logger.info(f"Configuration summary:\n{config_manager.get_config_summary(config)}")
        
        # Initialize price fetcher
        price_fetcher = initialize_price_fetcher(config)
        
        # Initialize orchestrator
        orchestrator = TradingOrchestrator(config, price_fetcher)
        
        # Handle special modes
        if hasattr(args, 'health_check') and args.health_check:
            success = perform_health_check(orchestrator)
            sys.exit(0 if success else 1)
        
        if hasattr(args, 'dry_run') and args.dry_run:
            perform_dry_run(config, orchestrator)
            sys.exit(0)
        
        # Perform health check unless skipped
        if not (hasattr(args, 'skip_health_check') and args.skip_health_check):
            health_ok = perform_health_check(orchestrator)
            if not health_ok:
                logger.warning("Health check found issues, but continuing...")
        
        # Run simulation
        weeks = getattr(args, 'weeks', 52)
        logger.info(f"Starting {weeks}-week trading simulation...")
        
        trades = orchestrator.execute_simulation(weeks=weeks)
        
        # Prepare output files
        output_files = {}
        
        if hasattr(args, 'output'):
            output_files['standard'] = args.output
        
        if hasattr(args, 'detailed_output') and not getattr(args, 'no_detailed', False):
            output_files['detailed'] = args.detailed_output
        
        if hasattr(args, 'consolidated_output') and not getattr(args, 'no_consolidated', False):
            output_files['consolidated'] = args.consolidated_output
        
        # Save results
        orchestrator.save_trades_to_files(trades, output_files)
        
        # Show final summary
        print("\nSimulation Results:")
        print("=" * 50)
        print(f"Total Trades: {len(trades)}")
        
        strategy_summary = orchestrator.get_strategy_summary()
        print(f"\nStrategy Performance:")
        print(strategy_summary)
        
        print(f"\nOutput Files:")
        for format_name, filename in output_files.items():
            print(f"  {format_name.title()}: {filename}")
        
        logger.info("Trading simulation completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
        sys.exit(130)  # Standard exit code for Ctrl+C
        
    except (CLIError, ConfigError, OrchestrationError, DataSourceError) as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()