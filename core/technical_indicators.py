"""
Technical Indicators Module

Provides comprehensive technical analysis calculations for trading recommendations.
Includes moving averages, momentum indicators, volatility measures, and trend analysis.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Technical analysis indicators calculation"""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> List[float]:
        """Simple Moving Average"""
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        sma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                sma_values.append(np.nan)
            else:
                sma_values.append(np.mean(prices[i - period + 1:i + 1]))
        
        return sma_values
    
    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        """Exponential Moving Average"""
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        alpha = 2 / (period + 1)
        ema_values = [prices[0]]  # Start with first price
        
        for i in range(1, len(prices)):
            ema_val = alpha * prices[i] + (1 - alpha) * ema_values[-1]
            ema_values.append(ema_val)
        
        return ema_values
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return [np.nan] * len(prices)
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(d, 0) for d in deltas]
        losses = [abs(min(d, 0)) for d in deltas]
        
        rsi_values = [np.nan]  # First value is NaN
        
        # Initial average gain/loss
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))
        
        # Calculate subsequent RSI values
        for i in range(period + 1, len(prices)):
            gain = gains[i-1]
            loss = losses[i-1]
            
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
        
        return rsi_values
    
    @staticmethod
    def macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[float]]:
        """MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow_period:
            nan_list = [np.nan] * len(prices)
            return {'macd': nan_list, 'signal': nan_list, 'histogram': nan_list}
        
        ema_fast = TechnicalIndicators.ema(prices, fast_period)
        ema_slow = TechnicalIndicators.ema(prices, slow_period)
        
        macd_line = [fast - slow if not (np.isnan(fast) or np.isnan(slow)) else np.nan 
                     for fast, slow in zip(ema_fast, ema_slow)]
        
        # Remove NaN values for signal calculation
        valid_macd = [x for x in macd_line if not np.isnan(x)]
        if len(valid_macd) >= signal_period:
            signal_line = TechnicalIndicators.ema(valid_macd, signal_period)
            # Pad with NaN to match original length
            nan_count = len(macd_line) - len(signal_line)
            signal_line = [np.nan] * nan_count + signal_line
        else:
            signal_line = [np.nan] * len(macd_line)
        
        histogram = [macd - signal if not (np.isnan(macd) or np.isnan(signal)) else np.nan 
                    for macd, signal in zip(macd_line, signal_line)]
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, List[float]]:
        """Bollinger Bands"""
        if len(prices) < period:
            nan_list = [np.nan] * len(prices)
            return {'upper': nan_list, 'middle': nan_list, 'lower': nan_list}
        
        sma_values = TechnicalIndicators.sma(prices, period)
        
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1:
                upper_band.append(np.nan)
                lower_band.append(np.nan)
            else:
                price_slice = prices[i - period + 1:i + 1]
                std = np.std(price_slice, ddof=1)
                upper_band.append(sma_values[i] + (std_dev * std))
                lower_band.append(sma_values[i] - (std_dev * std))
        
        return {
            'upper': upper_band,
            'middle': sma_values,
            'lower': lower_band
        }
    
    @staticmethod
    def momentum(prices: List[float], period: int = 10) -> List[float]:
        """Price Momentum"""
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        momentum_values = []
        for i in range(len(prices)):
            if i < period:
                momentum_values.append(np.nan)
            else:
                momentum_values.append(prices[i] - prices[i - period])
        
        return momentum_values
    
    @staticmethod
    def rate_of_change(prices: List[float], period: int = 10) -> List[float]:
        """Rate of Change (ROC)"""
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        roc_values = []
        for i in range(len(prices)):
            if i < period or prices[i - period] == 0:
                roc_values.append(np.nan)
            else:
                roc = ((prices[i] - prices[i - period]) / prices[i - period]) * 100
                roc_values.append(roc)
        
        return roc_values
    
    @staticmethod
    def stochastic(highs: List[float], lows: List[float], closes: List[float], 
                   k_period: int = 14, d_period: int = 3) -> Dict[str, List[float]]:
        """Stochastic Oscillator"""
        if len(closes) < k_period:
            nan_list = [np.nan] * len(closes)
            return {'%K': nan_list, '%D': nan_list}
        
        k_values = []
        for i in range(len(closes)):
            if i < k_period - 1:
                k_values.append(np.nan)
            else:
                highest_high = max(highs[i - k_period + 1:i + 1])
                lowest_low = min(lows[i - k_period + 1:i + 1])
                
                if highest_high == lowest_low:
                    k_values.append(50)  # Avoid division by zero
                else:
                    k = ((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100
                    k_values.append(k)
        
        # %D is a moving average of %K
        valid_k = [x for x in k_values if not np.isnan(x)]
        if len(valid_k) >= d_period:
            d_values = TechnicalIndicators.sma(valid_k, d_period)
            # Pad with NaN to match original length
            nan_count = len(k_values) - len(d_values)
            d_values = [np.nan] * nan_count + d_values
        else:
            d_values = [np.nan] * len(k_values)
        
        return {'%K': k_values, '%D': d_values}
    
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
        """Average True Range"""
        if len(closes) < 2:
            return [np.nan] * len(closes)
        
        true_ranges = [np.nan]  # First value is NaN
        
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            
            true_range = max(high_low, high_close, low_close)
            true_ranges.append(true_range)
        
        # Calculate ATR as moving average of true ranges
        atr_values = []
        for i in range(len(true_ranges)):
            if i < period:
                atr_values.append(np.nan)
            else:
                valid_tr = [tr for tr in true_ranges[i - period + 1:i + 1] if not np.isnan(tr)]
                if valid_tr:
                    atr_values.append(np.mean(valid_tr))
                else:
                    atr_values.append(np.nan)
        
        return atr_values
    
    @staticmethod
    def volatility(prices: List[float], period: int = 20) -> List[float]:
        """Price Volatility (standard deviation of returns)"""
        if len(prices) < period + 1:
            return [np.nan] * len(prices)
        
        returns = [(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
        volatility_values = [np.nan]  # First value is NaN
        
        for i in range(len(returns)):
            if i < period - 1:
                volatility_values.append(np.nan)
            else:
                vol = np.std(returns[i - period + 1:i + 1], ddof=1) * np.sqrt(252)  # Annualized
                volatility_values.append(vol)
        
        return volatility_values


class MarketAnalysis:
    """Advanced market analysis using technical indicators"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def analyze_trend(self, prices: List[float], short_ma: int = 20, long_ma: int = 50) -> Dict[str, Any]:
        """Comprehensive trend analysis"""
        if len(prices) < long_ma:
            return {"trend": "INSUFFICIENT_DATA", "strength": 0, "signals": []}
        
        sma_short = self.indicators.sma(prices, short_ma)
        sma_long = self.indicators.sma(prices, long_ma)
        
        current_price = prices[-1]
        current_short_ma = sma_short[-1]
        current_long_ma = sma_long[-1]
        
        signals = []
        trend = "NEUTRAL"
        strength = 0
        
        # Golden Cross / Death Cross
        if not (np.isnan(current_short_ma) or np.isnan(current_long_ma)):
            if current_short_ma > current_long_ma:
                if len(sma_short) > 1 and sma_short[-2] <= sma_long[-2]:
                    signals.append("GOLDEN_CROSS")
                trend = "BULLISH"
                strength = min(((current_short_ma / current_long_ma) - 1) * 100, 10)
            else:
                if len(sma_short) > 1 and sma_short[-2] >= sma_long[-2]:
                    signals.append("DEATH_CROSS")
                trend = "BEARISH"
                strength = min(((current_long_ma / current_short_ma) - 1) * 100, 10)
        
        # Price vs MA relationship
        if not np.isnan(current_short_ma):
            if current_price > current_short_ma * 1.02:
                signals.append("PRICE_ABOVE_MA")
            elif current_price < current_short_ma * 0.98:
                signals.append("PRICE_BELOW_MA")
        
        return {
            "trend": trend,
            "strength": abs(strength),
            "signals": signals,
            "short_ma": current_short_ma,
            "long_ma": current_long_ma,
            "price_vs_short_ma": ((current_price / current_short_ma) - 1) * 100 if not np.isnan(current_short_ma) else 0
        }
    
    def analyze_momentum(self, prices: List[float]) -> Dict[str, Any]:
        """Momentum analysis using multiple indicators"""
        if len(prices) < 30:
            return {"momentum": "INSUFFICIENT_DATA", "rsi": np.nan, "signals": []}
        
        rsi_values = self.indicators.rsi(prices, 14)
        macd_data = self.indicators.macd(prices)
        roc_values = self.indicators.rate_of_change(prices, 10)
        
        current_rsi = rsi_values[-1] if not np.isnan(rsi_values[-1]) else 50
        current_macd = macd_data['macd'][-1] if not np.isnan(macd_data['macd'][-1]) else 0
        current_roc = roc_values[-1] if not np.isnan(roc_values[-1]) else 0
        
        signals = []
        momentum = "NEUTRAL"
        
        # RSI signals
        if current_rsi > 70:
            signals.append("RSI_OVERBOUGHT")
            momentum = "BEARISH"
        elif current_rsi < 30:
            signals.append("RSI_OVERSOLD")
            momentum = "BULLISH"
        
        # MACD signals
        if current_macd > 0:
            signals.append("MACD_POSITIVE")
            if momentum != "BEARISH":
                momentum = "BULLISH"
        elif current_macd < 0:
            signals.append("MACD_NEGATIVE")
            if momentum != "BULLISH":
                momentum = "BEARISH"
        
        # ROC signals
        if current_roc > 5:
            signals.append("STRONG_POSITIVE_ROC")
        elif current_roc < -5:
            signals.append("STRONG_NEGATIVE_ROC")
        
        return {
            "momentum": momentum,
            "rsi": current_rsi,
            "macd": current_macd,
            "roc": current_roc,
            "signals": signals
        }
    
    def analyze_volatility(self, prices: List[float]) -> Dict[str, Any]:
        """Volatility analysis"""
        if len(prices) < 21:
            return {"volatility": "INSUFFICIENT_DATA", "regime": "UNKNOWN"}
        
        volatility_values = self.indicators.volatility(prices, 20)
        current_vol = volatility_values[-1] if not np.isnan(volatility_values[-1]) else 0.15
        
        # Volatility regimes
        if current_vol > 0.30:
            regime = "HIGH"
        elif current_vol > 0.20:
            regime = "MEDIUM"
        else:
            regime = "LOW"
        
        # Bollinger Bands for volatility context
        bb_data = self.indicators.bollinger_bands(prices, 20, 2)
        current_price = prices[-1]
        upper_band = bb_data['upper'][-1]
        lower_band = bb_data['lower'][-1]
        
        bb_position = "MIDDLE"
        if not (np.isnan(upper_band) or np.isnan(lower_band)):
            if current_price > upper_band:
                bb_position = "UPPER"
            elif current_price < lower_band:
                bb_position = "LOWER"
        
        return {
            "volatility": current_vol,
            "regime": regime,
            "bollinger_position": bb_position,
            "upper_band": upper_band,
            "lower_band": lower_band
        }
    
    def comprehensive_analysis(self, prices: List[float], symbol: str = "") -> Dict[str, Any]:
        """Complete technical analysis combining all indicators"""
        if len(prices) < 50:
            return {
                "symbol": symbol,
                "status": "INSUFFICIENT_DATA",
                "recommendation": "HOLD",
                "confidence": 0.0,
                "reasoning": "Insufficient price history for technical analysis"
            }
        
        trend_analysis = self.analyze_trend(prices)
        momentum_analysis = self.analyze_momentum(prices)
        volatility_analysis = self.analyze_volatility(prices)
        
        # Combine analyses for recommendation
        signals = trend_analysis['signals'] + momentum_analysis['signals']
        
        # Simple scoring system
        bullish_signals = len([s for s in signals if s in ['GOLDEN_CROSS', 'PRICE_ABOVE_MA', 'RSI_OVERSOLD', 'MACD_POSITIVE', 'STRONG_POSITIVE_ROC']])
        bearish_signals = len([s for s in signals if s in ['DEATH_CROSS', 'PRICE_BELOW_MA', 'RSI_OVERBOUGHT', 'MACD_NEGATIVE', 'STRONG_NEGATIVE_ROC']])
        
        if bullish_signals > bearish_signals + 1:
            recommendation = "BUY"
            confidence = min(0.8, 0.4 + (bullish_signals - bearish_signals) * 0.1)
        elif bearish_signals > bullish_signals + 1:
            recommendation = "SELL"
            confidence = min(0.8, 0.4 + (bearish_signals - bullish_signals) * 0.1)
        else:
            recommendation = "HOLD"
            confidence = 0.5
        
        # Build reasoning
        reasoning_parts = []
        if trend_analysis['trend'] != "NEUTRAL":
            reasoning_parts.append(f"{trend_analysis['trend'].lower()} trend (strength: {trend_analysis['strength']:.1f}%)")
        
        if momentum_analysis['momentum'] != "NEUTRAL":
            reasoning_parts.append(f"{momentum_analysis['momentum'].lower()} momentum (RSI: {momentum_analysis['rsi']:.1f})")
        
        if volatility_analysis['regime'] == "HIGH":
            reasoning_parts.append(f"high volatility environment ({volatility_analysis['volatility']:.1%})")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "mixed signals, neutral stance"
        
        return {
            "symbol": symbol,
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning.capitalize(),
            "trend_analysis": trend_analysis,
            "momentum_analysis": momentum_analysis,
            "volatility_analysis": volatility_analysis,
            "signals": signals,
            "current_price": prices[-1]
        }


