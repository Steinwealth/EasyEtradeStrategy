#!/usr/bin/env python3
"""
Prime Rank Review Tool
=====================

This script allows you to review prime scores and rankings after market hours.
It reads the symbol_scores.json file and displays current rankings.

Usage:
    python3 review_prime_ranks.py
    python3 review_prime_ranks.py --export-csv
    python3 review_prime_ranks.py --symbol TQQQ
    python3 review_prime_ranks.py --top 10
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
import csv

class PrimeRankReviewer:
    def __init__(self, data_file="symbol_scores.json"):
        self.data_file = Path(data_file)
        self.symbol_data = self._load_data()
    
    def _load_data(self):
        """Load symbol score data from file"""
        if not self.data_file.exists():
            print(f"❌ Data file not found: {self.data_file}")
            print("   The system needs to run for a while to generate data.")
            return {}
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return {}
    
    def get_symbol_rankings(self, min_trades=5):
        """Get symbol rankings sorted by average prime score"""
        if not self.symbol_data.get('symbol_ranks'):
            return []
        
        # Filter symbols with minimum trades
        qualified_symbols = []
        for symbol, rank_data in self.symbol_data['symbol_ranks'].items():
            if rank_data.get('total_trades', 0) >= min_trades:
                qualified_symbols.append((symbol, rank_data))
        
        # Sort by average prime score (descending)
        sorted_symbols = sorted(
            qualified_symbols,
            key=lambda x: x[1].get('avg_prime_score', 0),
            reverse=True
        )
        
        return sorted_symbols
    
    def display_rankings(self, top_n=None, min_trades=5):
        """Display symbol rankings"""
        rankings = self.get_symbol_rankings(min_trades)
        
        if not rankings:
            print("📊 No symbol data available yet.")
            print("   The system needs to complete some trades to generate rankings.")
            return
        
        print(f"\n🏆 Prime Symbol Rankings (Last 200 Trades Average)")
        print("=" * 80)
        print(f"{'Rank':<4} {'Symbol':<8} {'Avg Prime Score':<15} {'Trades':<8} {'Win Rate':<10} {'Total Profit':<12}")
        print("-" * 80)
        
        for rank, (symbol, data) in enumerate(rankings[:top_n] if top_n else rankings, 1):
            avg_score = data.get('avg_prime_score', 0)
            total_trades = data.get('total_trades', 0)
            win_rate = data.get('win_rate', 0)
            total_profit = data.get('total_profit', 0)
            
            print(f"{rank:<4} {symbol:<8} {avg_score:<15.2f} {total_trades:<8} {win_rate:<10.1f}% ${total_profit:<11.2f}")
    
    def get_symbol_details(self, symbol):
        """Get detailed information for a specific symbol"""
        if not self.symbol_data.get('symbol_ranks', {}).get(symbol):
            print(f"❌ No data found for symbol: {symbol}")
            return
        
        rank_data = self.symbol_data['symbol_ranks'][symbol]
        trades_data = self.symbol_data.get('symbol_trades', {}).get(symbol, [])
        
        print(f"\n📈 Detailed Analysis for {symbol}")
        print("=" * 50)
        print(f"Average Prime Score: {rank_data.get('avg_prime_score', 0):.2f}")
        print(f"Total Trades: {rank_data.get('total_trades', 0)}")
        print(f"Profitable Trades: {rank_data.get('profitable_trades', 0)}")
        print(f"Win Rate: {rank_data.get('win_rate', 0):.1f}%")
        print(f"Total Profit: ${rank_data.get('total_profit', 0):.2f}")
        print(f"Average Trade Size: ${rank_data.get('avg_trade_size', 0):.2f}")
        print(f"Last Updated: {rank_data.get('last_updated', 'Unknown')}")
        
        if trades_data:
            print(f"\nRecent Prime Scores: {rank_data.get('recent_prime_scores', [])}")
            
            # Show last 5 trades
            print(f"\nLast 5 Trades:")
            print(f"{'Date':<12} {'Size':<10} {'P&L':<10} {'Prime Score':<12}")
            print("-" * 50)
            for trade in trades_data[-5:]:
                timestamp = trade.get('timestamp', 'Unknown')[:10]  # Just date
                size = trade.get('trade_size', 0)
                pnl = trade.get('profit_loss', 0)
                score = trade.get('prime_score', 0)
                print(f"{timestamp:<12} ${size:<9.2f} ${pnl:<9.2f} {score:<12.2f}")
    
    def export_csv(self, filename=None):
        """Export rankings to CSV file"""
        rankings = self.get_symbol_rankings()
        
        if not rankings:
            print("❌ No data to export")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prime_rankings_{timestamp}.csv"
        
        filepath = Path(filename)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Rank', 'Symbol', 'Avg_Prime_Score', 'Total_Trades', 
                'Win_Rate', 'Total_Profit', 'Avg_Trade_Size', 'Last_Updated'
            ])
            
            for rank, (symbol, data) in enumerate(rankings, 1):
                writer.writerow([
                    rank,
                    symbol,
                    data.get('avg_prime_score', 0),
                    data.get('total_trades', 0),
                    data.get('win_rate', 0),
                    data.get('total_profit', 0),
                    data.get('avg_trade_size', 0),
                    data.get('last_updated', 'Unknown')
                ])
        
        print(f"✅ Rankings exported to: {filepath}")
    
    def get_system_stats(self):
        """Get overall system statistics"""
        if not self.symbol_data:
            print("❌ No system data available")
            return
        
        total_symbols = len(self.symbol_data.get('symbol_ranks', {}))
        total_trades = sum(
            data.get('total_trades', 0) 
            for data in self.symbol_data.get('symbol_ranks', {}).values()
        )
        
        print(f"\n📊 System Statistics")
        print("=" * 30)
        print(f"Total Symbols Tracked: {total_symbols}")
        print(f"Total Trades Recorded: {total_trades}")
        print(f"Data File: {self.data_file}")
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    parser = argparse.ArgumentParser(description='Review Prime Symbol Rankings')
    parser.add_argument('--top', type=int, help='Show top N symbols')
    parser.add_argument('--symbol', help='Show details for specific symbol')
    parser.add_argument('--export-csv', action='store_true', help='Export to CSV file')
    parser.add_argument('--min-trades', type=int, default=5, help='Minimum trades required')
    
    args = parser.parse_args()
    
    reviewer = PrimeRankReviewer()
    
    if args.symbol:
        reviewer.get_symbol_details(args.symbol.upper())
    elif args.export_csv:
        reviewer.export_csv()
    else:
        reviewer.display_rankings(top_n=args.top, min_trades=args.min_trades)
        reviewer.get_system_stats()

if __name__ == "__main__":
    main()
