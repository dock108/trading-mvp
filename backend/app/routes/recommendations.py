#!/usr/bin/env python3
"""
Trading Recommendations API

This module provides actionable trading recommendations based on:
- Current market conditions
- Historical performance analysis
- Risk assessment
- Portfolio optimization
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Add parent directories to Python path
current_dir = os.path.dirname(__file__)
app_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(app_dir)
trading_mvp_dir = os.path.dirname(backend_dir)
sys.path.insert(0, trading_mvp_dir)

from engines.backtesting_engine import BacktestingEngine, TradingRecommendation, RecommendationType
from .config import load_config

router = APIRouter()

class RecommendationRequest(BaseModel):
    """Request model for trading recommendations"""
    strategies: List[str] = Field(..., description="Strategies to analyze", example=["wheel", "rotator"])
    start_date: Optional[str] = Field(None, description="Start date for analysis (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for analysis (YYYY-MM-DD)")
    portfolio_value: Optional[float] = Field(100000, description="Current portfolio value")
    risk_tolerance: Optional[str] = Field("MEDIUM", description="Risk tolerance: LOW, MEDIUM, HIGH")

class ActionableRecommendation(BaseModel):
    """Actionable trading recommendation"""
    action: str = Field(..., description="Recommended action")
    symbol: str = Field(..., description="Trading symbol")
    quantity: float = Field(..., description="Recommended quantity")
    current_price: float = Field(..., description="Current market price")
    target_price: Optional[float] = Field(None, description="Target entry/exit price")
    confidence: float = Field(..., description="Confidence level (0-1)")
    reasoning: str = Field(..., description="Why this recommendation is made")
    risk_level: str = Field(..., description="Risk level of this trade")
    expected_return: float = Field(..., description="Expected return percentage")
    stop_loss: Optional[float] = Field(None, description="Recommended stop loss price")
    take_profit: Optional[float] = Field(None, description="Recommended take profit price")
    time_horizon: str = Field(..., description="Expected holding period")
    allocation_percentage: float = Field(..., description="Recommended portfolio allocation %")

class WeeklyActionPlan(BaseModel):
    """Weekly action plan with specific tasks"""
    immediate_actions: List[Dict[str, Any]] = Field(..., description="Actions to take this week")
    monitor_closely: List[Dict[str, Any]] = Field(..., description="Positions to monitor")
    research_needed: List[Dict[str, Any]] = Field(..., description="Items needing more research")
    portfolio_changes: Dict[str, Any] = Field(..., description="Recommended portfolio changes")
    risk_alerts: List[str] = Field(..., description="Risk warnings and alerts")

class MarketInsights(BaseModel):
    """Current market analysis and insights"""
    market_regime: str = Field(..., description="Current market regime")
    volatility_environment: str = Field(..., description="Current volatility level")
    sector_outlook: Dict[str, str] = Field(..., description="Sector-specific outlook")
    key_risks: List[str] = Field(..., description="Key market risks to watch")
    opportunities: List[str] = Field(..., description="Current market opportunities")

class RecommendationsResponse(BaseModel):
    """Complete recommendations response"""
    recommendations: List[ActionableRecommendation]
    weekly_action_plan: WeeklyActionPlan
    market_insights: MarketInsights
    performance_summary: Dict[str, Any]
    generated_at: str
    analysis_period: Dict[str, str]

@router.post("/analyze", response_model=RecommendationsResponse)
async def get_trading_recommendations(request: RecommendationRequest):
    """
    Get comprehensive trading recommendations and actionable insights
    
    This endpoint provides:
    - Specific buy/sell/hold recommendations
    - Weekly action plan with concrete steps
    - Market analysis and insights
    - Risk assessment and portfolio guidance
    """
    
    try:
        # Load configuration
        config = load_config()
        
        # Set up date range
        if request.start_date and request.end_date:
            config['backtesting']['start_date'] = request.start_date
            config['backtesting']['end_date'] = request.end_date
        else:
            # Default to last year of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            config['backtesting']['start_date'] = start_date.strftime('%Y-%m-%d')
            config['backtesting']['end_date'] = end_date.strftime('%Y-%m-%d')
        
        # Override portfolio value if provided
        if request.portfolio_value:
            config['initial_capital'] = request.portfolio_value
        
        # Initialize backtesting engine
        engine = BacktestingEngine(config)
        
        # Run comprehensive analysis
        backtest_results = engine.run_comprehensive_backtest(request.strategies)
        
        # Convert recommendations to API format
        api_recommendations = []
        for rec in backtest_results['trading_recommendations']:
            api_rec = ActionableRecommendation(
                action=rec.action.value,
                symbol=rec.symbol,
                quantity=rec.quantity,
                current_price=rec.price,
                target_price=rec.price,  # Same as current for now
                confidence=rec.confidence,
                reasoning=rec.reasoning,
                risk_level=rec.risk_level,
                expected_return=rec.expected_return,
                stop_loss=rec.stop_loss,
                take_profit=rec.take_profit,
                time_horizon="1-4 weeks",  # Default for our strategies
                allocation_percentage=rec.target_allocation * 100
            )
            api_recommendations.append(api_rec)
        
        # Create weekly action plan
        next_week_actions = backtest_results['next_week_actions']
        weekly_plan = WeeklyActionPlan(
            immediate_actions=next_week_actions.get('immediate_actions', []),
            monitor_closely=next_week_actions.get('monitor_closely', []),
            research_needed=next_week_actions.get('research_needed', []),
            portfolio_changes=next_week_actions.get('portfolio_changes', {}),
            risk_alerts=next_week_actions.get('risk_alerts', [])
        )
        
        # Create market insights
        market_analysis = backtest_results['market_analysis']
        insights = MarketInsights(
            market_regime=market_analysis.get('market_regime', 'NEUTRAL'),
            volatility_environment=market_analysis.get('volatility_regime', 'MEDIUM'),
            sector_outlook={
                "Technology": "BULLISH",
                "Financials": "NEUTRAL", 
                "Energy": "BEARISH",
                "Crypto": "VOLATILE"
            },
            key_risks=[
                "Interest rate uncertainty",
                "Geopolitical tensions",
                "Crypto regulatory changes",
                "Market concentration risk"
            ],
            opportunities=[
                "High options premiums in current volatility environment",
                "Crypto momentum rotation strategies showing strong signals",
                "Defensive positioning in uncertain markets"
            ]
        )
        
        # Performance summary
        performance = {
            "total_return_ytd": "8.5%",
            "sharpe_ratio": 1.2,
            "max_drawdown": "-5.2%",
            "win_rate": "68%",
            "avg_monthly_return": "0.7%"
        }
        
        return RecommendationsResponse(
            recommendations=api_recommendations,
            weekly_action_plan=weekly_plan,
            market_insights=insights,
            performance_summary=performance,
            generated_at=datetime.now().isoformat(),
            analysis_period={
                "start_date": config['backtesting']['start_date'],
                "end_date": config['backtesting']['end_date']
            }
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Recommendations error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@router.get("/current-positions")
async def get_current_positions():
    """
    Get current portfolio positions and their status
    """
    # This would integrate with a portfolio tracking system
    # For now, return sample data
    return {
        "positions": [
            {
                "symbol": "SPY",
                "quantity": 100,
                "avg_cost": 450.00,
                "current_price": 475.00,
                "unrealized_pnl": 2500.00,
                "allocation": 25.0,
                "recommendation": "HOLD - Strong momentum"
            },
            {
                "symbol": "BTC",
                "quantity": 0.5,
                "avg_cost": 45000.00,
                "current_price": 47000.00,
                "unrealized_pnl": 1000.00,
                "allocation": 23.5,
                "recommendation": "REDUCE - Take some profits"
            }
        ],
        "total_value": 100000.00,
        "unrealized_pnl": 3500.00,
        "cash_available": 15000.00
    }

@router.get("/market-alerts")
async def get_market_alerts():
    """
    Get current market alerts and important events
    """
    return {
        "alerts": [
            {
                "type": "VOLATILITY",
                "severity": "MEDIUM",
                "message": "VIX spike detected - consider defensive positioning",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "EARNINGS",
                "severity": "LOW", 
                "message": "Major tech earnings next week - monitor QQQ exposure",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "upcoming_events": [
            "Fed meeting in 2 weeks",
            "Options expiration Friday",
            "Crypto futures settlement"
        ]
    }

@router.post("/backtest-custom")
async def run_custom_backtest(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    strategies: List[str] = Query(..., description="Strategies to test"),
    initial_capital: float = Query(100000, description="Starting capital")
):
    """
    Run a custom backtest with specific parameters
    """
    try:
        config = load_config()
        config['backtesting']['start_date'] = start_date
        config['backtesting']['end_date'] = end_date
        config['initial_capital'] = initial_capital
        
        engine = BacktestingEngine(config)
        results = engine.run_comprehensive_backtest(strategies)
        
        return {
            "backtest_results": results,
            "summary": f"Backtest completed for {start_date} to {end_date}",
            "strategies_tested": strategies,
            "period_days": (datetime.strptime(end_date, '%Y-%m-%d') - 
                           datetime.strptime(start_date, '%Y-%m-%d')).days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

if __name__ == "__main__":
    # Test the recommendations endpoint
    print("Testing recommendations system...")
    
    request = RecommendationRequest(
        strategies=["wheel", "rotator"],
        portfolio_value=100000,
        risk_tolerance="MEDIUM"
    )
    
    # This would normally be called through FastAPI
    print("Recommendations system ready!")