"""
Asynchronous Market Data Fetcher

This module provides async/await-based market data fetching with:
- httpx.AsyncClient for non-blocking HTTP requests
- Connection pooling and keep-alive
- Concurrent API calls for multiple symbols
- Integration with FastAPI BackgroundTasks
- Backward compatibility with sync interfaces
"""

import asyncio
import aiofiles
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import os

import httpx
import yfinance as yf
from dotenv import load_dotenv

from .database import get_database, log_price_to_db

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AsyncPriceFetcher:
    """
    Asynchronous price fetcher with concurrent API support.
    
    Features:
    - Async HTTP requests using httpx
    - Connection pooling for efficiency
    - Concurrent fetching of multiple symbols
    - Automatic caching and database logging
    - Rate limiting and retry logic
    """
    
    def __init__(
        self,
        cache_dir: str = "data/cache",
        crypto_rate_limit: int = 10,  # requests per minute
        etf_rate_limit: int = 5,      # requests per minute
        timeout: float = 30.0
    ):
        """
        Initialize async price fetcher.
        
        Args:
            cache_dir: Directory for caching data
            crypto_rate_limit: Max crypto API calls per minute
            etf_rate_limit: Max ETF API calls per minute
            timeout: HTTP request timeout in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.crypto_rate_limit = crypto_rate_limit
        self.etf_rate_limit = etf_rate_limit
        self.timeout = timeout
        
        # API configuration
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        # Rate limiting semaphores
        self._crypto_semaphore = asyncio.Semaphore(crypto_rate_limit)
        self._etf_semaphore = asyncio.Semaphore(etf_rate_limit)
        
        # HTTP client (will be initialized when needed)
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"AsyncPriceFetcher initialized with {crypto_rate_limit} crypto, "
                   f"{etf_rate_limit} ETF rate limits")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self._client is None:
            # Configure HTTP client with connection pooling
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            )
            
            timeout = httpx.Timeout(self.timeout)
            
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                headers={
                    'User-Agent': 'TradingMVP/1.0 (Async Price Fetcher)'
                }
            )
            
            logger.debug("HTTP client initialized with connection pooling")
    
    async def close(self):
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("HTTP client closed")
    
    async def get_crypto_price_async(
        self, 
        crypto_id: str, 
        vs_currency: str = 'usd'
    ) -> Optional[float]:
        """
        Fetch crypto price asynchronously from CoinGecko.
        
        Args:
            crypto_id: CoinGecko crypto ID (e.g., 'bitcoin')
            vs_currency: Target currency (default: 'usd')
            
        Returns:
            Current price or None if failed
        """
        async with self._crypto_semaphore:
            await self._ensure_client()
            
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': crypto_id,
                'vs_currencies': vs_currency
            }
            
            # Add API key if available
            if self.coingecko_api_key:
                params['x_cg_demo_api_key'] = self.coingecko_api_key
            
            try:
                logger.debug(f"Fetching crypto price for {crypto_id}")
                response = await self._client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                price = data.get(crypto_id, {}).get(vs_currency)
                
                if price:
                    # Log to database
                    await self._log_price_async(
                        symbol=crypto_id.upper(), 
                        price=price, 
                        source='coingecko'
                    )
                    logger.debug(f"Crypto price {crypto_id}: ${price:,.2f}")
                    return float(price)
                
            except httpx.HTTPStatusError as e:
                logger.error(f"CoinGecko API error for {crypto_id}: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Failed to fetch crypto price for {crypto_id}: {e}")
            
            return None
    
    async def get_etf_price_async(self, symbol: str) -> Optional[float]:
        """
        Fetch ETF price asynchronously.
        
        Note: yfinance is not async, so we use asyncio.to_thread
        for non-blocking execution.
        
        Args:
            symbol: ETF symbol (e.g., 'SPY')
            
        Returns:
            Current price or None if failed
        """
        async with self._etf_semaphore:
            try:
                logger.debug(f"Fetching ETF price for {symbol}")
                
                # Run yfinance in thread pool to avoid blocking
                ticker = await asyncio.to_thread(yf.Ticker, symbol)
                hist = await asyncio.to_thread(
                    ticker.history, 
                    period="1d", 
                    interval="1d"
                )
                
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    
                    # Log to database
                    await self._log_price_async(
                        symbol=symbol, 
                        price=price, 
                        source='yfinance'
                    )
                    logger.debug(f"ETF price {symbol}: ${price:,.2f}")
                    return price
                
            except Exception as e:
                logger.error(f"Failed to fetch ETF price for {symbol}: {e}")
                
                # Try Alpha Vantage as fallback
                if self.alpha_vantage_api_key:
                    return await self._get_alpha_vantage_price(symbol)
            
            return None
    
    async def _get_alpha_vantage_price(self, symbol: str) -> Optional[float]:
        """Fetch price from Alpha Vantage API as fallback."""
        await self._ensure_client()
        
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_api_key
        }
        
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            quote = data.get('Global Quote', {})
            price_str = quote.get('05. price')
            
            if price_str:
                price = float(price_str)
                await self._log_price_async(
                    symbol=symbol, 
                    price=price, 
                    source='alpha_vantage'
                )
                logger.debug(f"Alpha Vantage price {symbol}: ${price:,.2f}")
                return price
                
        except Exception as e:
            logger.error(f"Alpha Vantage API error for {symbol}: {e}")
        
        return None
    
    async def get_multiple_crypto_prices_async(
        self, 
        crypto_ids: List[str], 
        vs_currency: str = 'usd'
    ) -> Dict[str, Optional[float]]:
        """
        Fetch multiple crypto prices concurrently.
        
        Args:
            crypto_ids: List of CoinGecko crypto IDs
            vs_currency: Target currency
            
        Returns:
            Dictionary mapping crypto_id to price
        """
        # Create concurrent tasks
        tasks = [
            self.get_crypto_price_async(crypto_id, vs_currency)
            for crypto_id in crypto_ids
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        prices = {}
        for crypto_id, result in zip(crypto_ids, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {crypto_id}: {result}")
                prices[crypto_id] = None
            else:
                prices[crypto_id] = result
        
        return prices
    
    async def get_multiple_etf_prices_async(
        self, 
        symbols: List[str]
    ) -> Dict[str, Optional[float]]:
        """
        Fetch multiple ETF prices concurrently.
        
        Args:
            symbols: List of ETF symbols
            
        Returns:
            Dictionary mapping symbol to price
        """
        # Create concurrent tasks
        tasks = [
            self.get_etf_price_async(symbol)
            for symbol in symbols
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        prices = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {symbol}: {result}")
                prices[symbol] = None
            else:
                prices[symbol] = result
        
        return prices
    
    async def _log_price_async(
        self, 
        symbol: str, 
        price: float, 
        source: str
    ):
        """Log price to database asynchronously."""
        try:
            # Run database operation in thread pool
            await asyncio.to_thread(
                log_price_to_db,
                symbol=symbol,
                price=price,
                source=source
            )
        except Exception as e:
            logger.error(f"Failed to log price to database: {e}")
    
    async def _cache_data_async(
        self, 
        cache_file: Path, 
        data: Any
    ):
        """Cache data to file asynchronously."""
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))
                
            logger.debug(f"Cached data to {cache_file}")
            
        except Exception as e:
            logger.error(f"Failed to cache data to {cache_file}: {e}")
    
    async def health_check_async(self) -> Dict[str, str]:
        """
        Perform async health check of all data sources.
        
        Returns:
            Dictionary with status of each data source
        """
        await self._ensure_client()
        
        health_status = {}
        
        # Test CoinGecko
        try:
            url = "https://api.coingecko.com/api/v3/ping"
            response = await self._client.get(url, timeout=10.0)
            if response.status_code == 200:
                health_status['coingecko'] = '✅ Working'
            else:
                health_status['coingecko'] = f'❌ Status {response.status_code}'
        except Exception as e:
            health_status['coingecko'] = f'❌ Error: {str(e)[:50]}'
        
        # Test Alpha Vantage (if API key available)
        if self.alpha_vantage_api_key:
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': 'SPY',
                    'apikey': self.alpha_vantage_api_key
                }
                response = await self._client.get(url, params=params, timeout=10.0)
                if response.status_code == 200:
                    health_status['alpha_vantage'] = '✅ Working'
                else:
                    health_status['alpha_vantage'] = f'❌ Status {response.status_code}'
            except Exception as e:
                health_status['alpha_vantage'] = f'❌ Error: {str(e)[:50]}'
        else:
            health_status['alpha_vantage'] = '⚠️  No API key'
        
        # Test yfinance (run in thread)
        try:
            ticker = await asyncio.to_thread(yf.Ticker, 'SPY')
            hist = await asyncio.to_thread(ticker.history, period="1d")
            if not hist.empty:
                health_status['yfinance'] = '✅ Working'
            else:
                health_status['yfinance'] = '❌ No data returned'
        except Exception as e:
            health_status['yfinance'] = f'❌ Error: {str(e)[:50]}'
        
        return health_status


class AsyncPriceFetcherWrapper:
    """
    Wrapper to provide sync interface for async price fetcher.
    
    This allows existing code to use async fetcher without changes.
    """
    
    def __init__(self, async_fetcher: AsyncPriceFetcher):
        self.async_fetcher = async_fetcher
        self._loop = None
    
    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to run in thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(coro)
    
    def get_crypto_price(self, crypto_id: str, vs_currency: str = 'usd') -> Optional[float]:
        """Sync wrapper for get_crypto_price_async."""
        return self._run_async(
            self.async_fetcher.get_crypto_price_async(crypto_id, vs_currency)
        )
    
    def get_etf_price(self, symbol: str) -> Optional[float]:
        """Sync wrapper for get_etf_price_async."""
        return self._run_async(
            self.async_fetcher.get_etf_price_async(symbol)
        )
    
    def get_multiple_crypto_prices(
        self, 
        crypto_ids: List[str], 
        vs_currency: str = 'usd'
    ) -> Dict[str, Optional[float]]:
        """Sync wrapper for get_multiple_crypto_prices_async."""
        return self._run_async(
            self.async_fetcher.get_multiple_crypto_prices_async(crypto_ids, vs_currency)
        )
    
    def get_multiple_etf_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Sync wrapper for get_multiple_etf_prices_async."""
        return self._run_async(
            self.async_fetcher.get_multiple_etf_prices_async(symbols)
        )
    
    def health_check(self) -> Dict[str, str]:
        """Sync wrapper for health_check_async."""
        return self._run_async(self.async_fetcher.health_check_async())


