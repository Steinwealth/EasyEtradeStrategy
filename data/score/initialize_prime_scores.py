#!/usr/bin/env python3
"""
Initialize Prime Symbol Score System

This script initializes the Prime Symbol Score system and creates
the initial data files that will be populated as trades are made.

Author: Easy ETrade Strategy Team
Version: 2.0
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the modules directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

try:
    from prime_symbol_score import PrimeSymbolScore
    print("✅ Prime Symbol Score module imported successfully")
except ImportError as e:
    print(f"❌ Error importing Prime Symbol Score module: {e}")
    print("   Make sure you're running this from the V2 Cursor Etrade Strategy directory")
    sys.exit(1)

def initialize_prime_score_system():
    """Initialize the Prime Symbol Score system"""
    print("🚀 Initializing Prime Symbol Score System...")
    
    # Create data directory if it doesn't exist
    data_dir = Path(".")
    data_dir.mkdir(exist_ok=True)
    print(f"📁 Data directory: {data_dir.absolute()}")
    
    # Initialize the Prime Symbol Score system
    try:
        symbol_score = PrimeSymbolScore(
            max_trades_per_symbol=300,
            data_file="symbol_scores.json",
            backup_interval=100
        )
        print("✅ Prime Symbol Score system initialized")
        
        # Test the system with a sample trade
        print("\n🧪 Testing system with sample trade...")
        
        # Add a sample trade to verify everything works
        sample_trade = symbol_score.add_trade_result(
            symbol="TEST",
            trade_size=1000.0,
            profit_loss=50.0,
            trade_id="TEST_001",
            strategy_mode="test",
            confidence=0.95
        )
        
        if sample_trade:
            print(f"✅ Sample trade added successfully")
            print(f"   Symbol: TEST")
            print(f"   Trade Size: $1,000.00")
            print(f"   Profit: $50.00")
            print(f"   Prime Score: {sample_trade.prime_score}")
            
            # Get the priority list
            priority_list = symbol_score.get_daily_priority_list()
            print(f"\n📊 Priority List:")
            for i, rank in enumerate(priority_list, 1):
                print(f"   {i}. {rank.symbol}: {rank.avg_prime_score} (avg prime score)")
            
            # Get system stats
            stats = symbol_score.get_system_stats()
            print(f"\n📈 System Stats:")
            print(f"   Total Trades: {stats['total_trades']}")
            print(f"   Total Symbols: {stats['total_symbols']}")
            print(f"   Last Updated: {stats['last_updated']}")
            
        else:
            print("❌ Failed to add sample trade")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing Prime Symbol Score system: {e}")
        return False
    
    print(f"\n🎉 Prime Symbol Score System initialized successfully!")
    print(f"📁 Data files created:")
    print(f"   - symbol_scores.json")
    print(f"   - symbol_scores_backup.json")
    print(f"\n💡 The system is ready to record trades and calculate prime scores!")
    print(f"   As trades close, they will be automatically recorded and ranked.")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 PRIME SYMBOL SCORE SYSTEM INITIALIZATION")
    print("=" * 60)
    
    success = initialize_prime_score_system()
    
    if success:
        print("\n✅ Initialization completed successfully!")
        print("🚀 The system is ready for trading!")
    else:
        print("\n❌ Initialization failed!")
        print("   Please check the error messages above.")
        sys.exit(1)
