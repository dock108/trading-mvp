"""
Strategy Recommendation Engine

Core engine that analyzes market data, applies strategy rules, and generates
actionable trading recommendations with detailed explanations. Designed for
Monday trading execution with weekend analysis.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import our custom modules
from core.technical_indicators import TechnicalIndicators, MarketAnalysis
from core.explanation_generator import ExplanationGenerator, ExplanationStyle

logger = logging.getLogger(__name__)


class RecommendationAction(Enum):
    """Possible recommendation actions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    INCREASE = "INCREASE"


class RiskLevel(Enum):
    """Risk levels for recommendations"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class TradingRecommendation:
    """Structured trading recommendation with all necessary details"""
    symbol: str
    action: RecommendationAction
    confidence: float  # 0.0 to 1.0
    reasoning: str
    current_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: float = 0.0  # Suggested position size
    allocation_percentage: float = 0.0  # Portfolio allocation %
    risk_level: RiskLevel = RiskLevel.MEDIUM
    expected_return: float = 0.0  # Expected return %
    time_horizon: str = "1-4 weeks"
    analysis_data: Optional[Dict[str, Any]] = None
    generated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        data = asdict(self)
        # Convert enums to strings
        data['action'] = self.action.value
        data['risk_level'] = self.risk_level.value
        data['generated_at'] = self.generated_at.isoformat() if self.generated_at else None
        return data


class RecommendationEngine:
    """Main recommendation engine that processes market data and generates trading recommendations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.recommendation_config = config.get('recommendation_engine', {})
        self.technical_analyzer = MarketAnalysis()
        self.explanation_generator = ExplanationGenerator(ExplanationStyle.DETAILED)
        
        # Configuration parameters
        self.confidence_threshold = self.recommendation_config.get('confidence_threshold', 0.5)
        self.max_position_size = self.recommendation_config.get('max_position_size', 0.15)  # 15% max
        self.lookback_days = self.recommendation_config.get('lookback_days', 60)
        
        logger.info("RecommendationEngine initialized with configuration")
    
    def generate_recommendations(self, market_data: Dict[str, List[float]], 
                               portfolio_data: Optional[Dict[str, Any]] = None,
                               strategy_name: str = "weekly_momentum") -> List[TradingRecommendation]:
        """
        Generate trading recommendations based on current market data
        
        Args:
            market_data: Dict of symbol -> list of prices (most recent last)
            portfolio_data: Current portfolio information
            strategy_name: Strategy configuration to use
            
        Returns:
            List of TradingRecommendation objects
        """
        logger.info(f"Generating recommendations for {len(market_data)} symbols using {strategy_name} strategy")
        
        recommendations = []
        strategy_config = self._get_strategy_config(strategy_name)
        
        for symbol, prices in market_data.items():
            try:
                if len(prices) < 30:  # Minimum data requirement
                    logger.warning(f"Insufficient data for {symbol}: {len(prices)} prices")
                    continue
                
                # Perform comprehensive technical analysis
                analysis = self.technical_analyzer.comprehensive_analysis(prices, symbol)
                
                # Apply strategy rules to generate recommendation
                recommendation = self._apply_strategy_rules(symbol, prices, analysis, strategy_config, portfolio_data)
                
                if recommendation:
                    recommendations.append(recommendation)
                    logger.info(f"Generated {recommendation.action.value} recommendation for {symbol} (confidence: {recommendation.confidence:.1%})")
                
            except Exception as e:
                logger.error(f"Error generating recommendation for {symbol}: {e}", exc_info=True)
                continue
        
        # Post-process recommendations (sort by confidence, apply portfolio constraints)
        recommendations = self._post_process_recommendations(recommendations, portfolio_data)
        
        logger.info(f"Generated {len(recommendations)} total recommendations")
        return recommendations
    
    def _get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """Get configuration for specific strategy"""
        strategies = self.recommendation_config.get('strategies', {})
        strategy_config = strategies.get(strategy_name, {})
        
        # Default configuration if strategy not found
        if not strategy_config:
            logger.warning(f"Strategy '{strategy_name}' not found in config, using defaults")
            strategy_config = {
                'name': 'Default Weekly Momentum',
                'rules': [
                    {'type': 'momentum', 'lookback_days': 7, 'threshold': 0.03},
                    {'type': 'mean_reversion', 'indicator': 'RSI', 'buy_below': 30, 'sell_above': 70}
                ],
                'risk_level': 'MEDIUM'
            }
        
        return strategy_config
    
    def _apply_strategy_rules(self, symbol: str, prices: List[float], 
                            analysis: Dict[str, Any], strategy_config: Dict[str, Any],
                            portfolio_data: Optional[Dict[str, Any]]) -> Optional[TradingRecommendation]:
        """Apply strategy rules to generate a recommendation"""
        
        # Check if analysis has sufficient data
        if analysis.get('status') == 'INSUFFICIENT_DATA' or len(prices) < 30:
            return None
        
        current_price = prices[-1]
        rules = strategy_config.get('rules', [])
        
        # Initialize scoring system
        signal_score = 0.0
        max_score = len(rules)
        reasoning_parts = []
        
        # Apply each rule
        for rule in rules:
            rule_result = self._evaluate_rule(rule, prices, analysis)
            signal_score += rule_result['score']
            if rule_result['reasoning']:
                reasoning_parts.append(rule_result['reasoning'])
        
        # Determine action based on score
        confidence = signal_score / max_score if max_score > 0 else 0.5
        
        if confidence >= 0.7:
            action = RecommendationAction.BUY if signal_score > 0 else RecommendationAction.SELL
        elif confidence >= 0.5:
            action = RecommendationAction.INCREASE if signal_score > 0 else RecommendationAction.REDUCE
        else:
            action = RecommendationAction.HOLD
        
        # Adjust action based on existing positions
        if portfolio_data:
            action = self._adjust_for_existing_positions(action, symbol, portfolio_data)
        
        # Calculate position sizing and risk metrics
        position_metrics = self._calculate_position_metrics(symbol, current_price, confidence, analysis, portfolio_data)
        
        # Generate detailed reasoning
        base_reasoning = "; ".join(reasoning_parts) if reasoning_parts else analysis.get('reasoning', 'Mixed technical signals')
        
        # Create recommendation
        recommendation = TradingRecommendation(
            symbol=symbol,
            action=action,
            confidence=abs(confidence),  # Ensure positive confidence
            reasoning=base_reasoning,
            current_price=current_price,
            target_price=position_metrics['target_price'],
            stop_loss=position_metrics['stop_loss'],
            take_profit=position_metrics['take_profit'],
            position_size=position_metrics['position_size'],
            allocation_percentage=position_metrics['allocation_percentage'],
            risk_level=RiskLevel(strategy_config.get('risk_level', 'MEDIUM')),
            expected_return=position_metrics['expected_return'],
            analysis_data=analysis
        )
        
        return recommendation
    
    def _evaluate_rule(self, rule: Dict[str, Any], prices: List[float], 
                      analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single strategy rule"""
        
        rule_type = rule.get('type', '')
        score = 0.0
        reasoning = ""
        
        if rule_type == 'momentum':
            score, reasoning = self._evaluate_momentum_rule(rule, prices, analysis)
        elif rule_type == 'mean_reversion':
            score, reasoning = self._evaluate_mean_reversion_rule(rule, prices, analysis)
        elif rule_type == 'trend_following':
            score, reasoning = self._evaluate_trend_rule(rule, prices, analysis)
        elif rule_type == 'volatility':
            score, reasoning = self._evaluate_volatility_rule(rule, prices, analysis)
        else:
            logger.warning(f"Unknown rule type: {rule_type}")
        
        return {'score': score, 'reasoning': reasoning}
    
    def _evaluate_momentum_rule(self, rule: Dict[str, Any], prices: List[float], 
                               analysis: Dict[str, Any]) -> Tuple[float, str]:
        """Evaluate momentum-based rule"""
        
        lookback_days = rule.get('lookback_days', 7)
        threshold = rule.get('threshold', 0.03)  # 3% threshold
        
        if len(prices) < lookback_days + 1:
            return 0.0, ""
        
        # Calculate momentum
        current_price = prices[-1]
        past_price = prices[-(lookback_days + 1)]
        momentum = (current_price / past_price) - 1
        
        # Score based on momentum strength
        if momentum > threshold:
            score = min(momentum / threshold, 1.0)  # Cap at 1.0
            reasoning = f"{lookback_days}-day momentum: {momentum:.1%} (above {threshold:.1%} threshold)"
        elif momentum < -threshold:
            score = max(momentum / threshold, -1.0)  # Cap at -1.0
            reasoning = f"{lookback_days}-day momentum: {momentum:.1%} (below -{threshold:.1%} threshold)"
        else:
            score = 0.0
            reasoning = f"{lookback_days}-day momentum: {momentum:.1%} (within neutral range)"
        
        return score, reasoning
    
    def _evaluate_mean_reversion_rule(self, rule: Dict[str, Any], prices: List[float], 
                                    analysis: Dict[str, Any]) -> Tuple[float, str]:
        """Evaluate mean reversion rule"""
        
        indicator = rule.get('indicator', 'RSI')
        buy_below = rule.get('buy_below', 30)
        sell_above = rule.get('sell_above', 70)
        
        momentum_data = analysis.get('momentum_analysis', {})
        
        if indicator == 'RSI':
            rsi = momentum_data.get('rsi', 50)
            
            if rsi < buy_below:
                score = (buy_below - rsi) / buy_below  # Stronger signal when more oversold
                reasoning = f"RSI at {rsi:.1f} (oversold below {buy_below})"
            elif rsi > sell_above:
                score = -(rsi - sell_above) / (100 - sell_above)  # Stronger signal when more overbought
                reasoning = f"RSI at {rsi:.1f} (overbought above {sell_above})"
            else:
                score = 0.0
                reasoning = f"RSI at {rsi:.1f} (neutral range)"
        else:
            # Placeholder for other indicators
            score = 0.0
            reasoning = f"Unknown indicator: {indicator}"
        
        return score, reasoning
    
    def _evaluate_trend_rule(self, rule: Dict[str, Any], prices: List[float], 
                           analysis: Dict[str, Any]) -> Tuple[float, str]:
        """Evaluate trend-following rule"""
        
        trend_data = analysis.get('trend_analysis', {})
        trend = trend_data.get('trend', 'NEUTRAL')
        strength = trend_data.get('strength', 0)
        
        if trend == 'BULLISH':
            score = min(strength / 5.0, 1.0)  # Normalize strength to 0-1
            reasoning = f"Bullish trend (strength: {strength:.1f}%)"
        elif trend == 'BEARISH':
            score = -min(strength / 5.0, 1.0)
            reasoning = f"Bearish trend (strength: {strength:.1f}%)"
        else:
            score = 0.0
            reasoning = "Neutral trend"
        
        return score, reasoning
    
    def _evaluate_volatility_rule(self, rule: Dict[str, Any], prices: List[float], 
                                analysis: Dict[str, Any]) -> Tuple[float, str]:
        """Evaluate volatility-based rule"""
        
        volatility_data = analysis.get('volatility_analysis', {})
        vol_regime = volatility_data.get('regime', 'MEDIUM')
        volatility = volatility_data.get('volatility', 0.15)
        
        # High volatility can be good for options strategies, bad for momentum
        action = rule.get('action', 'avoid_high_vol')
        
        if action == 'prefer_high_vol':
            if vol_regime == 'HIGH':
                score = 0.5
                reasoning = f"High volatility environment ({volatility:.1%}) favors this strategy"
            else:
                score = 0.0
                reasoning = f"{vol_regime.lower()} volatility ({volatility:.1%})"
        else:  # avoid_high_vol
            if vol_regime == 'HIGH':
                score = -0.5
                reasoning = f"High volatility environment ({volatility:.1%}) increases risk"
            else:
                score = 0.0
                reasoning = f"{vol_regime.lower()} volatility ({volatility:.1%})"
        
        return score, reasoning
    
    def _adjust_for_existing_positions(self, action: RecommendationAction, symbol: str, 
                                     portfolio_data: Dict[str, Any]) -> RecommendationAction:
        """Adjust recommendation based on existing positions"""
        
        positions = portfolio_data.get('positions', [])
        existing_position = next((p for p in positions if p.get('symbol') == symbol), None)
        
        if existing_position:
            current_allocation = existing_position.get('allocation', 0) / 100  # Convert to decimal
            
            # Adjust actions based on current allocation
            if action == RecommendationAction.BUY and current_allocation > 0.20:  # Already 20%+
                action = RecommendationAction.HOLD
            elif action == RecommendationAction.SELL and current_allocation < 0.05:  # Less than 5%
                action = RecommendationAction.HOLD
        
        return action
    
    def _calculate_position_metrics(self, symbol: str, current_price: float, confidence: float,
                                  analysis: Dict[str, Any], portfolio_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate position sizing, targets, and risk metrics"""
        
        # Base position size on confidence and volatility
        volatility_data = analysis.get('volatility_analysis', {})
        volatility = volatility_data.get('volatility', 0.15)
        
        # Position sizing: higher confidence = larger position, higher volatility = smaller position
        base_allocation = confidence * 0.15  # Max 15% at 100% confidence
        vol_adjustment = max(0.5, 1.0 - (volatility - 0.15))  # Reduce size for high vol
        allocation_percentage = base_allocation * vol_adjustment * 100  # Convert to percentage
        
        # Calculate dollar amount
        portfolio_value = portfolio_data.get('total_value', 100000) if portfolio_data else 100000
        dollar_amount = (allocation_percentage / 100) * portfolio_value
        position_size = dollar_amount / current_price
        
        # Price targets based on technical analysis
        target_price = None
        stop_loss = None
        take_profit = None
        expected_return = 0.0
        
        # Set targets based on volatility and trend
        if volatility < 0.20:  # Low/medium volatility
            stop_loss = current_price * 0.90  # 10% stop loss
            take_profit = current_price * 1.15  # 15% take profit
            expected_return = 0.10  # 10% expected return
        else:  # High volatility
            stop_loss = current_price * 0.85  # 15% stop loss
            take_profit = current_price * 1.25  # 25% take profit
            expected_return = 0.15  # 15% expected return
        
        # Adjust for crypto vs equity
        if symbol in ['BTC', 'ETH', 'SOL']:
            stop_loss = current_price * 0.80  # Wider stops for crypto
            take_profit = current_price * 1.30
            expected_return = 0.20
        
        target_price = take_profit  # Use take profit as target
        
        return {
            'position_size': position_size,
            'allocation_percentage': allocation_percentage,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'expected_return': expected_return
        }
    
    def _post_process_recommendations(self, recommendations: List[TradingRecommendation],
                                    portfolio_data: Optional[Dict[str, Any]]) -> List[TradingRecommendation]:
        """Post-process recommendations for portfolio-level optimization"""
        
        # Sort by confidence (highest first)
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        # Apply portfolio-level constraints
        total_allocation = sum(r.allocation_percentage for r in recommendations if r.action in [RecommendationAction.BUY, RecommendationAction.INCREASE])
        
        # Scale down allocations if they exceed 100%
        if total_allocation > 100:
            scale_factor = 95 / total_allocation  # Leave 5% cash buffer
            for rec in recommendations:
                if rec.action in [RecommendationAction.BUY, RecommendationAction.INCREASE]:
                    rec.allocation_percentage *= scale_factor
                    rec.position_size *= scale_factor
        
        # Filter out very low confidence recommendations
        filtered_recommendations = [r for r in recommendations if r.confidence >= self.confidence_threshold]
        
        return filtered_recommendations
    
    def generate_explanations(self, recommendations: List[TradingRecommendation], 
                            style: ExplanationStyle = ExplanationStyle.DETAILED) -> Dict[str, str]:
        """Generate detailed explanations for all recommendations"""
        
        explanations = {}
        explanation_generator = ExplanationGenerator(style)
        
        for rec in recommendations:
            explanation_data = {
                'action': rec.action.value,
                'symbol': rec.symbol,
                'confidence': rec.confidence,
                'reasoning': rec.reasoning,
                'analysis': rec.analysis_data
            }
            
            explanation = explanation_generator.generate_recommendation_explanation(explanation_data)
            explanations[rec.symbol] = explanation
        
        return explanations
    
    def generate_monday_action_plan(self, recommendations: List[TradingRecommendation]) -> Dict[str, Any]:
        """Generate specific Monday execution plan"""
        
        # High confidence actions (execute immediately)
        immediate_actions = [r for r in recommendations if r.confidence >= 0.7]
        
        # Medium confidence actions (monitor closely)
        monitor_actions = [r for r in recommendations if 0.5 <= r.confidence < 0.7]
        
        # Low confidence actions (research needed)
        research_actions = [r for r in recommendations if r.confidence < 0.5]
        
        action_plan = {
            'immediate_actions': [
                {
                    'symbol': r.symbol,
                    'action': r.action.value,
                    'details': f"{r.action.value} {r.position_size:.4f} shares of {r.symbol} at ~${r.current_price:.2f}",
                    'reasoning': r.reasoning,
                    'confidence': f"{r.confidence:.0%}",
                    'allocation': f"{r.allocation_percentage:.1f}%"
                }
                for r in immediate_actions
            ],
            'monitor_closely': [
                {
                    'symbol': r.symbol,
                    'action': r.action.value,
                    'reasoning': r.reasoning,
                    'confidence': f"{r.confidence:.0%}"
                }
                for r in monitor_actions
            ],
            'research_needed': [
                {
                    'symbol': r.symbol,
                    'action': r.action.value,
                    'reasoning': r.reasoning,
                    'confidence': f"{r.confidence:.0%}"
                }
                for r in research_actions
            ],
            'portfolio_changes': {
                r.symbol: {
                    'target_allocation': f"{r.allocation_percentage:.1f}%",
                    'expected_return': f"{r.expected_return:.1%}",
                    'stop_loss': f"${r.stop_loss:.2f}" if r.stop_loss else "None",
                    'take_profit': f"${r.take_profit:.2f}" if r.take_profit else "None"
                }
                for r in recommendations
            },
            'risk_alerts': [
                f"HIGH RISK: {r.symbol} - {r.reasoning}" 
                for r in recommendations if r.risk_level == RiskLevel.HIGH
            ]
        }
        
        return action_plan
    
    def get_market_insights(self, recommendations: List[TradingRecommendation]) -> Dict[str, Any]:
        """Generate market insights based on recommendations"""
        
        if not recommendations:
            return {
                'market_regime': 'UNKNOWN',
                'volatility_environment': 'UNKNOWN',
                'opportunities': [],
                'key_risks': []
            }
        
        # Analyze overall market regime
        bullish_count = len([r for r in recommendations if r.action in [RecommendationAction.BUY, RecommendationAction.INCREASE]])
        bearish_count = len([r for r in recommendations if r.action in [RecommendationAction.SELL, RecommendationAction.REDUCE]])
        
        if bullish_count > bearish_count * 1.5:
            market_regime = 'BULLISH'
        elif bearish_count > bullish_count * 1.5:
            market_regime = 'BEARISH'
        else:
            market_regime = 'NEUTRAL'
        
        # Analyze volatility environment
        high_vol_count = len([r for r in recommendations if r.risk_level == RiskLevel.HIGH])
        low_vol_count = len([r for r in recommendations if r.risk_level == RiskLevel.LOW])
        
        if high_vol_count > low_vol_count:
            volatility_environment = 'HIGH'
        elif low_vol_count > high_vol_count:
            volatility_environment = 'LOW'
        else:
            volatility_environment = 'MEDIUM'
        
        # Generate opportunities and risks
        opportunities = []
        key_risks = []
        
        high_confidence_recs = [r for r in recommendations if r.confidence >= 0.7]
        if high_confidence_recs:
            opportunities.append(f"{len(high_confidence_recs)} high-confidence trading opportunities identified")
        
        crypto_recs = [r for r in recommendations if r.symbol in ['BTC', 'ETH', 'SOL']]
        if crypto_recs:
            if any(r.action == RecommendationAction.BUY for r in crypto_recs):
                opportunities.append("Crypto momentum rotation signals detected")
        
        equity_recs = [r for r in recommendations if r.symbol in ['SPY', 'QQQ', 'IWM']]
        if equity_recs:
            if any(r.action == RecommendationAction.BUY for r in equity_recs):
                opportunities.append("Favorable conditions for options wheel strategies")
        
        # Risk identification
        if volatility_environment == 'HIGH':
            key_risks.append("Elevated market volatility increases position risk")
        
        if any(r.risk_level == RiskLevel.HIGH for r in recommendations):
            key_risks.append("Some recommendations carry elevated risk levels")
        
        return {
            'market_regime': market_regime,
            'volatility_environment': volatility_environment,
            'opportunities': opportunities,
            'key_risks': key_risks
        }


if __name__ == "__main__":
    # Test the recommendation engine
    print("=== RECOMMENDATION ENGINE TEST ===")
    
    # Sample configuration
    test_config = {
        'recommendation_engine': {
            'strategies': {
                'weekly_momentum': {
                    'name': 'Weekly Momentum Strategy',
                    'rules': [
                        {'type': 'momentum', 'lookback_days': 7, 'threshold': 0.03},
                        {'type': 'mean_reversion', 'indicator': 'RSI', 'buy_below': 30, 'sell_above': 70}
                    ],
                    'risk_level': 'MEDIUM'
                }
            }
        }
    }
    
    # Sample market data
    np.random.seed(42)
    sample_data = {}
    
    for symbol in ['SPY', 'BTC']:
        prices = [100]
        for _ in range(60):
            change = np.random.normal(0, 0.02)
            prices.append(prices[-1] * (1 + change))
        sample_data[symbol] = prices
    
    # Create engine and generate recommendations
    engine = RecommendationEngine(test_config)
    recommendations = engine.generate_recommendations(sample_data)
    
    print(f"\nGenerated {len(recommendations)} recommendations:")
    for rec in recommendations:
        print(f"\n{rec.action.value} {rec.symbol}:")
        print(f"  Confidence: {rec.confidence:.1%}")
        print(f"  Reasoning: {rec.reasoning}")
        print(f"  Allocation: {rec.allocation_percentage:.1f}%")
    
    # Test action plan generation
    action_plan = engine.generate_monday_action_plan(recommendations)
    print(f"\nImmediate actions: {len(action_plan['immediate_actions'])}")
    print(f"Monitor closely: {len(action_plan['monitor_closely'])}")
    
    print("\n=== TEST COMPLETE ===")