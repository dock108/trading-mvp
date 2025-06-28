"""
Unit tests for the Configuration management module.

Tests cover:
- Configuration loading and validation
- Default configuration handling
- CLI override integration
- Error handling and validation
- Capital allocation calculations
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock

from core.config import ConfigManager, ConfigError, load_config, get_default_config


class TestConfigManager:
    """Test suite for ConfigManager class."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.config_manager = ConfigManager()

    def test_get_default_config(self):
        """Test default configuration generation."""
        default_config = self.config_manager.get_default_config()
        
        # Check required fields exist
        assert 'initial_capital' in default_config
        assert 'strategies' in default_config
        assert 'allocation' in default_config
        assert 'wheel_symbols' in default_config
        assert 'rotator_symbols' in default_config
        assert 'data_mode' in default_config
        
        # Check data types
        assert isinstance(default_config['initial_capital'], (int, float))
        assert isinstance(default_config['strategies'], dict)
        assert isinstance(default_config['allocation'], dict)
        assert isinstance(default_config['wheel_symbols'], list)
        assert isinstance(default_config['rotator_symbols'], list)
        
        # Check default values
        assert default_config['initial_capital'] == 100000
        assert default_config['data_mode'] == 'mock'
        assert len(default_config['wheel_symbols']) > 0
        assert len(default_config['rotator_symbols']) > 0

    def test_load_valid_config(self):
        """Test loading valid configuration file."""
        # Create temporary config file
        config_data = {
            'initial_capital': 50000,
            'strategies': {'wheel': True, 'rotator': False},
            'allocation': {'wheel': 1.0, 'rotator': 0.0}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = self.config_manager.load_config(config_path)
            
            # Check loaded values
            assert config['initial_capital'] == 50000
            assert config['strategies']['wheel'] is True
            assert config['strategies']['rotator'] is False
            
            # Check defaults were applied
            assert 'wheel_symbols' in config
            assert 'data_mode' in config
            
        finally:
            Path(config_path).unlink()

    def test_load_nonexistent_config(self):
        """Test loading nonexistent configuration file."""
        with pytest.raises(ConfigError, match="Config file .* not found"):
            self.config_manager.load_config("/nonexistent/config.yaml")

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [unclosed")
            config_path = f.name
        
        try:
            with pytest.raises(ConfigError, match="Error parsing config file"):
                self.config_manager.load_config(config_path)
        finally:
            Path(config_path).unlink()

    def test_validate_missing_required_field(self):
        """Test validation with missing required fields."""
        incomplete_config = {
            'strategies': {'wheel': True},
            # Missing initial_capital and allocation
        }
        
        with pytest.raises(ConfigError, match="Missing required configuration field"):
            self.config_manager.validate_and_apply_defaults(incomplete_config)

    def test_validate_negative_capital(self):
        """Test validation with negative capital."""
        invalid_config = {
            'initial_capital': -1000,
            'strategies': {'wheel': True},
            'allocation': {'wheel': 1.0}
        }
        
        with pytest.raises(ConfigError, match="initial_capital must be positive"):
            self.config_manager.validate_and_apply_defaults(invalid_config)

    def test_validate_invalid_allocation_sum(self):
        """Test validation with invalid allocation sum."""
        invalid_config = {
            'initial_capital': 100000,
            'strategies': {'wheel': True, 'rotator': True},
            'allocation': {'wheel': 0.6, 'rotator': 0.6}  # Sum = 1.2
        }
        
        with pytest.raises(ConfigError, match="Allocation percentages must sum to 1.0"):
            self.config_manager.validate_and_apply_defaults(invalid_config)

    def test_validate_single_strategy_allocation(self):
        """Test that single strategy doesn't require allocation validation."""
        config = {
            'initial_capital': 100000,
            'strategies': {'wheel': True, 'rotator': False},
            'allocation': {'wheel': 0.6, 'rotator': 0.4}  # Sum != 1.0 but only wheel enabled
        }
        
        # Should not raise error for single strategy
        validated = self.config_manager.validate_and_apply_defaults(config)
        assert validated['initial_capital'] == 100000

    def test_validate_empty_symbol_list(self):
        """Test validation with empty symbol lists."""
        invalid_config = {
            'initial_capital': 100000,
            'strategies': {'wheel': True, 'rotator': False},
            'allocation': {'wheel': 1.0, 'rotator': 0.0},
            'wheel_symbols': []  # Empty list
        }
        
        with pytest.raises(ConfigError, match="wheel_symbols cannot be empty"):
            self.config_manager.validate_and_apply_defaults(invalid_config)

    def test_validate_invalid_data_mode(self):
        """Test validation with invalid data mode."""
        invalid_config = {
            'initial_capital': 100000,
            'strategies': {'wheel': True, 'rotator': False},
            'allocation': {'wheel': 1.0, 'rotator': 0.0},
            'data_mode': 'invalid_mode'
        }
        
        with pytest.raises(ConfigError, match="data_mode must be one of"):
            self.config_manager.validate_and_apply_defaults(invalid_config)

    def test_apply_cli_overrides(self):
        """Test applying CLI overrides to configuration."""
        config = {
            'initial_capital': 100000,
            'strategies': {'wheel': True, 'rotator': True},
            'allocation': {'wheel': 0.5, 'rotator': 0.5}
        }
        
        # Mock CLI args
        args = Mock()
        args.wheel = False
        args.rotator = True
        args.config = 'custom.yaml'
        
        updated_config = self.config_manager.apply_cli_overrides(config, args)
        
        # Check overrides were applied
        assert updated_config['strategies']['wheel'] is False
        assert updated_config['strategies']['rotator'] is True
        
        # Original config should be unchanged
        assert config['strategies']['wheel'] is True

    def test_apply_cli_overrides_none_values(self):
        """Test CLI overrides with None values (no override)."""
        config = {
            'strategies': {'wheel': True, 'rotator': False}
        }
        
        # Mock CLI args with None values
        args = Mock()
        args.wheel = None
        args.rotator = None
        
        updated_config = self.config_manager.apply_cli_overrides(config, args)
        
        # Values should remain unchanged
        assert updated_config['strategies']['wheel'] is True
        assert updated_config['strategies']['rotator'] is False

    def test_get_enabled_strategies(self):
        """Test getting enabled strategies."""
        config = {
            'strategies': {
                'wheel': True,
                'rotator': False,
                'momentum': True
            }
        }
        
        enabled = self.config_manager.get_enabled_strategies(config)
        
        assert len(enabled) == 2
        assert enabled['wheel'] is True
        assert enabled['momentum'] is True
        assert 'rotator' not in enabled

    def test_calculate_strategy_allocation_single(self):
        """Test capital allocation calculation for single strategy."""
        config = {
            'strategies': {'wheel': True, 'rotator': False},
            'allocation': {'wheel': 0.6, 'rotator': 0.4}
        }
        
        allocations = self.config_manager.calculate_strategy_allocation(config)
        
        # Single strategy should get 100%
        assert len(allocations) == 1
        assert allocations['wheel'] == 1.0

    def test_calculate_strategy_allocation_multiple(self):
        """Test capital allocation calculation for multiple strategies."""
        config = {
            'strategies': {'wheel': True, 'rotator': True},
            'allocation': {'wheel': 0.7, 'rotator': 0.3}
        }
        
        allocations = self.config_manager.calculate_strategy_allocation(config)
        
        # Multiple strategies use configured allocations
        assert len(allocations) == 2
        assert allocations['wheel'] == 0.7
        assert allocations['rotator'] == 0.3

    def test_get_strategy_capital(self):
        """Test getting capital allocation for specific strategy."""
        config = {
            'initial_capital': 100000,
            'strategies': {'wheel': True, 'rotator': True},
            'allocation': {'wheel': 0.6, 'rotator': 0.4}
        }
        
        wheel_capital = self.config_manager.get_strategy_capital(config, 'wheel')
        rotator_capital = self.config_manager.get_strategy_capital(config, 'rotator')
        
        assert wheel_capital == 60000  # 100k * 0.6
        assert rotator_capital == 40000  # 100k * 0.4

    def test_get_config_summary(self):
        """Test configuration summary generation."""
        config = {
            'initial_capital': 250000,
            'data_mode': 'live',
            'strategies': {'wheel': True, 'rotator': False},
            'allocation': {'wheel': 1.0, 'rotator': 0.0}
        }
        
        summary = self.config_manager.get_config_summary(config)
        
        assert "Initial Capital: $250,000.00" in summary
        assert "Data Mode: live" in summary
        assert "Enabled Strategies: 1" in summary
        assert "wheel: 100.0%" in summary

    def test_deep_merge(self):
        """Test deep merging of dictionaries."""
        base = {
            'a': 1,
            'b': {
                'c': 2,
                'd': 3
            },
            'e': 4
        }
        
        override = {
            'b': {
                'd': 30,  # Override existing
                'f': 5    # Add new
            },
            'g': 6        # Add new top-level
        }
        
        result = self.config_manager._deep_merge(base, override)
        
        assert result['a'] == 1      # Unchanged
        assert result['b']['c'] == 2 # Unchanged nested
        assert result['b']['d'] == 30 # Overridden nested
        assert result['b']['f'] == 5  # Added nested
        assert result['e'] == 4      # Unchanged
        assert result['g'] == 6      # Added top-level


class TestConfigConvenienceFunctions:
    """Test convenience functions for configuration management."""

    def test_load_config_function(self):
        """Test load_config convenience function."""
        # Create temporary config file
        config_data = {
            'initial_capital': 75000,
            'strategies': {'wheel': True, 'rotator': False},
            'allocation': {'wheel': 1.0, 'rotator': 0.0}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            assert config['initial_capital'] == 75000
        finally:
            Path(config_path).unlink()

    def test_get_default_config_function(self):
        """Test get_default_config convenience function."""
        default_config = get_default_config()
        
        assert isinstance(default_config, dict)
        assert 'initial_capital' in default_config
        assert default_config['initial_capital'] == 100000


class TestConfigValidationEdgeCases:
    """Test edge cases in configuration validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()

    def test_allocation_tolerance(self):
        """Test allocation sum tolerance for floating point errors."""
        config = {
            'initial_capital': 100000,
            'strategies': {'wheel': True, 'rotator': True},
            'allocation': {'wheel': 0.6, 'rotator': 0.4000001}  # Sum = 1.0000001
        }
        
        # Should not raise error due to tolerance
        validated = self.config_manager.validate_and_apply_defaults(config)
        assert validated['initial_capital'] == 100000

    def test_strategies_not_dict(self):
        """Test validation when strategies is not a dictionary."""
        invalid_config = {
            'initial_capital': 100000,
            'strategies': ['wheel', 'rotator'],  # Should be dict
            'allocation': {'wheel': 1.0}
        }
        
        with pytest.raises(ConfigError, match="strategies must be a dictionary"):
            self.config_manager.validate_and_apply_defaults(invalid_config)

    def test_allocation_not_dict(self):
        """Test validation when allocation is not a dictionary."""
        invalid_config = {
            'initial_capital': 100000,
            'strategies': {'wheel': True},
            'allocation': 0.5  # Should be dict
        }
        
        with pytest.raises(ConfigError, match="allocation must be a dictionary"):
            self.config_manager.validate_and_apply_defaults(invalid_config)

    def test_symbol_list_not_list(self):
        """Test validation when symbol list is not a list."""
        invalid_config = {
            'initial_capital': 100000,
            'strategies': {'wheel': True, 'rotator': False},
            'allocation': {'wheel': 1.0, 'rotator': 0.0},
            'wheel_symbols': 'SPY,QQQ,IWM'  # Should be list
        }
        
        with pytest.raises(ConfigError, match="wheel_symbols must be a list"):
            self.config_manager.validate_and_apply_defaults(invalid_config)