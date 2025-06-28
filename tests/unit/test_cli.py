"""
Unit tests for the CLI module.

Tests cover:
- Argument parsing and validation
- Help text generation
- Error handling
- Logging configuration
- CLI flag combinations
"""

import pytest
import sys
import logging
from io import StringIO
from unittest.mock import Mock, patch

from core.cli import TradingCLI, CLIError, parse_args, configure_logging


class TestTradingCLI:
    """Test suite for TradingCLI class."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.cli = TradingCLI()

    def test_cli_initialization(self):
        """Test CLI initialization."""
        assert self.cli.prog_name == "Trading MVP"
        assert self.cli.parser is not None

    def test_basic_argument_parsing(self):
        """Test parsing basic arguments."""
        args = self.cli.parse_args(['--backtest'])
        
        assert args.backtest is True
        assert args.config == 'config/config.yaml'  # Default value

    def test_strategy_flags(self):
        """Test strategy enable/disable flags."""
        # Test enabling wheel strategy
        args = self.cli.parse_args(['--wheel'])
        assert args.wheel is True
        
        # Test disabling wheel strategy
        args = self.cli.parse_args(['--no-wheel'])
        assert args.wheel is False
        
        # Test enabling rotator strategy
        args = self.cli.parse_args(['--rotator'])
        assert args.rotator is True
        
        # Test disabling rotator strategy
        args = self.cli.parse_args(['--no-rotator'])
        assert args.rotator is False

    def test_strategy_flags_default_none(self):
        """Test that strategy flags default to None when not specified."""
        args = self.cli.parse_args(['--backtest'])
        
        assert args.wheel is None
        assert args.rotator is None

    def test_config_file_override(self):
        """Test configuration file path override."""
        args = self.cli.parse_args(['--config', 'custom/config.yaml'])
        
        assert args.config == 'custom/config.yaml'

    def test_output_file_options(self):
        """Test output file configuration options."""
        args = self.cli.parse_args([
            '--output', 'custom_trades.csv',
            '--detailed-output', 'custom_detailed.csv',
            '--consolidated-output', 'custom_consolidated.csv'
        ])
        
        assert args.output == 'custom_trades.csv'
        assert args.detailed_output == 'custom_detailed.csv'
        assert args.consolidated_output == 'custom_consolidated.csv'

    def test_output_disable_flags(self):
        """Test flags to disable output files."""
        args = self.cli.parse_args(['--no-detailed', '--no-consolidated'])
        
        assert args.no_detailed is True
        assert args.no_consolidated is True

    def test_verbosity_levels(self):
        """Test verbosity level options."""
        # Test single verbose flag
        args = self.cli.parse_args(['-v'])
        assert args.verbose == 1
        
        # Test multiple verbose flags
        args = self.cli.parse_args(['-vvv'])
        assert args.verbose == 3
        
        # Test quiet flag
        args = self.cli.parse_args(['-q'])
        assert args.quiet is True

    def test_data_mode_options(self):
        """Test data mode selection."""
        for mode in ['mock', 'live', 'hybrid']:
            args = self.cli.parse_args(['--data-mode', mode])
            assert args.data_mode == mode

    def test_health_check_options(self):
        """Test health check related options."""
        args = self.cli.parse_args(['--health-check'])
        assert args.health_check is True
        
        args = self.cli.parse_args(['--skip-health-check'])
        assert args.skip_health_check is True

    def test_simulation_parameters(self):
        """Test simulation parameter options."""
        args = self.cli.parse_args([
            '--weeks', '26',
            '--initial-capital', '250000'
        ])
        
        assert args.weeks == 26
        assert args.initial_capital == 250000.0

    def test_dry_run_flag(self):
        """Test dry run option."""
        args = self.cli.parse_args(['--dry-run'])
        assert args.dry_run is True

    def test_log_file_option(self):
        """Test log file specification."""
        args = self.cli.parse_args(['--log-file', 'trading.log'])
        assert args.log_file == 'trading.log'

    def test_help_flag(self):
        """Test that help flag works without error."""
        with pytest.raises(SystemExit) as exc_info:
            self.cli.parse_args(['--help'])
        
        # Help should exit with code 0
        assert exc_info.value.code == 0

    def test_invalid_data_mode(self):
        """Test invalid data mode raises error."""
        with pytest.raises((SystemExit, CLIError)):
            self.cli.parse_args(['--data-mode', 'invalid'])

    def test_validation_conflicting_verbosity(self):
        """Test validation of conflicting verbosity flags."""
        with pytest.raises(CLIError, match="Cannot use both --quiet and --verbose"):
            self.cli.parse_args(['--quiet', '--verbose'])

    def test_validation_negative_weeks(self):
        """Test validation of negative weeks."""
        with pytest.raises(CLIError, match="Number of weeks must be positive"):
            self.cli.parse_args(['--weeks', '-5'])

    def test_validation_large_weeks(self):
        """Test validation of unreasonably large weeks."""
        with pytest.raises(CLIError, match="Number of weeks seems unreasonably large"):
            self.cli.parse_args(['--weeks', '2000'])

    def test_validation_negative_capital(self):
        """Test validation of negative initial capital."""
        with pytest.raises(CLIError, match="Initial capital must be positive"):
            self.cli.parse_args(['--initial-capital', '-1000'])

    def test_validation_all_strategies_disabled(self):
        """Test validation when all strategies are disabled."""
        with pytest.raises(CLIError, match="Cannot disable all strategies"):
            self.cli.parse_args(['--no-wheel', '--no-rotator'])

    def test_complex_argument_combination(self):
        """Test complex combination of arguments."""
        args = self.cli.parse_args([
            '--backtest',
            '--wheel',
            '--no-rotator',
            '--config', 'test.yaml',
            '--output', 'test_trades.csv',
            '--weeks', '13',
            '--verbose',
            '--data-mode', 'live'
        ])
        
        assert args.backtest is True
        assert args.wheel is True
        assert args.rotator is False
        assert args.config == 'test.yaml'
        assert args.output == 'test_trades.csv'
        assert args.weeks == 13
        assert args.verbose == 1
        assert args.data_mode == 'live'


class TestLoggingConfiguration:
    """Test logging configuration functionality."""

    def test_configure_logging_quiet(self):
        """Test logging configuration in quiet mode."""
        args = Mock()
        args.quiet = True
        args.verbose = 0
        args.log_file = None
        
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        configure_logging(args)
        
        # Check that root logger level is ERROR
        assert logging.getLogger().level == logging.ERROR

    def test_configure_logging_verbose(self):
        """Test logging configuration in verbose mode."""
        args = Mock()
        args.quiet = False
        args.verbose = 1
        args.log_file = None
        
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        configure_logging(args)
        
        # Check that root logger level is DEBUG
        assert logging.getLogger().level == logging.DEBUG

    def test_configure_logging_very_verbose(self):
        """Test logging configuration in very verbose mode."""
        args = Mock()
        args.quiet = False
        args.verbose = 2
        args.log_file = None
        
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        configure_logging(args)
        
        # Check that root logger level is DEBUG
        assert logging.getLogger().level == logging.DEBUG
        
        # Check that format includes filename and line number
        handler = logging.getLogger().handlers[0]
        formatter = handler.formatter
        assert 'filename' in formatter._fmt

    def test_configure_logging_default(self):
        """Test default logging configuration."""
        args = Mock()
        args.quiet = False
        args.verbose = 0
        args.log_file = None
        
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        configure_logging(args)
        
        # Check that root logger level is INFO
        assert logging.getLogger().level == logging.INFO

    @patch('logging.FileHandler')
    def test_configure_logging_with_file(self, mock_file_handler):
        """Test logging configuration with file output."""
        args = Mock()
        args.quiet = False
        args.verbose = 0
        args.log_file = 'test.log'
        
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        # Mock file handler with proper level attribute
        mock_handler = Mock()
        mock_handler.level = logging.INFO
        mock_file_handler.return_value = mock_handler
        
        configure_logging(args)
        
        # Check that file handler was created
        mock_file_handler.assert_called_once_with('test.log')
        mock_handler.setLevel.assert_called_once()
        mock_handler.setFormatter.assert_called_once()

    def test_configure_logging_file_error(self):
        """Test logging configuration handles file errors gracefully."""
        args = Mock()
        args.quiet = False
        args.verbose = 0
        args.log_file = '/invalid/path/test.log'
        
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        # Should not raise exception even if file can't be created
        configure_logging(args)
        
        # Should still have console handler
        assert len(logging.getLogger().handlers) >= 1


class TestConvenienceFunctions:
    """Test convenience functions for CLI operations."""

    def test_parse_args_function(self):
        """Test parse_args convenience function."""
        args = parse_args(['--backtest', '--wheel'])
        
        assert args.backtest is True
        assert args.wheel is True

    @patch('core.cli.cli')
    def test_configure_logging_function(self, mock_cli):
        """Test configure_logging convenience function."""
        args = Mock()
        
        configure_logging(args)
        
        mock_cli.configure_logging.assert_called_once_with(args)


class TestCLIHelp:
    """Test CLI help and documentation features."""

    def test_examples_text_content(self):
        """Test that examples text contains expected content."""
        cli = TradingCLI()
        examples = cli._get_examples_text()
        
        # Check for key examples
        assert 'python main.py --backtest' in examples
        assert '--health-check' in examples
        assert '--dry-run' in examples
        assert 'config/config.yaml' in examples

    def test_print_version(self):
        """Test version printing."""
        cli = TradingCLI()
        
        with patch('builtins.print') as mock_print:
            cli.print_version()
            
        # Check that version info was printed
        assert mock_print.call_count >= 1
        call_args = str(mock_print.call_args_list)
        assert 'Trading MVP' in call_args

    def test_print_config_help(self):
        """Test configuration help printing."""
        cli = TradingCLI()
        
        with patch('builtins.print') as mock_print:
            cli.print_config_help()
            
        # Check that config help was printed
        assert mock_print.call_count >= 1
        call_args = str(mock_print.call_args_list)
        assert 'initial_capital' in call_args
        assert 'strategies' in call_args


class TestErrorHandling:
    """Test error handling in CLI operations."""

    def test_parse_args_with_invalid_argument(self):
        """Test parsing with invalid argument."""
        cli = TradingCLI()
        
        with pytest.raises(CLIError):
            cli.parse_args(['--invalid-argument'])

    def test_validation_with_valid_args(self):
        """Test validation passes with valid arguments."""
        cli = TradingCLI()
        
        # Create valid args object
        args = Mock()
        args.quiet = False
        args.verbose = 1
        args.weeks = 52
        args.initial_capital = 100000
        args.wheel = True
        args.rotator = None
        
        # Should not raise exception
        cli._validate_args(args)

    def test_cli_error_inheritance(self):
        """Test that CLIError inherits from Exception."""
        error = CLIError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"