"""
Configuration management for trading MVP.

This module handles:
- YAML configuration loading and validation
- Default configuration values
- Environment variable integration
- Configuration validation and error handling
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configuration constants
ALLOCATION_TOLERANCE = 0.01  # Allow small floating point errors in allocation percentages
DEFAULT_INITIAL_CAPITAL = 100000
DEFAULT_CONFIG_PATH = "config/config.yaml"


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class ConfigManager:
    """Manages configuration loading, validation, and defaults."""
    
    def __init__(self):
        """Initialize config manager."""
        self._config = None
        self._config_path = None
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
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
            'rotator_symbols': ['BTC', 'ETH', 'SOL'],
            'data_mode': 'mock',  # 'mock', 'live', or 'hybrid'
            'data_sources': {
                'crypto': {
                    'primary': 'coingecko',
                    'symbols': {
                        'BTC': 'bitcoin',
                        'ETH': 'ethereum',
                        'SOL': 'solana'
                    },
                    'rate_limit_per_minute': 10,
                    'timeout_seconds': 30
                },
                'etf': {
                    'primary': 'yfinance',
                    'secondary': 'alpha_vantage',
                    'symbols': {
                        'SPY': 'SPY',
                        'QQQ': 'QQQ',
                        'IWM': 'IWM'
                    },
                    'rate_limit_per_minute': 5,
                    'timeout_seconds': 30
                }
            },
            'fallback_strategy': {
                'on_api_failure': 'use_cached',
                'cache_expiry_minutes': 60,
                'enable_mock_fallback': True
            }
        }
    
    def load_config(self, config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
        """Load configuration from YAML file with validation and defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            dict: Loaded and validated configuration
            
        Raises:
            ConfigError: If configuration loading or validation fails
        """
        self._config_path = config_path
        
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise ConfigError(f"Config file '{config_path}' not found.")
            
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                
        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing config file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading config file: {e}")
        
        # Validate and apply defaults
        config = self.validate_and_apply_defaults(config)
        self._config = config
        
        logger.info(f"Configuration loaded from {config_path}")
        return config
    
    def validate_and_apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration and apply defaults for missing values.
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            dict: Validated configuration with defaults applied
            
        Raises:
            ConfigError: If validation fails
        """
        # Validate required fields in provided config before merging defaults
        required_fields = ['initial_capital', 'strategies', 'allocation']
        for field in required_fields:
            if field not in config:
                raise ConfigError(f"Missing required configuration field: {field}")
        
        # Start with defaults and update with provided config
        default_config = self.get_default_config()
        validated_config = self._deep_merge(default_config, config)
        
        # Validate capital is positive
        if validated_config['initial_capital'] <= 0:
            raise ConfigError("initial_capital must be positive")
        
        # Validate strategies configuration
        strategies = validated_config.get('strategies', {})
        if not isinstance(strategies, dict):
            raise ConfigError("strategies must be a dictionary")
        
        # Validate allocation configuration
        allocation = validated_config.get('allocation', {})
        if not isinstance(allocation, dict):
            raise ConfigError("allocation must be a dictionary")
        
        # Validate allocation percentages sum to approximately 1.0
        enabled_strategies = [name for name, enabled in strategies.items() if enabled]
        if len(enabled_strategies) > 1:
            total_allocation = sum(allocation.get(strategy, 0) for strategy in enabled_strategies)
            if abs(total_allocation - 1.0) > ALLOCATION_TOLERANCE:
                raise ConfigError(
                    f"Allocation percentages must sum to 1.0 for multiple strategies. "
                    f"Current sum: {total_allocation:.3f}"
                )
        
        # Validate symbol lists
        for symbol_field in ['wheel_symbols', 'rotator_symbols']:
            if symbol_field in validated_config:
                if not isinstance(validated_config[symbol_field], list):
                    raise ConfigError(f"{symbol_field} must be a list")
                if not validated_config[symbol_field]:
                    raise ConfigError(f"{symbol_field} cannot be empty")
        
        # Validate data mode
        valid_data_modes = ['mock', 'live', 'hybrid']
        data_mode = validated_config.get('data_mode', 'mock')
        if data_mode not in valid_data_modes:
            raise ConfigError(f"data_mode must be one of {valid_data_modes}")
        
        logger.debug("Configuration validation completed successfully")
        return validated_config
    
    def apply_cli_overrides(self, config: Dict[str, Any], args: Any) -> Dict[str, Any]:
        """Apply CLI argument overrides to configuration.
        
        Args:
            config: Base configuration
            args: Parsed CLI arguments
            
        Returns:
            dict: Configuration with CLI overrides applied
        """
        # Create a deep copy to avoid modifying original
        import copy
        config = copy.deepcopy(config)
        
        # Override strategy enabling/disabling
        if hasattr(args, 'wheel') and args.wheel is not None:
            config['strategies']['wheel'] = args.wheel
            logger.info(f"CLI override: wheel strategy {'enabled' if args.wheel else 'disabled'}")
        
        if hasattr(args, 'rotator') and args.rotator is not None:
            config['strategies']['rotator'] = args.rotator
            logger.info(f"CLI override: rotator strategy {'enabled' if args.rotator else 'disabled'}")
        
        # Override config file path
        if hasattr(args, 'config') and args.config:
            self._config_path = args.config
        
        return config
    
    def get_enabled_strategies(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """Get list of enabled strategies from configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            dict: Mapping of strategy names to enabled status
        """
        strategies = config.get('strategies', {})
        return {name: enabled for name, enabled in strategies.items() if enabled}
    
    def calculate_strategy_allocation(self, config: Dict[str, Any]) -> Dict[str, float]:
        """Calculate capital allocation for each enabled strategy.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            dict: Mapping of strategy names to capital allocation
        """
        enabled_strategies = self.get_enabled_strategies(config)
        allocation_config = config.get('allocation', {})
        
        if len(enabled_strategies) == 1:
            # Single strategy gets all capital
            strategy_name = list(enabled_strategies.keys())[0]
            return {strategy_name: 1.0}
        
        # Multiple strategies use configured allocations
        strategy_allocations = {}
        for strategy_name in enabled_strategies:
            allocation = allocation_config.get(strategy_name, 0.0)
            strategy_allocations[strategy_name] = allocation
        
        return strategy_allocations
    
    def get_strategy_capital(self, config: Dict[str, Any], strategy_name: str) -> float:
        """Get capital allocation for a specific strategy.
        
        Args:
            config: Configuration dictionary
            strategy_name: Name of strategy
            
        Returns:
            float: Capital allocated to strategy
        """
        initial_capital = config.get('initial_capital', DEFAULT_INITIAL_CAPITAL)
        allocations = self.calculate_strategy_allocation(config)
        allocation_pct = allocations.get(strategy_name, 0.0)
        
        return initial_capital * allocation_pct
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            dict: Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_config_summary(self, config: Dict[str, Any]) -> str:
        """Generate a human-readable configuration summary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            str: Configuration summary
        """
        enabled_strategies = self.get_enabled_strategies(config)
        allocations = self.calculate_strategy_allocation(config)
        
        summary_lines = [
            f"Initial Capital: ${config.get('initial_capital', 0):,.2f}",
            f"Data Mode: {config.get('data_mode', 'unknown')}",
            f"Enabled Strategies: {len(enabled_strategies)}"
        ]
        
        for strategy_name, allocation in allocations.items():
            capital = config.get('initial_capital', 0) * allocation
            summary_lines.append(f"  - {strategy_name}: {allocation:.1%} (${capital:,.2f})")
        
        return "\n".join(summary_lines)


# Global config manager instance
config_manager = ConfigManager()


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Convenience function to load configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        dict: Loaded configuration
    """
    return config_manager.load_config(config_path)


def get_default_config() -> Dict[str, Any]:
    """Convenience function to get default configuration.
    
    Returns:
        dict: Default configuration
    """
    return ConfigManager.get_default_config()