#!/usr/bin/env python3
"""
Production-Grade Market Data Fetcher

This module provides enterprise-ready market data fetching with:
- API key management and authentication
- Rate limiting and exponential backoff
- Multiple data source support with fallbacks
- Local caching for development and reliability
- Comprehensive error handling and logging
- Data validation and sanity checking

Supported Data Sources:
- CoinGecko API for cryptocurrency prices
- Yahoo Finance (via yfinance) for ETF/stock prices
- Alpha Vantage API as backup for traditional assets
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path

import requests
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry
from backoff import on_exception, expo
import pytz

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSourceError(Exception):
    """Base exception for data source errors"""
    pass

class RateLimitError(DataSourceError):
    """Raised when API rate limit is exceeded"""
    pass

class AuthenticationError(DataSourceError):
    """Raised when API authentication fails"""
    pass

class InsufficientDataError(DataSourceError):
    """Raised when insufficient data is returned"""
    pass

class DataValidationError(DataSourceError):
    """Raised when data fails validation checks"""
    pass

class PriceFetcher:
    """
    Production-grade market data fetcher with comprehensive error handling.
    
    Features:
    - Multiple API source support with automatic fallbacks
    - Rate limiting to respect API terms of service
    - Local caching for development and reliability
    - Data validation and sanity checking
    - Comprehensive logging and monitoring
    """
    
    def __init__(self):
        """Initialize the price fetcher with configuration from environment variables."""
        self.load_configuration()
        self.setup_cache_directory()
        self.setup_logging()
        
        # API endpoints and configurations
        self.coingecko_base_url = os.getenv('COINGECKO_BASE_URL', 'https://api.coingecko.com/api/v3')
        self.alpha_vantage_base_url = 'https://www.alphavantage.co/query'
        
        # Rate limiting configurations
        self.crypto_rate_limit = int(os.getenv('CRYPTO_API_RATE_LIMIT', '10'))
        self.etf_rate_limit = int(os.getenv('ETF_API_RATE_LIMIT', '5'))
        
        # Request configurations
        self.timeout = int(os.getenv('API_TIMEOUT_SECONDS', '30'))
        self.retry_attempts = int(os.getenv('API_RETRY_ATTEMPTS', '3'))
        self.backoff_factor = float(os.getenv('API_BACKOFF_FACTOR', '2.0'))
        
        logger.info(f"PriceFetcher initialized with crypto rate limit: {self.crypto_rate_limit}/min, ETF rate limit: {self.etf_rate_limit}/min")
    
    def load_configuration(self):
        """Load and validate configuration from environment variables."""
        # API Keys
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY')
        
        # Cache configuration
        self.cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        self.cache_expiry_minutes = int(os.getenv('CACHE_EXPIRY_MINUTES', '60'))
        self.cache_directory = Path(os.getenv('CACHE_DIRECTORY', 'data/cache'))
        
        # Security settings
        self.mask_api_keys = os.getenv('MASK_API_KEYS_IN_LOGS', 'true').lower() == 'true'
        self.enable_request_logging = os.getenv('ENABLE_REQUEST_LOGGING', 'false').lower() == 'true'
    
    def setup_cache_directory(self):
        """Create cache directories if they don't exist."""
        if self.cache_enabled:
            self.cache_directory.mkdir(parents=True, exist_ok=True)
            (self.cache_directory / 'crypto').mkdir(exist_ok=True)
            (self.cache_directory / 'etf').mkdir(exist_ok=True)
    
    def setup_logging(self):
        """Configure logging for production use."""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logging.getLogger().setLevel(getattr(logging, log_level))
    
    def mask_api_key(self, api_key: str) -> str:
        """Mask API key for logging (show only first and last 4 characters)."""
        if not api_key or not self.mask_api_keys:
            return api_key
        if len(api_key) <= 8:
            return '*' * len(api_key)
        return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"
    
    def get_cache_path(self, asset_type: str, symbol: str, days: int) -> Path:
        """Generate cache file path for given parameters."""
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{symbol}_{days}d_{today}.json"
        return self.cache_directory / asset_type / filename
    
    def load_from_cache(self, asset_type: str, symbol: str, days: int) -> Optional[List[float]]:
        """Load price data from cache if available and not expired."""
        if not self.cache_enabled:
            return None
            
        cache_path = self.get_cache_path(asset_type, symbol, days)
        
        if not cache_path.exists():
            return None
        
        try:
            # Check if cache is expired
            file_age_minutes = (time.time() - cache_path.stat().st_mtime) / 60
            if file_age_minutes > self.cache_expiry_minutes:
                logger.info(f"Cache expired for {symbol} ({file_age_minutes:.1f} minutes old)")
                cache_path.unlink()  # Remove expired cache
                return None
            
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            prices = data.get('prices', [])
            if prices:
                logger.info(f"Loaded {len(prices)} prices for {symbol} from cache")
                return prices
                
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Failed to load cache for {symbol}: {e}")
            if cache_path.exists():
                cache_path.unlink()  # Remove corrupted cache
        
        return None
    
    def save_to_cache(self, asset_type: str, symbol: str, days: int, prices: List[float], metadata: Dict = None):
        """Save price data to cache with metadata."""
        if not self.cache_enabled or not prices:
            return
        
        cache_path = self.get_cache_path(asset_type, symbol, days)
        
        try:
            cache_data = {
                'symbol': symbol,
                'asset_type': asset_type,
                'days': days,
                'prices': prices,
                'fetched_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Cached {len(prices)} prices for {symbol}")
            
        except OSError as e:
            logger.warning(f"Failed to save cache for {symbol}: {e}")
    
    def validate_prices(self, prices: List[float], symbol: str, asset_type: str) -> List[float]:
        """Validate price data for sanity and completeness."""
        if not prices:
            raise InsufficientDataError(f"No price data returned for {symbol}")
        
        # Remove any None or invalid values
        valid_prices = [p for p in prices if p is not None and p > 0]
        
        if len(valid_prices) == 0:
            raise DataValidationError(f"All price data invalid for {symbol}")
        
        if len(valid_prices) < len(prices) * 0.8:  # Allow up to 20% data loss
            logger.warning(f"Significant data loss for {symbol}: {len(valid_prices)}/{len(prices)} valid prices")
        
        # Sanity check: detect obviously wrong prices
        if asset_type == 'crypto':
            # Crypto prices should be reasonable (e.g., $0.01 to $1M)
            if any(p < 0.01 or p > 1000000 for p in valid_prices):
                logger.warning(f"Suspicious crypto prices detected for {symbol}: range ${min(valid_prices):.2f} - ${max(valid_prices):.2f}")
        
        elif asset_type == 'etf':
            # ETF prices should be reasonable (e.g., $1 to $10,000)
            if any(p < 1 or p > 10000 for p in valid_prices):
                logger.warning(f"Suspicious ETF prices detected for {symbol}: range ${min(valid_prices):.2f} - ${max(valid_prices):.2f}")
        
        # Check for extreme volatility (>50% daily moves)
        for i in range(1, len(valid_prices)):
            daily_change = abs(valid_prices[i] - valid_prices[i-1]) / valid_prices[i-1]
            if daily_change > 0.5:  # 50% daily move
                logger.warning(f"Extreme daily volatility detected for {symbol}: {daily_change:.2%} on day {i}")
        
        return valid_prices
    
    @sleep_and_retry
    @limits(calls=10, period=60)  # Default rate limit, will be overridden by specific methods
    def _rate_limited_request(self, url: str, params: Dict = None, headers: Dict = None) -> requests.Response:
        """Make rate-limited HTTP request with proper error handling."""
        try:
            if self.enable_request_logging:
                logger.debug(f"Making request to {url} with params: {params}")
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout:
            raise DataSourceError(f"Request timeout to {url}")
        except requests.exceptions.ConnectionError:
            raise DataSourceError(f"Connection error to {url}")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded for {url}")
            elif response.status_code == 401:
                raise AuthenticationError(f"Authentication failed for {url}")
            else:
                raise DataSourceError(f"HTTP error {response.status_code} for {url}: {e}")
    
    @on_exception(expo, (DataSourceError, requests.exceptions.RequestException), max_tries=3)
    def get_crypto_prices_coingecko(self, coin_id: str, days: int = 7) -> List[float]:
        """Fetch cryptocurrency prices from CoinGecko API."""
        url = f"{self.coingecko_base_url}/coins/{coin_id}/market_chart"
        
        params = {
            'vs_currency': 'usd',
            'days': days
        }
        
        headers = {}
        if self.coingecko_api_key:
            headers['x-cg-demo-api-key'] = self.coingecko_api_key
            logger.debug(f"Using CoinGecko API key: {self.mask_api_key(self.coingecko_api_key)}")
        else:
            logger.info("Using CoinGecko free tier (no API key)")
        
        try:
            response = self._rate_limited_request(url, params=params, headers=headers)
            data = response.json()
            
            if 'prices' not in data:
                raise DataValidationError(f"Invalid response format from CoinGecko for {coin_id}")
            
            # Extract prices from [timestamp, price] pairs
            prices = [entry[1] for entry in data['prices'] if entry[1] is not None]
            
            logger.info(f"Fetched {len(prices)} crypto prices for {coin_id} from CoinGecko")
            return self.validate_prices(prices, coin_id, 'crypto')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API error for {coin_id}: {e}")
            raise DataSourceError(f"Failed to fetch crypto data for {coin_id}: {e}")
    
    @on_exception(expo, Exception, max_tries=3)
    def get_etf_prices_yfinance(self, symbol: str, days: int = 7) -> List[float]:
        """Fetch ETF/stock prices from Yahoo Finance via yfinance."""
        try:
            # Calculate the period string for yfinance
            if days <= 7:
                period = "7d"
            elif days <= 30:
                period = "1mo"
            elif days <= 90:
                period = "3mo"
            else:
                period = "1y"
            
            logger.debug(f"Fetching {symbol} data for period: {period}")
            
            # Download data from Yahoo Finance
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval="1d", auto_adjust=True, prepost=False)
            
            if df.empty:
                raise InsufficientDataError(f"No data returned from Yahoo Finance for {symbol}")
            
            # Use closing prices
            prices = df['Close'].dropna().tolist()
            
            # Trim to requested number of days
            if len(prices) > days:
                prices = prices[-days:]
            
            logger.info(f"Fetched {len(prices)} ETF prices for {symbol} from Yahoo Finance")
            return self.validate_prices(prices, symbol, 'etf')
            
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            raise DataSourceError(f"Failed to fetch ETF data for {symbol}: {e}")
    
    def get_etf_prices_alpha_vantage(self, symbol: str, days: int = 7) -> List[float]:
        """Fetch ETF/stock prices from Alpha Vantage API (backup source)."""
        if not self.alpha_vantage_api_key:
            raise AuthenticationError("Alpha Vantage API key not configured")
        
        url = self.alpha_vantage_base_url
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.alpha_vantage_api_key,
            'outputsize': 'compact'
        }
        
        try:
            response = self._rate_limited_request(url, params=params)
            data = response.json()
            
            if 'Error Message' in data:
                raise DataValidationError(f"Alpha Vantage error: {data['Error Message']}")
            
            if 'Note' in data:
                raise RateLimitError(f"Alpha Vantage rate limit: {data['Note']}")
            
            time_series = data.get('Time Series (Daily)', {})
            if not time_series:
                raise InsufficientDataError(f"No time series data for {symbol} from Alpha Vantage")
            
            # Extract closing prices for the requested number of days
            sorted_dates = sorted(time_series.keys(), reverse=True)
            prices = []
            
            for date in sorted_dates[:days]:
                close_price = float(time_series[date]['4. close'])
                prices.append(close_price)
            
            # Reverse to get chronological order (oldest to newest)
            prices.reverse()
            
            logger.info(f"Fetched {len(prices)} ETF prices for {symbol} from Alpha Vantage")
            return self.validate_prices(prices, symbol, 'etf')
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Alpha Vantage data parsing error for {symbol}: {e}")
            raise DataValidationError(f"Failed to parse Alpha Vantage data for {symbol}: {e}")
    
    def get_prices(self, symbol: str, asset_type: str, days: int = 7) -> List[float]:
        """
        Main entry point to fetch prices with fallback mechanisms.
        
        Args:
            symbol: Asset symbol (e.g., 'SPY', 'bitcoin')
            asset_type: 'crypto' or 'etf'
            days: Number of days of historical data
            
        Returns:
            List of daily closing prices (oldest to newest)
            
        Raises:
            DataSourceError: When all data sources fail
        """
        # Check cache first
        cached_prices = self.load_from_cache(asset_type, symbol, days)
        if cached_prices:
            return cached_prices
        
        prices = None
        errors = []
        
        try:
            if asset_type.lower() == 'crypto':
                prices = self.get_crypto_prices_coingecko(symbol, days)
                self.save_to_cache(asset_type, symbol, days, prices, {'source': 'coingecko'})
                
            elif asset_type.lower() == 'etf':
                # Primary: Yahoo Finance (free, reliable)
                try:
                    prices = self.get_etf_prices_yfinance(symbol, days)
                    self.save_to_cache(asset_type, symbol, days, prices, {'source': 'yfinance'})
                except Exception as e:
                    errors.append(f"Yahoo Finance failed: {e}")
                    logger.warning(f"Yahoo Finance failed for {symbol}, trying Alpha Vantage backup")
                    
                    # Fallback: Alpha Vantage
                    if self.alpha_vantage_api_key:
                        prices = self.get_etf_prices_alpha_vantage(symbol, days)
                        self.save_to_cache(asset_type, symbol, days, prices, {'source': 'alpha_vantage'})
                    else:
                        raise DataSourceError("No backup ETF data source available (Alpha Vantage key missing)")
            
            else:
                raise ValueError(f"Unsupported asset_type: {asset_type}. Use 'crypto' or 'etf'")
            
            if prices:
                logger.info(f"Successfully fetched {len(prices)} prices for {symbol} ({asset_type})")
                return prices
            
        except Exception as e:
            errors.append(str(e))
            logger.error(f"All data sources failed for {symbol} ({asset_type}): {'; '.join(errors)}")
        
        # If we get here, all sources failed
        raise DataSourceError(f"Failed to fetch data for {symbol} from all sources: {'; '.join(errors)}")
    
    def get_multiple_prices(self, symbols: List[str], asset_type: str, days: int = 7) -> Dict[str, List[float]]:
        """
        Fetch prices for multiple symbols efficiently.
        
        Args:
            symbols: List of asset symbols
            asset_type: 'crypto' or 'etf'
            days: Number of days of historical data
            
        Returns:
            Dictionary mapping symbols to price lists
        """
        results = {}
        errors = {}
        
        for symbol in symbols:
            try:
                prices = self.get_prices(symbol, asset_type, days)
                results[symbol] = prices
            except Exception as e:
                errors[symbol] = str(e)
                logger.error(f"Failed to fetch prices for {symbol}: {e}")
        
        if errors:
            logger.warning(f"Failed to fetch data for {len(errors)} symbols: {list(errors.keys())}")
        
        logger.info(f"Successfully fetched prices for {len(results)}/{len(symbols)} symbols")
        return results
    
    def health_check(self) -> Dict[str, bool]:
        """
        Check the health of all configured data sources.
        
        Returns:
            Dictionary with data source names and their status
        """
        health_status = {}
        
        # Test CoinGecko
        try:
            test_prices = self.get_crypto_prices_coingecko('bitcoin', 1)
            health_status['coingecko'] = len(test_prices) > 0
        except Exception as e:
            health_status['coingecko'] = False
            logger.warning(f"CoinGecko health check failed: {e}")
        
        # Test Yahoo Finance
        try:
            test_prices = self.get_etf_prices_yfinance('SPY', 1)
            health_status['yfinance'] = len(test_prices) > 0
        except Exception as e:
            health_status['yfinance'] = False
            logger.warning(f"Yahoo Finance health check failed: {e}")
        
        # Test Alpha Vantage (if configured)
        if self.alpha_vantage_api_key:
            try:
                test_prices = self.get_etf_prices_alpha_vantage('SPY', 1)
                health_status['alpha_vantage'] = len(test_prices) > 0
            except Exception as e:
                health_status['alpha_vantage'] = False
                logger.warning(f"Alpha Vantage health check failed: {e}")
        else:
            health_status['alpha_vantage'] = None  # Not configured
        
        working_sources = sum(1 for status in health_status.values() if status is True)
        logger.info(f"Data source health check: {working_sources}/{len([s for s in health_status.values() if s is not None])} sources working")
        
        return health_status


