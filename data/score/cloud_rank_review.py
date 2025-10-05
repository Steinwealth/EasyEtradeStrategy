#!/usr/bin/env python3
"""
Cloud Prime Rank Review Tool
============================

This script downloads and reviews prime scores from Google Cloud Storage.
Use this when the system is running in the cloud and you want to review
rankings from your local machine.

Prerequisites:
    pip install google-cloud-storage

Usage:
    python3 cloud_rank_review.py
    python3 cloud_rank_review.py --download
    python3 cloud_rank_review.py --bucket your-bucket-name
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
import os

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    print("⚠️  Google Cloud Storage not available. Install with: pip install google-cloud-storage")

class CloudPrimeRankReviewer:
    def __init__(self, bucket_name=None, project_id=None):
        self.bucket_name = bucket_name or os.getenv('GCS_BUCKET_NAME', 'etrade-strategy-data')
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.client = None
        
        if GCS_AVAILABLE:
            try:
                self.client = storage.Client(project=self.project_id)
            except Exception as e:
                print(f"❌ Error initializing GCS client: {e}")
    
    def download_data(self, local_file="symbol_scores.json"):
        """Download symbol scores from Google Cloud Storage"""
        if not self.client:
            print("❌ Google Cloud Storage client not available")
            return False
        
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob('data/symbol_scores.json')
            
            # Create local directory if it doesn't exist
            Path(local_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Download the file
            blob.download_to_filename(local_file)
            print(f"✅ Downloaded data from gs://{self.bucket_name}/data/symbol_scores.json")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading data: {e}")
            return False
    
    def list_available_files(self):
        """List available files in the cloud bucket"""
        if not self.client:
            print("❌ Google Cloud Storage client not available")
            return
        
        try:
            bucket = self.client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix='data/')
            
            print(f"\n📁 Available files in gs://{self.bucket_name}/data/:")
            print("-" * 50)
            
            for blob in blobs:
                size = blob.size if blob.size else 0
                updated = blob.updated.strftime('%Y-%m-%d %H:%M:%S') if blob.updated else 'Unknown'
                print(f"{blob.name:<40} {size:>8} bytes  {updated}")
                
        except Exception as e:
            print(f"❌ Error listing files: {e}")
    
    def review_rankings(self, local_file="symbol_scores.json"):
        """Review rankings from downloaded data"""
        if not Path(local_file).exists():
            print(f"❌ Local file not found: {local_file}")
            print("   Try running with --download first")
            return
        
        try:
            with open(local_file, 'r') as f:
                data = json.load(f)
            
            symbol_ranks = data.get('symbol_ranks', {})
            if not symbol_ranks:
                print("📊 No symbol rankings available yet")
                return
            
            # Sort by average prime score
            sorted_symbols = sorted(
                symbol_ranks.items(),
                key=lambda x: x[1].get('avg_prime_score', 0),
                reverse=True
            )
            
            print(f"\n🏆 Prime Symbol Rankings (Cloud Data)")
            print("=" * 80)
            print(f"{'Rank':<4} {'Symbol':<8} {'Avg Prime Score':<15} {'Trades':<8} {'Win Rate':<10} {'Total Profit':<12}")
            print("-" * 80)
            
            for rank, (symbol, data) in enumerate(sorted_symbols, 1):
                avg_score = data.get('avg_prime_score', 0)
                total_trades = data.get('total_trades', 0)
                win_rate = data.get('win_rate', 0)
                total_profit = data.get('total_profit', 0)
                
                print(f"{rank:<4} {symbol:<8} {avg_score:<15.2f} {total_trades:<8} {win_rate:<10.1f}% ${total_profit:<11.2f}")
            
            print(f"\n📊 Summary:")
            print(f"Total Symbols: {len(sorted_symbols)}")
            print(f"Total Trades: {sum(data.get('total_trades', 0) for _, data in sorted_symbols)}")
            print(f"Data Updated: {data.get('last_updated', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error reading data: {e}")

def main():
    parser = argparse.ArgumentParser(description='Review Prime Rankings from Cloud')
    parser.add_argument('--download', action='store_true', help='Download data from cloud first')
    parser.add_argument('--bucket', help='GCS bucket name')
    parser.add_argument('--project', help='Google Cloud project ID')
    parser.add_argument('--list', action='store_true', help='List available files in bucket')
    
    args = parser.parse_args()
    
    if not GCS_AVAILABLE:
        print("❌ Google Cloud Storage not available")
        print("   Install with: pip install google-cloud-storage")
        return
    
    reviewer = CloudPrimeRankReviewer(
        bucket_name=args.bucket,
        project_id=args.project
    )
    
    if args.list:
        reviewer.list_available_files()
    elif args.download:
        if reviewer.download_data():
            reviewer.review_rankings()
    else:
        reviewer.review_rankings()

if __name__ == "__main__":
    main()
