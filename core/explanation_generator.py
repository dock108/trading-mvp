"""
Explanation Generator Module

Provides detailed explanations for trading recommendations to help users understand
the reasoning behind each suggested trade. Supports multiple explanation formats
and confidence-based messaging.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ExplanationStyle(Enum):
    """Different explanation styles for different contexts"""
    CONCISE = "concise"        # Brief explanations for quick review
    DETAILED = "detailed"      # Comprehensive explanations with full context
    TECHNICAL = "technical"    # Technical analysis focused explanations
    BEGINNER = "beginner"      # Simple explanations for new traders


class RecommendationReason(Enum):
    """Categories of recommendation reasoning"""
    TECHNICAL_SIGNAL = "technical_signal"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    TREND_FOLLOWING = "trend_following"
    RISK_MANAGEMENT = "risk_management"
    PORTFOLIO_REBALANCING = "portfolio_rebalancing"


class ExplanationGenerator:
    """Generate clear, actionable explanations for trading recommendations"""
    
    def __init__(self, style: ExplanationStyle = ExplanationStyle.DETAILED):
        self.style = style
        self.confidence_thresholds = {
            "very_high": 0.8,
            "high": 0.65,
            "medium": 0.5,
            "low": 0.35
        }
    
    def generate_recommendation_explanation(self, recommendation_data: Dict[str, Any]) -> str:
        """Generate a comprehensive explanation for a trading recommendation"""
        
        action = recommendation_data.get('action', 'HOLD')
        symbol = recommendation_data.get('symbol', 'UNKNOWN')
        confidence = recommendation_data.get('confidence', 0.5)
        reasoning = recommendation_data.get('reasoning', '')
        analysis_data = recommendation_data.get('analysis', {})
        
        # Build explanation based on style
        if self.style == ExplanationStyle.CONCISE:
            return self._generate_concise_explanation(action, symbol, confidence, reasoning)
        elif self.style == ExplanationStyle.TECHNICAL:
            return self._generate_technical_explanation(action, symbol, confidence, analysis_data)
        elif self.style == ExplanationStyle.BEGINNER:
            return self._generate_beginner_explanation(action, symbol, confidence, reasoning)
        else:  # DETAILED
            return self._generate_detailed_explanation(action, symbol, confidence, reasoning, analysis_data)
    
    def _generate_concise_explanation(self, action: str, symbol: str, confidence: float, reasoning: str) -> str:
        """Generate a brief explanation"""
        confidence_text = self._get_confidence_text(confidence)
        return f"{action} {symbol} - {confidence_text} confidence. {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}"
    
    def _generate_detailed_explanation(self, action: str, symbol: str, confidence: float, 
                                     reasoning: str, analysis_data: Dict[str, Any]) -> str:
        """Generate a comprehensive explanation with full context"""
        
        explanation_parts = []
        
        # Header with action and confidence
        confidence_text = self._get_confidence_text(confidence)
        explanation_parts.append(f"**{action.upper()} {symbol}** - {confidence_text.upper()} CONVICTION ({confidence:.0%} confidence)")
        
        # Primary reasoning
        if reasoning:
            explanation_parts.append(f"\n**Primary Analysis:** {reasoning}")
        
        # Technical analysis details
        if analysis_data:
            technical_details = self._extract_technical_details(analysis_data)
            if technical_details:
                explanation_parts.append(f"\n**Technical Details:** {technical_details}")
        
        # Risk and position sizing guidance
        risk_guidance = self._generate_risk_guidance(action, confidence, analysis_data)
        if risk_guidance:
            explanation_parts.append(f"\n**Risk Management:** {risk_guidance}")
        
        # Timing and execution guidance
        timing_guidance = self._generate_timing_guidance(action, analysis_data)
        if timing_guidance:
            explanation_parts.append(f"\n**Execution Timing:** {timing_guidance}")
        
        return "\n".join(explanation_parts)
    
    def _generate_technical_explanation(self, action: str, symbol: str, confidence: float, 
                                      analysis_data: Dict[str, Any]) -> str:
        """Generate technical analysis focused explanation"""
        
        explanation_parts = []
        
        # Technical signal summary
        explanation_parts.append(f"{action} {symbol} based on technical analysis:")
        
        # Trend analysis
        trend_data = analysis_data.get('trend_analysis', {})
        if trend_data:
            trend = trend_data.get('trend', 'NEUTRAL')
            strength = trend_data.get('strength', 0)
            signals = trend_data.get('signals', [])
            
            explanation_parts.append(f"• Trend: {trend} (strength: {strength:.1f}%)")
            if signals:
                explanation_parts.append(f"• Trend signals: {', '.join(signals)}")
        
        # Momentum analysis
        momentum_data = analysis_data.get('momentum_analysis', {})
        if momentum_data:
            rsi = momentum_data.get('rsi', 50)
            macd = momentum_data.get('macd', 0)
            signals = momentum_data.get('signals', [])
            
            explanation_parts.append(f"• RSI: {rsi:.1f} {'(Overbought)' if rsi > 70 else '(Oversold)' if rsi < 30 else ''}")
            explanation_parts.append(f"• MACD: {macd:.4f} {'(Bullish)' if macd > 0 else '(Bearish)'}")
            if signals:
                explanation_parts.append(f"• Momentum signals: {', '.join(signals)}")
        
        # Volatility context
        volatility_data = analysis_data.get('volatility_analysis', {})
        if volatility_data:
            vol = volatility_data.get('volatility', 0.15)
            regime = volatility_data.get('regime', 'MEDIUM')
            explanation_parts.append(f"• Volatility: {vol:.1%} ({regime} regime)")
        
        return "\n".join(explanation_parts)
    
    def _generate_beginner_explanation(self, action: str, symbol: str, confidence: float, reasoning: str) -> str:
        """Generate simple explanation for beginner traders"""
        
        # Action explanation
        action_explanations = {
            'BUY': f"Consider buying {symbol}. This means you would purchase shares expecting the price to go up.",
            'SELL': f"Consider selling {symbol}. This means you would sell shares you own or avoid buying new ones.",
            'HOLD': f"Hold your current position in {symbol}. This means don't make any changes right now.",
            'REDUCE': f"Consider reducing your position in {symbol}. This means sell some (but not all) of your shares.",
            'INCREASE': f"Consider increasing your position in {symbol}. This means buy more shares if you already own some."
        }
        
        explanation = action_explanations.get(action, f"Consider {action.lower()} action for {symbol}.")
        
        # Confidence explanation
        if confidence >= 0.7:
            confidence_note = "We're quite confident about this recommendation."
        elif confidence >= 0.5:
            confidence_note = "We have moderate confidence in this recommendation."
        else:
            confidence_note = "This recommendation has lower confidence - be more cautious."
        
        # Simplified reasoning
        simple_reasoning = self._simplify_reasoning(reasoning)
        
        return f"{explanation}\n\n**Why:** {simple_reasoning}\n\n**Confidence:** {confidence_note}"
    
    def _extract_technical_details(self, analysis_data: Dict[str, Any]) -> str:
        """Extract and format technical analysis details"""
        details = []
        
        # Moving averages
        trend_data = analysis_data.get('trend_analysis', {})
        if 'short_ma' in trend_data and 'long_ma' in trend_data:
            short_ma = trend_data['short_ma']
            long_ma = trend_data['long_ma']
            if not (pd.isna(short_ma) or pd.isna(long_ma)):
                details.append(f"20-day MA: ${short_ma:.2f}, 50-day MA: ${long_ma:.2f}")
        
        # Current price vs MA
        if 'price_vs_short_ma' in trend_data:
            price_vs_ma = trend_data['price_vs_short_ma']
            details.append(f"Price vs 20-day MA: {price_vs_ma:+.1f}%")
        
        # Technical signals
        all_signals = analysis_data.get('signals', [])
        if all_signals:
            signal_descriptions = {
                'GOLDEN_CROSS': '20-day MA crossed above 50-day MA (bullish)',
                'DEATH_CROSS': '20-day MA crossed below 50-day MA (bearish)',
                'RSI_OVERBOUGHT': 'RSI indicates overbought conditions',
                'RSI_OVERSOLD': 'RSI indicates oversold conditions',
                'MACD_POSITIVE': 'MACD line is positive (bullish momentum)',
                'MACD_NEGATIVE': 'MACD line is negative (bearish momentum)'
            }
            
            described_signals = [signal_descriptions.get(signal, signal) for signal in all_signals[:3]]
            details.append(f"Key signals: {'; '.join(described_signals)}")
        
        return "; ".join(details)
    
    def _generate_risk_guidance(self, action: str, confidence: float, analysis_data: Dict[str, Any]) -> str:
        """Generate risk management guidance"""
        guidance_parts = []
        
        # Position sizing based on confidence
        if action in ['BUY', 'INCREASE']:
            if confidence >= 0.7:
                guidance_parts.append("Consider standard position size (10-15% of portfolio)")
            elif confidence >= 0.5:
                guidance_parts.append("Consider smaller position size (5-10% of portfolio)")
            else:
                guidance_parts.append("Consider minimal position size (2-5% of portfolio)")
        
        # Stop loss suggestions
        volatility_data = analysis_data.get('volatility_analysis', {})
        if volatility_data:
            vol_regime = volatility_data.get('regime', 'MEDIUM')
            if vol_regime == 'HIGH':
                guidance_parts.append("Use wider stop losses due to high volatility")
            elif vol_regime == 'LOW':
                guidance_parts.append("Can use tighter stop losses in low volatility environment")
        
        # General risk reminders
        if confidence < 0.5:
            guidance_parts.append("Consider paper trading this recommendation first")
        
        return "; ".join(guidance_parts)
    
    def _generate_timing_guidance(self, action: str, analysis_data: Dict[str, Any]) -> str:
        """Generate timing and execution guidance"""
        guidance_parts = []
        
        # Monday execution focus
        guidance_parts.append("Best executed at Monday market open for optimal timing")
        
        # Market conditions timing
        volatility_data = analysis_data.get('volatility_analysis', {})
        if volatility_data:
            bb_position = volatility_data.get('bollinger_position', 'MIDDLE')
            if bb_position == 'UPPER' and action == 'SELL':
                guidance_parts.append("Good timing as price is near upper Bollinger Band")
            elif bb_position == 'LOWER' and action == 'BUY':
                guidance_parts.append("Good timing as price is near lower Bollinger Band")
        
        # Momentum timing
        momentum_data = analysis_data.get('momentum_analysis', {})
        if momentum_data:
            momentum = momentum_data.get('momentum', 'NEUTRAL')
            if momentum == 'BULLISH' and action == 'BUY':
                guidance_parts.append("Momentum supports the buy signal")
            elif momentum == 'BEARISH' and action == 'SELL':
                guidance_parts.append("Momentum supports the sell signal")
        
        return "; ".join(guidance_parts)
    
    def _get_confidence_text(self, confidence: float) -> str:
        """Convert confidence score to descriptive text"""
        if confidence >= self.confidence_thresholds["very_high"]:
            return "very high"
        elif confidence >= self.confidence_thresholds["high"]:
            return "high"
        elif confidence >= self.confidence_thresholds["medium"]:
            return "medium"
        else:
            return "low"
    
    def _simplify_reasoning(self, reasoning: str) -> str:
        """Simplify technical reasoning for beginners"""
        # Replace technical terms with simpler explanations
        replacements = {
            'golden cross': 'short-term average crossed above long-term average (bullish signal)',
            'death cross': 'short-term average crossed below long-term average (bearish signal)',
            'RSI': 'momentum indicator',
            'MACD': 'trend-following indicator',
            'bollinger bands': 'volatility bands',
            'overbought': 'price may be too high',
            'oversold': 'price may be too low',
            'bullish': 'positive/upward',
            'bearish': 'negative/downward'
        }
        
        simplified = reasoning.lower()
        for technical_term, simple_term in replacements.items():
            simplified = simplified.replace(technical_term, simple_term)
        
        return simplified.capitalize()
    
    def generate_portfolio_explanation(self, recommendations: List[Dict[str, Any]], 
                                     portfolio_data: Dict[str, Any]) -> str:
        """Generate explanation for overall portfolio recommendations"""
        
        explanation_parts = []
        
        # Portfolio overview
        total_value = portfolio_data.get('total_value', 100000)
        explanation_parts.append(f"**Portfolio Analysis** (Total Value: ${total_value:,.2f})")
        
        # Action summary
        buy_count = len([r for r in recommendations if r.get('action') == 'BUY'])
        sell_count = len([r for r in recommendations if r.get('action') == 'SELL'])
        hold_count = len([r for r in recommendations if r.get('action') == 'HOLD'])
        
        explanation_parts.append(f"**Weekly Actions:** {buy_count} Buy, {sell_count} Sell, {hold_count} Hold recommendations")
        
        # Market regime analysis
        if any('trend_analysis' in r.get('analysis', {}) for r in recommendations):
            bullish_trends = len([r for r in recommendations 
                                if r.get('analysis', {}).get('trend_analysis', {}).get('trend') == 'BULLISH'])
            bearish_trends = len([r for r in recommendations 
                                if r.get('analysis', {}).get('trend_analysis', {}).get('trend') == 'BEARISH'])
            
            if bullish_trends > bearish_trends:
                explanation_parts.append("**Market Outlook:** Generally bullish conditions across analyzed assets")
            elif bearish_trends > bullish_trends:
                explanation_parts.append("**Market Outlook:** Generally bearish conditions across analyzed assets")
            else:
                explanation_parts.append("**Market Outlook:** Mixed signals, neutral market conditions")
        
        # Risk assessment
        high_confidence_recs = [r for r in recommendations if r.get('confidence', 0) >= 0.7]
        if high_confidence_recs:
            explanation_parts.append(f"**High Confidence Actions:** {len(high_confidence_recs)} recommendations with high conviction")
        
        # Diversification note
        assets = [r.get('symbol') for r in recommendations]
        crypto_assets = [a for a in assets if a in ['BTC', 'ETH', 'SOL']]
        equity_assets = [a for a in assets if a in ['SPY', 'QQQ', 'IWM']]
        
        if crypto_assets and equity_assets:
            explanation_parts.append("**Diversification:** Recommendations span both traditional equities and cryptocurrencies")
        
        return "\n\n".join(explanation_parts)
    
    def generate_monday_action_plan(self, recommendations: List[Dict[str, Any]]) -> str:
        """Generate specific Monday execution plan"""
        
        plan_parts = []
        plan_parts.append("🗓️ **MONDAY MARKET OPEN ACTION PLAN**")
        
        # Immediate actions (high confidence)
        immediate_actions = [r for r in recommendations if r.get('confidence', 0) >= 0.7]
        if immediate_actions:
            plan_parts.append("\n**🚀 IMMEDIATE ACTIONS (Execute at Market Open):**")
            for i, rec in enumerate(immediate_actions, 1):
                symbol = rec.get('symbol', '')
                action = rec.get('action', '')
                quantity = rec.get('quantity', 0)
                price = rec.get('current_price', 0)
                
                plan_parts.append(f"{i}. {action} {quantity:.4f} shares of {symbol} at ~${price:.2f}")
                plan_parts.append(f"   → {rec.get('reasoning', '')[:80]}...")
        
        # Monitor closely (medium confidence)
        monitor_actions = [r for r in recommendations if 0.5 <= r.get('confidence', 0) < 0.7]
        if monitor_actions:
            plan_parts.append("\n**👀 MONITOR CLOSELY (Watch for confirmation):**")
            for rec in monitor_actions:
                symbol = rec.get('symbol', '')
                action = rec.get('action', '')
                plan_parts.append(f"• {symbol}: Potential {action} - wait for stronger signals")
        
        # Pre-market checklist
        plan_parts.append("\n**📋 PRE-MARKET CHECKLIST:**")
        plan_parts.append("• Check overnight news and earnings announcements")
        plan_parts.append("• Review pre-market price action for significant gaps")
        plan_parts.append("• Confirm account buying power and available shares to sell")
        plan_parts.append("• Set limit orders slightly below market for buys, above market for sells")
        
        return "\n".join(plan_parts)


if __name__ == "__main__":
    # Test the explanation generator
    import pandas as pd
    
    # Sample recommendation data
    test_recommendation = {
        'action': 'BUY',
        'symbol': 'SPY',
        'confidence': 0.75,
        'reasoning': 'Golden cross signal with RSI oversold condition and strong momentum confirmation',
        'analysis': {
            'trend_analysis': {
                'trend': 'BULLISH',
                'strength': 3.2,
                'signals': ['GOLDEN_CROSS', 'PRICE_ABOVE_MA'],
                'short_ma': 475.50,
                'long_ma': 472.30,
                'price_vs_short_ma': 1.2
            },
            'momentum_analysis': {
                'momentum': 'BULLISH',
                'rsi': 35.2,
                'macd': 0.0023,
                'signals': ['RSI_OVERSOLD', 'MACD_POSITIVE']
            },
            'volatility_analysis': {
                'volatility': 0.18,
                'regime': 'MEDIUM',
                'bollinger_position': 'LOWER'
            },
            'signals': ['GOLDEN_CROSS', 'RSI_OVERSOLD', 'MACD_POSITIVE']
        }
    }
    
    print("=== EXPLANATION GENERATOR TEST ===")
    
    # Test different explanation styles
    for style in ExplanationStyle:
        print(f"\n--- {style.value.upper()} STYLE ---")
        generator = ExplanationGenerator(style)
        explanation = generator.generate_recommendation_explanation(test_recommendation)
        print(explanation)
    
    # Test Monday action plan
    print("\n=== MONDAY ACTION PLAN ===")
    generator = ExplanationGenerator()
    action_plan = generator.generate_monday_action_plan([test_recommendation])
    print(action_plan)