# Global instances for convenience
_async_fetcher: Optional[AsyncPriceFetcher] = None
_sync_wrapper: Optional[AsyncPriceFetcherWrapper] = None


def get_async_price_fetcher(**kwargs) -> AsyncPriceFetcher:
    """Get or create global async price fetcher instance."""
    global _async_fetcher
    
    if _async_fetcher is None:
        _async_fetcher = AsyncPriceFetcher(**kwargs)
    
    return _async_fetcher


def get_sync_price_fetcher(**kwargs) -> AsyncPriceFetcherWrapper:
    """Get sync wrapper for async price fetcher."""
    global _sync_wrapper
    
    if _sync_wrapper is None:
        async_fetcher = get_async_price_fetcher(**kwargs)
        _sync_wrapper = AsyncPriceFetcherWrapper(async_fetcher)
    
    return _sync_wrapper


# Convenience functions for FastAPI integration
async def fetch_crypto_prices_background(crypto_ids: List[str]) -> Dict[str, Optional[float]]:
    """
    Background task function for fetching crypto prices.
    
    This can be used with FastAPI BackgroundTasks:
    
    @app.post("/fetch-crypto")
    async def fetch_crypto(background_tasks: BackgroundTasks):
        background_tasks.add_task(
            fetch_crypto_prices_background, 
            ['bitcoin', 'ethereum']
        )
        return {"message": "Fetching prices in background"}
    """
    async with AsyncPriceFetcher() as fetcher:
        return await fetcher.get_multiple_crypto_prices_async(crypto_ids)


async def fetch_etf_prices_background(symbols: List[str]) -> Dict[str, Optional[float]]:
    """Background task function for fetching ETF prices."""
    async with AsyncPriceFetcher() as fetcher:
        return await fetcher.get_multiple_etf_prices_async(symbols)