# Convenience functions for backward compatibility and ease of use
def get_prices(symbol: str, asset_type: str, days: int = 7) -> List[float]:
    """Convenience function to get prices using the global PriceFetcher instance."""
    fetcher = PriceFetcher()
    return fetcher.get_prices(symbol, asset_type, days)

def get_crypto_prices(coin_id: str, days: int = 7) -> List[float]:
    """Convenience function to get cryptocurrency prices."""
    return get_prices(coin_id, 'crypto', days)

def get_etf_prices(symbol: str, days: int = 7) -> List[float]:
    """Convenience function to get ETF/stock prices."""
    return get_prices(symbol, 'etf', days)


if __name__ == "__main__":
    """Self-test module for price fetcher."""
    import sys
    
    print("=" * 60)
    print("PRICE FETCHER SELF-TEST")
    print("=" * 60)
    
    # Initialize fetcher
    fetcher = PriceFetcher()
    
    # Health check
    print("\\nPerforming health check...")
    health = fetcher.health_check()
    for source, status in health.items():
        status_str = "✅ Working" if status else "❌ Failed" if status is False else "⚠️ Not configured"
        print(f"  {source}: {status_str}")
    
    # Test crypto prices
    print("\\nTesting crypto price fetching...")
    try:
        btc_prices = fetcher.get_prices('bitcoin', 'crypto', 7)
        print(f"BTC prices (7 days): {len(btc_prices)} data points")
        print(f"  Range: ${min(btc_prices):,.2f} - ${max(btc_prices):,.2f}")
        print(f"  Latest: ${btc_prices[-1]:,.2f}")
    except Exception as e:
        print(f"  ❌ Crypto test failed: {e}")
    
    # Test ETF prices
    print("\\nTesting ETF price fetching...")
    try:
        spy_prices = fetcher.get_prices('SPY', 'etf', 7)
        print(f"SPY prices (7 days): {len(spy_prices)} data points")
        print(f"  Range: ${min(spy_prices):.2f} - ${max(spy_prices):.2f}")
        print(f"  Latest: ${spy_prices[-1]:.2f}")
    except Exception as e:
        print(f"  ❌ ETF test failed: {e}")
    
    # Test multiple symbols
    print("\\nTesting multiple symbol fetching...")
    try:
        crypto_symbols = ['bitcoin', 'ethereum', 'solana']
        crypto_data = fetcher.get_multiple_prices(crypto_symbols, 'crypto', 5)
        print(f"Fetched data for {len(crypto_data)}/{len(crypto_symbols)} crypto symbols")
        
        etf_symbols = ['SPY', 'QQQ', 'IWM']
        etf_data = fetcher.get_multiple_prices(etf_symbols, 'etf', 5)
        print(f"Fetched data for {len(etf_data)}/{len(etf_symbols)} ETF symbols")
    except Exception as e:
        print(f"  ❌ Multiple symbol test failed: {e}")
    
    print("\\n" + "=" * 60)
    print("SELF-TEST COMPLETE")
    print("=" * 60)