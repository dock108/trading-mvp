"""
Unit tests for the Async Price Fetcher implementation.

Tests cover:
- Async HTTP operations with httpx
- Connection pooling and context management
- Concurrent price fetching
- Rate limiting with semaphores
- Error handling and retries
- Database integration
- FastAPI BackgroundTasks integration
"""

import pytest
import asyncio
import json
import httpx
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from data.async_price_fetcher import (
    AsyncPriceFetcher, 
    AsyncPriceFetcherWrapper,
    get_async_price_fetcher,
    get_sync_price_fetcher,
    fetch_crypto_prices_background,
    fetch_etf_prices_background
)


@pytest.mark.asyncio
class TestAsyncPriceFetcher:
    """Test suite for AsyncPriceFetcher class."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.fetcher = AsyncPriceFetcher(
            cache_dir="tests/temp_cache",
            crypto_rate_limit=10,
            etf_rate_limit=5,
            timeout=30.0
        )

    def teardown_method(self):
        """Clean up after each test."""
        # Clean up will be handled by test context managers

    async def test_context_manager(self):
        """Test async context manager functionality."""
        async with AsyncPriceFetcher() as fetcher:
            assert fetcher._client is not None
            # Client should be initialized when entering context
            await fetcher._ensure_client()
            assert isinstance(fetcher._client, httpx.AsyncClient)

    async def test_client_initialization(self):
        """Test HTTP client initialization with proper config."""
        await self.fetcher._ensure_client()
        
        assert self.fetcher._client is not None
        assert isinstance(self.fetcher._client, httpx.AsyncClient)
        
        # Check that client was initialized (limits are internal implementation)
        assert self.fetcher._client.timeout.read == 30.0

    async def test_client_cleanup(self):
        """Test proper cleanup of HTTP client."""
        await self.fetcher._ensure_client()
        assert self.fetcher._client is not None
        
        await self.fetcher.close()
        assert self.fetcher._client is None

    @patch('httpx.AsyncClient.get')
    async def test_get_crypto_price_success(self, mock_get):
        """Test successful crypto price fetching."""
        # Mock successful CoinGecko response
        mock_response = Mock()
        mock_response.json.return_value = {
            'bitcoin': {'usd': 50000.0}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        async with self.fetcher:
            price = await self.fetcher.get_crypto_price_async('bitcoin', 'usd')
            
        assert price == 50000.0
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    async def test_get_crypto_price_failure(self, mock_get):
        """Test crypto price fetching with API failure."""
        # Mock API failure
        mock_get.side_effect = httpx.HTTPStatusError(
            "Rate limit exceeded", 
            request=Mock(), 
            response=Mock(status_code=429)
        )

        async with self.fetcher:
            price = await self.fetcher.get_crypto_price_async('bitcoin', 'usd')
            
        assert price is None

    @patch('asyncio.to_thread')
    async def test_get_etf_price_success(self, mock_to_thread):
        """Test successful ETF price fetching using yfinance."""
        # Mock yfinance data structure
        mock_hist = pd.DataFrame({'Close': [450.0, 452.0, 448.0]})
        
        mock_ticker = Mock()
        
        # Mock the two asyncio.to_thread calls
        mock_to_thread.side_effect = [mock_ticker, mock_hist]

        async with self.fetcher:
            price = await self.fetcher.get_etf_price_async('SPY')
            
        assert price == 448.0  # Last price in mock data
        # Called for: Ticker creation, history call, and database logging
        assert mock_to_thread.call_count == 3

    @patch('asyncio.to_thread')
    @patch.object(AsyncPriceFetcher, '_get_alpha_vantage_price')
    async def test_get_etf_price_failure(self, mock_alpha_vantage, mock_to_thread):
        """Test ETF price fetching with yfinance failure."""
        # Mock yfinance failure
        mock_to_thread.side_effect = Exception("No data found")
        # Mock Alpha Vantage fallback failure
        mock_alpha_vantage.return_value = None

        async with self.fetcher:
            price = await self.fetcher.get_etf_price_async('SPY')
            
        assert price is None

    async def test_get_multiple_crypto_prices(self):
        """Test concurrent fetching of multiple crypto prices."""
        crypto_ids = ['bitcoin', 'ethereum', 'solana']
        
        with patch.object(self.fetcher, 'get_crypto_price_async') as mock_get_price:
            # Mock different prices for each crypto
            mock_get_price.side_effect = [50000.0, 3000.0, 100.0]
            
            async with self.fetcher:
                prices = await self.fetcher.get_multiple_crypto_prices_async(crypto_ids)
            
        assert len(prices) == 3
        assert prices['bitcoin'] == 50000.0
        assert prices['ethereum'] == 3000.0
        assert prices['solana'] == 100.0
        assert mock_get_price.call_count == 3

    async def test_get_multiple_crypto_prices_with_errors(self):
        """Test concurrent fetching with some errors."""
        crypto_ids = ['bitcoin', 'ethereum', 'invalid_coin']
        
        with patch.object(self.fetcher, 'get_crypto_price_async') as mock_get_price:
            # Mock success, success, failure
            mock_get_price.side_effect = [50000.0, 3000.0, Exception("Invalid coin")]
            
            async with self.fetcher:
                prices = await self.fetcher.get_multiple_crypto_prices_async(crypto_ids)
            
        assert len(prices) == 3
        assert prices['bitcoin'] == 50000.0
        assert prices['ethereum'] == 3000.0
        assert prices['invalid_coin'] is None

    async def test_get_multiple_etf_prices(self):
        """Test concurrent fetching of multiple ETF prices."""
        symbols = ['SPY', 'QQQ', 'IWM']
        
        with patch.object(self.fetcher, 'get_etf_price_async') as mock_get_price:
            # Mock different prices for each ETF
            mock_get_price.side_effect = [450.0, 380.0, 200.0]
            
            async with self.fetcher:
                prices = await self.fetcher.get_multiple_etf_prices_async(symbols)
            
        assert len(prices) == 3
        assert prices['SPY'] == 450.0
        assert prices['QQQ'] == 380.0
        assert prices['IWM'] == 200.0

    @patch('asyncio.to_thread')
    async def test_log_price_async(self, mock_to_thread):
        """Test async price logging to database."""
        mock_to_thread.return_value = None  # log_price_to_db returns None
        
        await self.fetcher._log_price_async('SPY', 450.0, 'test')
        
        mock_to_thread.assert_called_once()
        args, kwargs = mock_to_thread.call_args
        assert kwargs['symbol'] == 'SPY'
        assert kwargs['price'] == 450.0
        assert kwargs['source'] == 'test'

    async def test_rate_limiting_semaphores(self):
        """Test that rate limiting semaphores are respected."""
        # Test crypto semaphore
        assert self.fetcher._crypto_semaphore._value == 10
        
        # Test ETF semaphore  
        assert self.fetcher._etf_semaphore._value == 5
        
        # Test acquiring semaphore
        async with self.fetcher._crypto_semaphore:
            assert self.fetcher._crypto_semaphore._value == 9

    @patch('httpx.AsyncClient.get')
    async def test_health_check_coingecko_success(self, mock_get):
        """Test health check for CoinGecko API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        async with self.fetcher:
            health = await self.fetcher.health_check_async()
            
        assert 'coingecko' in health
        assert health['coingecko'] == '✅ Working'

    @patch('httpx.AsyncClient.get')
    async def test_health_check_coingecko_failure(self, mock_get):
        """Test health check with CoinGecko API failure."""
        mock_get.side_effect = Exception("Connection failed")

        async with self.fetcher:
            health = await self.fetcher.health_check_async()
            
        assert 'coingecko' in health
        assert 'Error' in health['coingecko']

    @patch('httpx.AsyncClient.get')
    async def test_health_check_alpha_vantage(self, mock_get):
        """Test health check for Alpha Vantage API."""
        # Set API key for testing
        self.fetcher.alpha_vantage_api_key = "test_key"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        async with self.fetcher:
            health = await self.fetcher.health_check_async()
            
        assert 'alpha_vantage' in health
        assert health['alpha_vantage'] == '✅ Working'

    @patch('asyncio.to_thread')
    async def test_health_check_yfinance(self, mock_to_thread):
        """Test health check for yfinance."""
        # Mock successful yfinance call
        mock_hist = Mock()
        mock_hist.empty = False
        mock_to_thread.side_effect = [Mock(), mock_hist]  # Ticker, then history

        async with self.fetcher:
            health = await self.fetcher.health_check_async()
            
        assert 'yfinance' in health
        assert health['yfinance'] == '✅ Working'

    @patch('httpx.AsyncClient.get')
    async def test_alpha_vantage_fallback(self, mock_get):
        """Test Alpha Vantage fallback functionality."""
        self.fetcher.alpha_vantage_api_key = "test_key"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'Global Quote': {
                '05. price': '450.50'
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        async with self.fetcher:
            price = await self.fetcher._get_alpha_vantage_price('SPY')
            
        assert price == 450.50

    async def test_concurrent_operations_performance(self):
        """Test performance of concurrent operations."""
        crypto_ids = ['bitcoin', 'ethereum', 'litecoin']
        
        with patch.object(self.fetcher, 'get_crypto_price_async') as mock_get_price:
            # Mock async delay to simulate real API calls
            async def mock_fetch(crypto_id, vs_currency='usd'):
                await asyncio.sleep(0.1)  # Simulate network delay
                return 1000.0
            
            mock_get_price.side_effect = mock_fetch
            
            start_time = asyncio.get_event_loop().time()
            
            async with self.fetcher:
                prices = await self.fetcher.get_multiple_crypto_prices_async(crypto_ids)
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
        # Concurrent execution should be faster than sequential
        assert duration < 0.25  # Should be close to 0.1s, not 0.3s
        assert len(prices) == 3


class TestAsyncPriceFetcherWrapper:
    """Test suite for sync wrapper of AsyncPriceFetcher."""

    def setup_method(self):
        """Set up test fixtures."""
        self.async_fetcher = AsyncPriceFetcher()
        self.wrapper = AsyncPriceFetcherWrapper(self.async_fetcher)

    def test_sync_wrapper_initialization(self):
        """Test sync wrapper initialization."""
        assert self.wrapper.async_fetcher is self.async_fetcher
        assert self.wrapper._loop is None

    @patch.object(AsyncPriceFetcher, 'get_crypto_price_async')
    def test_sync_get_crypto_price(self, mock_async_method):
        """Test sync wrapper for crypto price fetching."""
        mock_async_method.return_value = asyncio.Future()
        mock_async_method.return_value.set_result(50000.0)
        
        with patch.object(self.wrapper, '_run_async') as mock_run_async:
            mock_run_async.return_value = 50000.0
            
            price = self.wrapper.get_crypto_price('bitcoin', 'usd')
            
        assert price == 50000.0
        mock_run_async.assert_called_once()

    @patch.object(AsyncPriceFetcher, 'get_etf_price_async')
    def test_sync_get_etf_price(self, mock_async_method):
        """Test sync wrapper for ETF price fetching."""
        with patch.object(self.wrapper, '_run_async') as mock_run_async:
            mock_run_async.return_value = 450.0
            
            price = self.wrapper.get_etf_price('SPY')
            
        assert price == 450.0

    @patch.object(AsyncPriceFetcher, 'health_check_async')
    def test_sync_health_check(self, mock_async_method):
        """Test sync wrapper for health check."""
        with patch.object(self.wrapper, '_run_async') as mock_run_async:
            mock_run_async.return_value = {'coingecko': '✅ Working'}
            
            health = self.wrapper.health_check()
            
        assert isinstance(health, dict)
        assert 'coingecko' in health


class TestGlobalInstances:
    """Test global instance management functions."""

    def test_get_async_price_fetcher_singleton(self):
        """Test that get_async_price_fetcher returns singleton."""
        fetcher1 = get_async_price_fetcher()
        fetcher2 = get_async_price_fetcher()
        
        assert fetcher1 is fetcher2

    def test_get_sync_price_fetcher_singleton(self):
        """Test that get_sync_price_fetcher returns singleton."""
        wrapper1 = get_sync_price_fetcher()
        wrapper2 = get_sync_price_fetcher()
        
        assert wrapper1 is wrapper2

    def test_get_async_price_fetcher_with_params(self):
        """Test async fetcher creation with custom parameters."""
        fetcher = get_async_price_fetcher(
            cache_dir="test_cache",
            crypto_rate_limit=5
        )
        
        assert isinstance(fetcher, AsyncPriceFetcher)


@pytest.mark.asyncio
class TestFastAPIIntegration:
    """Test FastAPI background task integration."""

    async def test_fetch_crypto_prices_background(self):
        """Test background crypto price fetching function."""
        crypto_ids = ['bitcoin', 'ethereum']
        
        with patch.object(AsyncPriceFetcher, 'get_multiple_crypto_prices_async') as mock_fetch:
            mock_fetch.return_value = {'bitcoin': 50000.0, 'ethereum': 3000.0}
            
            result = await fetch_crypto_prices_background(crypto_ids)
            
        assert result == {'bitcoin': 50000.0, 'ethereum': 3000.0}

    async def test_fetch_etf_prices_background(self):
        """Test background ETF price fetching function."""
        symbols = ['SPY', 'QQQ']
        
        with patch.object(AsyncPriceFetcher, 'get_multiple_etf_prices_async') as mock_fetch:
            mock_fetch.return_value = {'SPY': 450.0, 'QQQ': 380.0}
            
            result = await fetch_etf_prices_background(symbols)
            
        assert result == {'SPY': 450.0, 'QQQ': 380.0}


@pytest.mark.asyncio
class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    async def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        fetcher = AsyncPriceFetcher(timeout=0.001)  # Very short timeout
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timed out")
            
            async with fetcher:
                price = await fetcher.get_crypto_price_async('bitcoin')
                
        assert price is None

    async def test_invalid_json_response(self):
        """Test handling of invalid JSON responses."""
        fetcher = AsyncPriceFetcher()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            async with fetcher:
                price = await fetcher.get_crypto_price_async('bitcoin')
                
        assert price is None

    async def test_database_logging_failure(self):
        """Test graceful handling of database logging failures."""
        fetcher = AsyncPriceFetcher()
        
        with patch('asyncio.to_thread') as mock_to_thread:
            mock_to_thread.side_effect = Exception("Database error")
            
            # Should not raise exception, just log error
            await fetcher._log_price_async('SPY', 450.0, 'test')
            
            mock_to_thread.assert_called_once()


@pytest.mark.asyncio
class TestCacheOperations:
    """Test async cache operations."""

    async def test_cache_data_async(self):
        """Test async data caching."""
        import tempfile
        from pathlib import Path
        
        fetcher = AsyncPriceFetcher()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "test_cache.json"
            test_data = {"test": "data"}
            
            await fetcher._cache_data_async(cache_file, test_data)
            
            # Verify file was created and contains correct data
            assert cache_file.exists()
            
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            assert cached_data == test_data

    async def test_cache_data_failure_handling(self):
        """Test cache operation failure handling."""
        from pathlib import Path
        
        fetcher = AsyncPriceFetcher()
        
        # Try to cache to invalid path
        invalid_path = Path("/invalid/path/cache.json")
        
        # Should not raise exception, just log error
        await fetcher._cache_data_async(invalid_path, {"test": "data"})