if __name__ == "__main__":
    # Test the technical indicators
    import random
    
    # Generate sample price data
    np.random.seed(42)
    base_price = 100
    prices = [base_price]
    
    for _ in range(100):
        change = np.random.normal(0, 0.02)  # 2% daily volatility
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    print("=== TECHNICAL INDICATORS TEST ===")
    
    # Test individual indicators
    indicators = TechnicalIndicators()
    
    sma_20 = indicators.sma(prices, 20)
    rsi_14 = indicators.rsi(prices, 14)
    macd_data = indicators.macd(prices)
    
    print(f"Current Price: ${prices[-1]:.2f}")
    print(f"SMA(20): ${sma_20[-1]:.2f}")
    print(f"RSI(14): {rsi_14[-1]:.1f}")
    print(f"MACD: {macd_data['macd'][-1]:.4f}")
    
    # Test comprehensive analysis
    print("\n=== COMPREHENSIVE ANALYSIS ===")
    analyzer = MarketAnalysis()
    analysis = analyzer.comprehensive_analysis(prices, "TEST")
    
    print(f"Recommendation: {analysis['recommendation']}")
    print(f"Confidence: {analysis['confidence']:.1%}")
    print(f"Reasoning: {analysis['reasoning']}")
    print(f"Signals: {analysis['signals']}")