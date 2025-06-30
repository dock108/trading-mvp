#!/usr/bin/env python3
"""
Recommendation Engine CLI

Command-line interface for generating and managing trading recommendations.
Provides weekend analysis, Monday action plans, and strategy insights.
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import project modules
from core.config import ConfigManager, ConfigError
from data.price_fetcher import PriceFetcher, DataSourceError
from engines.recommendation_engine import RecommendationEngine
from core.explanation_generator import ExplanationGenerator, ExplanationStyle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class RecommendationCLI:
    """Command-line interface for the recommendation engine."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = None
        self.price_fetcher = None
        self.recommendation_engine = None
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description='Trading Recommendation Engine CLI - Generate data-driven trading recommendations',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_examples_text()
        )
        
        # Global options
        parser.add_argument(
            '--config', '-c',
            default='config/config.yaml',
            help='Configuration file path (default: config/config.yaml)'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--data-mode',
            choices=['live', 'mock', 'hybrid'],
            help='Override data mode from config'
        )
        
        # Create subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Generate recommendations command
        generate_parser = subparsers.add_parser(
            'generate',
            help='Generate new trading recommendations'
        )
        generate_parser.add_argument(
            '--strategy',
            choices=['weekly_momentum', 'mean_reversion', 'wheel_support', 'crypto_momentum'],
            default='weekly_momentum',
            help='Strategy to use for recommendations (default: weekly_momentum)'
        )
        generate_parser.add_argument(
            '--symbols',
            nargs='*',
            help='Specific symbols to analyze (overrides config)'
        )
        generate_parser.add_argument(
            '--output', '-o',
            help='Output file for recommendations (JSON format)'
        )
        generate_parser.add_argument(
            '--format',
            choices=['json', 'csv', 'text'],
            default='json',
            help='Output format (default: json)'
        )
        
        # Weekend analysis command
        weekend_parser = subparsers.add_parser(
            'weekend',
            help='Run weekend analysis for Monday trading'
        )
        weekend_parser.add_argument(
            '--all-strategies',
            action='store_true',
            help='Analyze using all configured strategies'
        )
        weekend_parser.add_argument(
            '--output-dir',
            default='recommendations',
            help='Output directory for analysis files (default: recommendations/)'
        )
        
        # Monday action plan command
        monday_parser = subparsers.add_parser(
            'monday',
            help='Generate Monday execution action plan'
        )
        monday_parser.add_argument(
            '--input',
            help='Input recommendations file (from weekend analysis)'
        )
        monday_parser.add_argument(
            '--style',
            choices=['concise', 'detailed', 'technical', 'beginner'],
            default='detailed',
            help='Explanation style (default: detailed)'
        )
        
        # Market insights command
        insights_parser = subparsers.add_parser(
            'insights',
            help='Generate market insights and analysis'
        )
        insights_parser.add_argument(
            '--symbols',
            nargs='*',
            help='Symbols to analyze for insights'
        )
        insights_parser.add_argument(
            '--timeframe',
            choices=['daily', 'weekly', 'monthly'],
            default='weekly',
            help='Analysis timeframe (default: weekly)'
        )
        
        # Health check command
        health_parser = subparsers.add_parser(
            'health',
            help='Check data sources and system health'
        )
        health_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed health information'
        )
        
        return parser
    
    def _get_examples_text(self) -> str:
        """Get CLI examples text."""
        return """
Examples:
  # Generate recommendations using weekly momentum strategy
  python recommend.py generate --strategy weekly_momentum
  
  # Run full weekend analysis with all strategies
  python recommend.py weekend --all-strategies --output-dir weekend_analysis/
  
  # Generate Monday action plan with detailed explanations
  python recommend.py monday --input recommendations.json --style detailed
  
  # Get market insights for specific symbols
  python recommend.py insights --symbols SPY BTC ETH --timeframe weekly
  
  # Check system health and data sources
  python recommend.py health --detailed
  
  # Generate recommendations for specific symbols only
  python recommend.py generate --symbols SPY QQQ BTC --output my_recs.json
        """
    
    def initialize_systems(self, args):
        """Initialize configuration and systems."""
        try:
            # Load configuration
            self.config = self.config_manager.load_config(args.config)
            
            # Override data mode if specified
            if args.data_mode:
                self.config['data_mode'] = args.data_mode
                logger.info(f"CLI override: data_mode = {args.data_mode}")
            
            # Configure logging level
            if args.verbose:
                logging.getLogger().setLevel(logging.DEBUG)
                logger.debug("Verbose logging enabled")
            
            # Initialize price fetcher
            data_mode = self.config.get('data_mode', 'mock')
            if data_mode != 'mock':
                logger.info(f"Initializing PriceFetcher for {data_mode} data mode")
                self.price_fetcher = PriceFetcher()
                logger.info("PriceFetcher initialized successfully")
            else:
                logger.info("Using mock data mode - no live data fetcher needed")
            
            # Initialize recommendation engine
            self.recommendation_engine = RecommendationEngine(self.config)
            logger.info("Recommendation engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize systems: {e}")
            raise
    
    def cmd_generate(self, args) -> int:
        """Generate trading recommendations."""
        try:
            logger.info(f"Generating recommendations using {args.strategy} strategy")
            
            # Get market data
            if self.price_fetcher:
                market_data = self.price_fetcher.get_recommendation_data_batch(self.config)
            else:
                # Use mock data for testing
                logger.info("Using mock market data for recommendation generation")
                market_data = self._generate_mock_market_data()
            
            # Filter to specific symbols if requested
            if args.symbols:
                logger.info(f"Filtering to specific symbols: {args.symbols}")
                market_data = {symbol: data for symbol, data in market_data.items() 
                             if symbol in args.symbols}
            
            if not market_data:
                logger.error("No market data available for analysis")
                return 1
            
            # Generate recommendations
            recommendations = self.recommendation_engine.generate_recommendations(
                market_data, strategy_name=args.strategy
            )
            
            if not recommendations:
                logger.warning("No recommendations generated")
                return 0
            
            # Output results
            self._output_recommendations(recommendations, args)
            
            logger.info(f"Generated {len(recommendations)} recommendations successfully")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return 1
    
    def cmd_weekend(self, args) -> int:
        """Run weekend analysis."""
        try:
            logger.info("Starting weekend analysis for Monday trading")
            
            # Create output directory
            output_dir = Path(args.output_dir)
            output_dir.mkdir(exist_ok=True)
            
            # Get fresh market data
            if self.price_fetcher:
                market_data = self.price_fetcher.get_weekend_analysis_data(self.config)
            else:
                market_data = self._generate_mock_market_data()
            
            if not market_data:
                logger.error("No market data available for weekend analysis")
                return 1
            
            # Analyze with configured strategies
            strategies = ['weekly_momentum']  # Default strategy
            if args.all_strategies:
                rec_config = self.config.get('recommendation_engine', {})
                strategies = list(rec_config.get('strategies', {}).keys())
            
            all_recommendations = []
            
            for strategy in strategies:
                logger.info(f"Analyzing with {strategy} strategy")
                
                recommendations = self.recommendation_engine.generate_recommendations(
                    market_data, strategy_name=strategy
                )
                
                if recommendations:
                    all_recommendations.extend(recommendations)
                    
                    # Save strategy-specific results
                    strategy_file = output_dir / f"{strategy}_recommendations.json"
                    self._save_recommendations_json(recommendations, strategy_file)
                    logger.info(f"Saved {len(recommendations)} recommendations to {strategy_file}")
            
            if all_recommendations:
                # Generate Monday action plan
                action_plan = self.recommendation_engine.generate_monday_action_plan(all_recommendations)
                
                # Save comprehensive results
                results = {
                    'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                    'strategies_analyzed': strategies,
                    'total_recommendations': len(all_recommendations),
                    'market_data_symbols': list(market_data.keys()),
                    'recommendations': [rec.to_dict() for rec in all_recommendations],
                    'monday_action_plan': action_plan,
                    'market_insights': self.recommendation_engine.get_market_insights(all_recommendations)
                }
                
                # Save comprehensive analysis
                weekend_file = output_dir / f"weekend_analysis_{datetime.now().strftime('%Y%m%d')}.json"
                self._save_json(results, weekend_file)
                
                # Save readable action plan
                action_plan_file = output_dir / f"monday_action_plan_{datetime.now().strftime('%Y%m%d')}.txt"
                self._save_action_plan_text(action_plan, action_plan_file)
                
                logger.info(f"Weekend analysis complete - {len(all_recommendations)} total recommendations")
                logger.info(f"Files saved to {output_dir}/")
                
                # Print summary
                print(f"\n📊 Weekend Analysis Summary")
                print(f"{'='*50}")
                print(f"Strategies analyzed: {', '.join(strategies)}")
                print(f"Symbols analyzed: {len(market_data)}")
                print(f"Total recommendations: {len(all_recommendations)}")
                print(f"High confidence actions: {len(action_plan.get('immediate_actions', []))}")
                print(f"Monitor closely: {len(action_plan.get('monitor_closely', []))}")
                print(f"\nFiles saved to: {output_dir}/")
            else:
                logger.warning("No recommendations generated from weekend analysis")
            
            return 0
            
        except Exception as e:
            logger.error(f"Weekend analysis failed: {e}")
            return 1
    
    def cmd_monday(self, args) -> int:
        """Generate Monday action plan."""
        try:
            logger.info("Generating Monday execution action plan")
            
            # Load recommendations from file or generate fresh ones
            if args.input:
                recommendations = self._load_recommendations(args.input)
            else:
                logger.info("No input file specified, generating fresh recommendations")
                # Generate fresh recommendations
                if self.price_fetcher:
                    market_data = self.price_fetcher.get_recommendation_data_batch(self.config)
                else:
                    market_data = self._generate_mock_market_data()
                
                recommendations = self.recommendation_engine.generate_recommendations(market_data)
            
            if not recommendations:
                logger.error("No recommendations available for Monday action plan")
                return 1
            
            # Generate action plan
            action_plan = self.recommendation_engine.generate_monday_action_plan(recommendations)
            
            # Generate explanations
            explanation_style = ExplanationStyle(args.style)
            explanations = self.recommendation_engine.generate_explanations(recommendations, explanation_style)
            
            # Output Monday action plan
            print(f"\n🗓️  MONDAY TRADING ACTION PLAN")
            print(f"{'='*60}")
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total recommendations: {len(recommendations)}")
            print()
            
            # Immediate actions
            immediate = action_plan.get('immediate_actions', [])
            if immediate:
                print(f"🚀 IMMEDIATE ACTIONS ({len(immediate)} items)")
                print("-" * 40)
                for i, action in enumerate(immediate, 1):
                    print(f"{i}. {action.get('details', 'N/A')}")
                    print(f"   Reasoning: {action.get('reasoning', 'N/A')[:80]}...")
                    print(f"   Confidence: {action.get('confidence', 'N/A')}")
                    print()
            
            # Monitor closely
            monitor = action_plan.get('monitor_closely', [])
            if monitor:
                print(f"👀 MONITOR CLOSELY ({len(monitor)} items)")
                print("-" * 40)
                for action in monitor:
                    print(f"• {action.get('symbol', 'N/A')}: {action.get('action', 'N/A')} - {action.get('confidence', 'N/A')}")
                print()
            
            # Risk alerts
            alerts = action_plan.get('risk_alerts', [])
            if alerts:
                print(f"⚠️  RISK ALERTS")
                print("-" * 40)
                for alert in alerts:
                    print(f"• {alert}")
                print()
            
            logger.info("Monday action plan generated successfully")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to generate Monday action plan: {e}")
            return 1
    
    def cmd_insights(self, args) -> int:
        """Generate market insights."""
        try:
            logger.info(f"Generating market insights for {args.timeframe} timeframe")
            
            # Get market data
            if self.price_fetcher:
                symbols = args.symbols or self.config.get('recommendation_engine', {}).get('data_sources', {}).get('symbols', [])
                market_data = self.price_fetcher.get_market_data_for_analysis(symbols)
            else:
                market_data = self._generate_mock_market_data()
            
            # Generate recommendations for insights
            recommendations = self.recommendation_engine.generate_recommendations(market_data)
            
            # Get market insights
            insights = self.recommendation_engine.get_market_insights(recommendations)
            
            # Display insights
            print(f"\n📈 MARKET INSIGHTS - {args.timeframe.upper()} ANALYSIS")
            print(f"{'='*60}")
            print(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Symbols analyzed: {len(market_data)}")
            print()
            
            print(f"Market Regime: {insights.get('market_regime', 'UNKNOWN')}")
            print(f"Volatility Environment: {insights.get('volatility_environment', 'UNKNOWN')}")
            print()
            
            opportunities = insights.get('opportunities', [])
            if opportunities:
                print("🎯 OPPORTUNITIES:")
                for opp in opportunities:
                    print(f"  • {opp}")
                print()
            
            risks = insights.get('key_risks', [])
            if risks:
                print("⚠️  KEY RISKS:")
                for risk in risks:
                    print(f"  • {risk}")
                print()
            
            logger.info("Market insights generated successfully")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to generate market insights: {e}")
            return 1
    
    def cmd_health(self, args) -> int:
        """Check system health."""
        try:
            logger.info("Performing system health check")
            
            health_status = {'overall': True, 'components': {}}
            
            # Check configuration
            try:
                rec_config = self.config.get('recommendation_engine')
                if rec_config:
                    health_status['components']['configuration'] = True
                    if args.detailed:
                        print("✅ Configuration: Loaded successfully")
                else:
                    health_status['components']['configuration'] = False
                    print("❌ Configuration: Recommendation engine config missing")
                    health_status['overall'] = False
            except Exception as e:
                health_status['components']['configuration'] = False
                print(f"❌ Configuration: Error - {e}")
                health_status['overall'] = False
            
            # Check price fetcher (if using live data)
            if self.price_fetcher:
                try:
                    data_health = self.price_fetcher.health_check()
                    health_status['components']['data_sources'] = data_health
                    
                    if args.detailed:
                        print(f"\n📊 Data Sources Health:")
                        for source, status in data_health.items():
                            status_icon = "✅" if status else "❌"
                            print(f"  {status_icon} {source}: {'Working' if status else 'Failed'}")
                    
                    if not any(data_health.values()):
                        health_status['overall'] = False
                        
                except Exception as e:
                    health_status['components']['data_sources'] = False
                    print(f"❌ Data sources: Error - {e}")
                    health_status['overall'] = False
            else:
                health_status['components']['data_sources'] = True
                if args.detailed:
                    print("✅ Data sources: Mock mode (no external dependencies)")
            
            # Check recommendation engine
            try:
                # Simple test of recommendation engine
                test_data = {'SPY': [100.0, 101.0, 102.0] * 20}  # 60 data points
                test_recs = self.recommendation_engine.generate_recommendations(test_data)
                health_status['components']['recommendation_engine'] = True
                if args.detailed:
                    print(f"✅ Recommendation engine: Generated {len(test_recs)} test recommendations")
            except Exception as e:
                health_status['components']['recommendation_engine'] = False
                print(f"❌ Recommendation engine: Error - {e}")
                health_status['overall'] = False
            
            # Overall status
            overall_icon = "✅" if health_status['overall'] else "❌"
            overall_text = "HEALTHY" if health_status['overall'] else "ISSUES DETECTED"
            print(f"\n{overall_icon} Overall system health: {overall_text}")
            
            return 0 if health_status['overall'] else 1
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return 1
    
    def _generate_mock_market_data(self) -> Dict[str, List[float]]:
        """Generate mock market data for testing."""
        import random
        random.seed(42)  # Deterministic for testing
        
        symbols = ['SPY', 'QQQ', 'IWM', 'BTC', 'ETH', 'SOL']
        market_data = {}
        
        for symbol in symbols:
            # Generate 60 days of mock price data
            base_price = random.uniform(50, 500)
            prices = [base_price]
            
            for _ in range(59):
                change = random.uniform(-0.03, 0.03)  # ±3% daily change
                new_price = prices[-1] * (1 + change)
                prices.append(new_price)
            
            market_data[symbol] = prices
        
        return market_data
    
    def _output_recommendations(self, recommendations: List, args):
        """Output recommendations in specified format."""
        if args.output:
            if args.format == 'json':
                self._save_recommendations_json(recommendations, args.output)
            elif args.format == 'csv':
                self._save_recommendations_csv(recommendations, args.output)
            else:  # text
                self._save_recommendations_text(recommendations, args.output)
            
            logger.info(f"Recommendations saved to {args.output}")
        else:
            # Print to console
            self._print_recommendations(recommendations)
    
    def _save_recommendations_json(self, recommendations: List, filename: str):
        """Save recommendations as JSON."""
        import json
        
        data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_recommendations': len(recommendations),
            'recommendations': [rec.to_dict() for rec in recommendations]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save_recommendations_csv(self, recommendations: List, filename: str):
        """Save recommendations as CSV."""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Symbol', 'Action', 'Confidence', 'Price', 'Target', 'Allocation%', 'Reasoning'])
            
            for rec in recommendations:
                writer.writerow([
                    rec.symbol,
                    rec.action.value,
                    f"{rec.confidence:.1%}",
                    f"${rec.current_price:.2f}",
                    f"${rec.target_price:.2f}" if rec.target_price else "N/A",
                    f"{rec.allocation_percentage:.1f}%",
                    rec.reasoning[:100] + "..." if len(rec.reasoning) > 100 else rec.reasoning
                ])
    
    def _save_recommendations_text(self, recommendations: List, filename: str):
        """Save recommendations as readable text."""
        with open(filename, 'w') as f:
            f.write(f"TRADING RECOMMENDATIONS\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total: {len(recommendations)} recommendations\n")
            f.write("=" * 60 + "\n\n")
            
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec.action.value} {rec.symbol}\n")
                f.write(f"   Confidence: {rec.confidence:.1%}\n")
                f.write(f"   Current Price: ${rec.current_price:.2f}\n")
                if rec.target_price:
                    f.write(f"   Target Price: ${rec.target_price:.2f}\n")
                f.write(f"   Position Size: {rec.allocation_percentage:.1f}%\n")
                f.write(f"   Reasoning: {rec.reasoning}\n")
                f.write("\n")
    
    def _print_recommendations(self, recommendations: List):
        """Print recommendations to console."""
        print(f"\n📋 TRADING RECOMMENDATIONS")
        print(f"{'='*60}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total: {len(recommendations)} recommendations\n")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.action.value} {rec.symbol}")
            print(f"   Confidence: {rec.confidence:.1%}")
            print(f"   Current Price: ${rec.current_price:.2f}")
            if rec.target_price:
                print(f"   Target Price: ${rec.target_price:.2f}")
            print(f"   Position Size: {rec.allocation_percentage:.1f}%")
            print(f"   Reasoning: {rec.reasoning}")
            print()
    
    def _load_recommendations(self, filename: str) -> List:
        """Load recommendations from JSON file."""
        import json
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # This would need to reconstruct TradingRecommendation objects
        # For now, return the raw data
        return data.get('recommendations', [])
    
    def _save_json(self, data: Dict, filename: str):
        """Save data as JSON file."""
        import json
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save_action_plan_text(self, action_plan: Dict, filename: str):
        """Save action plan as readable text file."""
        with open(filename, 'w') as f:
            f.write(f"MONDAY TRADING ACTION PLAN\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            # Immediate actions
            immediate = action_plan.get('immediate_actions', [])
            if immediate:
                f.write(f"🚀 IMMEDIATE ACTIONS ({len(immediate)} items)\n")
                f.write("-" * 40 + "\n")
                for i, action in enumerate(immediate, 1):
                    f.write(f"{i}. {action.get('details', 'N/A')}\n")
                    f.write(f"   Reasoning: {action.get('reasoning', 'N/A')}\n")
                    f.write(f"   Confidence: {action.get('confidence', 'N/A')}\n\n")
            
            # Monitor closely
            monitor = action_plan.get('monitor_closely', [])
            if monitor:
                f.write(f"👀 MONITOR CLOSELY ({len(monitor)} items)\n")
                f.write("-" * 40 + "\n")
                for action in monitor:
                    f.write(f"• {action.get('symbol', 'N/A')}: {action.get('action', 'N/A')} - {action.get('confidence', 'N/A')}\n")
                f.write("\n")
            
            # Risk alerts
            alerts = action_plan.get('risk_alerts', [])
            if alerts:
                f.write(f"⚠️  RISK ALERTS\n")
                f.write("-" * 40 + "\n")
                for alert in alerts:
                    f.write(f"• {alert}\n")
                f.write("\n")


def main():
    """Main entry point."""
    cli = RecommendationCLI()
    parser = cli.create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Initialize systems
        cli.initialize_systems(args)
        
        # Route to appropriate command handler
        if args.command == 'generate':
            return cli.cmd_generate(args)
        elif args.command == 'weekend':
            return cli.cmd_weekend(args)
        elif args.command == 'monday':
            return cli.cmd_monday(args)
        elif args.command == 'insights':
            return cli.cmd_insights(args)
        elif args.command == 'health':
            return cli.cmd_health(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 130
    except (ConfigError, DataSourceError) as e:
        logger.error(f"System error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())