#!/usr/bin/env python3
"""
Prime Symbol Score System - Example Usage

This script demonstrates how to use the Prime Symbol Score system
to track and analyze symbol performance for trading decisions.

Author: Easy ETrade Strategy Team
Version: 2.0
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the modules directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

from prime_symbol_score import PrimeSymbolScore
from symbol_score_integration import SymbolScoreIntegration


def simulate_trading_session(symbol_score_integration, num_trades=50):
    """
    Simulate a trading session with random trades
    
    Args:
        symbol_score_integration: SymbolScoreIntegration instance
        num_trades: Number of trades to simulate
    """
    print(f"Simulating {num_trades} trades...")
    
    # Define symbols and their characteristics
    symbols = {
        "TQQQ": {"base_return": 0.15, "volatility": 0.05},  # High volatility, high return
        "SPY": {"base_return": 0.08, "volatility": 0.02},   # Low volatility, medium return
        "QQQ": {"base_return": 0.12, "volatility": 0.03},   # Medium volatility, high return
        "IWM": {"base_return": 0.10, "volatility": 0.04},   # Medium volatility, medium return
        "XLF": {"base_return": 0.06, "volatility": 0.03},   # Low volatility, low return
        "XLK": {"base_return": 0.14, "volatility": 0.04},   # High volatility, high return
    }
    
    strategy_modes = ["standard", "advanced", "quantum"]
    
    for i in range(num_trades):
        # Randomly select symbol
        symbol = random.choice(list(symbols.keys()))
        symbol_data = symbols[symbol]
        
        # Generate trade size (between $500 and $2000)
        trade_size = random.uniform(500, 2000)
        
        # Generate profit/loss based on symbol characteristics
        base_return = symbol_data["base_return"]
        volatility = symbol_data["volatility"]
        
        # Add some randomness
        random_factor = random.gauss(0, volatility)
        return_rate = base_return + random_factor
        
        # Calculate profit/loss
        profit_loss = trade_size * return_rate
        
        # Generate trade ID
        trade_id = f"{symbol}_{i+1:03d}"
        
        # Select random strategy mode
        strategy_mode = random.choice(strategy_modes)
        
        # Generate confidence (higher for better performing symbols)
        confidence = min(0.99, 0.7 + (base_return * 2) + random.uniform(-0.1, 0.1))
        
        # Add trade result
        rank_score = symbol_score_integration.on_trade_closed(
            symbol=symbol,
            trade_size=trade_size,
            profit_loss=profit_loss,
            trade_id=trade_id,
            strategy_mode=strategy_mode,
            confidence=confidence
        )
        
        # Print trade result
        print(f"Trade {i+1:2d}: {symbol} | ${profit_loss:7.2f} on ${trade_size:6.0f} | "
              f"Rank: {rank_score:6.2f} | {strategy_mode:8s} | {confidence:.2f}")


def analyze_performance(symbol_score_integration):
    """Analyze and display performance metrics"""
    print("\n" + "="*80)
    print("PERFORMANCE ANALYSIS")
    print("="*80)
    
    # Get daily report
    report = symbol_score_integration.generate_daily_report()
    print(report)
    
    # Get detailed analysis for each symbol
    print("\nDetailed Symbol Analysis:")
    print("-" * 80)
    
    symbols = ["TQQQ", "SPY", "QQQ", "IWM", "XLF", "XLK"]
    for symbol in symbols:
        analysis = symbol_score_integration.get_symbol_analysis(symbol)
        if "error" not in analysis:
            print(f"\n{symbol}:")
            print(f"  Performance Rating: {analysis['performance_rating']}")
            print(f"  Recommendation: {analysis['recommendation']}")
            print(f"  Rank Score: {analysis['rank_score']:.2f} per $100")
            print(f"  Win Rate: {analysis['win_rate']:.1f}%")
            print(f"  Total Trades: {analysis['total_trades']}")
            print(f"  Total Profit: ${analysis['total_profit']:.2f}")
            print(f"  Volatility: {analysis['volatility']:.2f}")


def demonstrate_priority_system(symbol_score_integration):
    """Demonstrate the priority system for trade allocation"""
    print("\n" + "="*80)
    print("PRIORITY SYSTEM DEMONSTRATION")
    print("="*80)
    
    # Get priority weights for all symbols
    candidate_symbols = ["TQQQ", "SPY", "QQQ", "IWM", "XLF", "XLK"]
    weights = symbol_score_integration.get_symbol_priority_weights(
        symbols=candidate_symbols,
        min_trades=3
    )
    
    print("Priority Weights (for position sizing):")
    print("-" * 50)
    for symbol, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"{symbol:6s}: {weight:.2f}x")
    
    # Get top priority symbols
    top_symbols = symbol_score_integration.get_top_priority_symbols(
        candidate_symbols=candidate_symbols,
        top_n=3,
        min_trades=3
    )
    
    print(f"\nTop 3 Priority Symbols: {', '.join(top_symbols)}")
    
    # Demonstrate position size recommendations
    print("\nPosition Size Recommendations (Base: $1000):")
    print("-" * 50)
    for symbol in candidate_symbols:
        base_size = 1000.0
        recommended_size = symbol_score_integration.should_increase_position_size(
            symbol=symbol,
            base_size=base_size
        )
        multiplier = recommended_size / base_size
        print(f"{symbol:6s}: ${recommended_size:7.0f} ({multiplier:.2f}x)")


def demonstrate_confidence_boosting(symbol_score_integration):
    """Demonstrate confidence boosting based on historical performance"""
    print("\n" + "="*80)
    print("CONFIDENCE BOOSTING DEMONSTRATION")
    print("="*80)
    
    symbols = ["TQQQ", "SPY", "QQQ", "IWM", "XLF", "XLK"]
    
    print("Confidence Boosts (based on historical performance):")
    print("-" * 60)
    for symbol in symbols:
        boost = symbol_score_integration.get_symbol_confidence_boost(symbol)
        print(f"{symbol:6s}: {boost:.2f}x boost")
    
    print("\nExample: If a signal has 0.90 confidence for TQQQ:")
    tqqq_boost = symbol_score_integration.get_symbol_confidence_boost("TQQQ")
    boosted_confidence = 0.90 * tqqq_boost
    print(f"  Boosted confidence: {0.90:.2f} × {tqqq_boost:.2f} = {boosted_confidence:.2f}")


def export_data(symbol_score):
    """Export data to CSV for analysis"""
    print("\n" + "="*80)
    print("DATA EXPORT")
    print("="*80)
    
    # Export priority list
    filename = symbol_score.export_priority_list()
    print(f"Priority list exported to: {filename}")
    
    # Get system stats
    stats = symbol_score.get_system_stats()
    print(f"\nSystem Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def main():
    """Main function to run the example"""
    print("Prime Symbol Score System - Example Usage")
    print("=" * 50)
    
    # Initialize the symbol score system
    symbol_score = PrimeSymbolScore(
        max_trades_per_symbol=100,
        data_file="data/example_symbol_scores.json"
    )
    
    # Initialize integration
    symbol_score_integration = SymbolScoreIntegration(symbol_score)
    
    # Simulate trading session
    simulate_trading_session(symbol_score_integration, num_trades=30)
    
    # Analyze performance
    analyze_performance(symbol_score_integration)
    
    # Demonstrate priority system
    demonstrate_priority_system(symbol_score_integration)
    
    # Demonstrate confidence boosting
    demonstrate_confidence_boosting(symbol_score_integration)
    
    # Export data
    export_data(symbol_score)
    
    print("\n" + "="*80)
    print("EXAMPLE COMPLETED")
    print("="*80)
    print("The Prime Symbol Score system is now ready for integration")
    print("with your trading system. Use the integration methods to:")
    print("1. Track trade results as they close")
    print("2. Get priority weights for position sizing")
    print("3. Boost confidence based on historical performance")
    print("4. Generate daily reports for analysis")


if __name__ == "__main__":
    main()
