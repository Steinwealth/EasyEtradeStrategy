# Prime Score Review Tools

This directory contains tools for reviewing prime scores and rankings after market hours.

## 📁 Files

- **`review_prime_ranks.py`** - Local review tool for prime rankings
- **`cloud_rank_review.py`** - Cloud data access and review tool
- **`prime_rank_dashboard.py`** - Web dashboard for viewing rankings

## 🚀 Usage

### Local Review (Recommended)

```bash
# Navigate to the score directory
cd data/score

# Review all rankings
python3 review_prime_ranks.py

# Show top 10 symbols
python3 review_prime_ranks.py --top 10

# Get details for specific symbol
python3 review_prime_ranks.py --symbol TQQQ

# Export to CSV for analysis
python3 review_prime_ranks.py --export-csv

# Show symbols with minimum 5 trades
python3 review_prime_ranks.py --min-trades 5
```

### Cloud Data Access

```bash
# Navigate to the score directory
cd data/score

# Download data from Google Cloud Storage
python3 cloud_rank_review.py --download

# List available files in cloud bucket
python3 cloud_rank_review.py --list

# Review rankings from cloud data
python3 cloud_rank_review.py

# Specify custom bucket
python3 cloud_rank_review.py --bucket your-bucket-name --download
```

### Web Dashboard

```bash
# Navigate to the score directory
cd data/score

# Start web dashboard
python3 prime_rank_dashboard.py

# Access in browser: http://localhost:8080
# Auto-refreshes every 30 seconds

# Run on different port
python3 prime_rank_dashboard.py --port 8081

# Run on all interfaces
python3 prime_rank_dashboard.py --host 0.0.0.0
```

## 📊 Data Source

All tools read from `../symbol_scores.json` which is automatically created and updated by the trading system.

## 🔧 Prerequisites

### For Local Review
- No additional packages required
- Uses built-in Python libraries

### For Cloud Access
```bash
pip install google-cloud-storage
```

### For Web Dashboard
- No additional packages required
- Uses built-in Python libraries

## 📈 Understanding Prime Scores

- **Prime Score Formula**: `(Profit × 100) ÷ Trade Size`
- **Represents**: Profit per $100 invested
- **200-Trade Rolling Average**: Only last 200 trades per symbol
- **Ranking**: Symbols ranked by average prime score (highest to lowest)

## 🎯 Example Output

```
🏆 Prime Symbol Rankings (Last 200 Trades Average)
================================================================================
Rank Symbol   Avg Prime Score  Trades   Win Rate   Total Profit
--------------------------------------------------------------------------------
1    TQQQ     12.45           15       86.7%      $1,245.30
2    QQQ      8.32            12       83.3%      $998.40
3    SPY      5.67            18       77.8%      $1,020.60
4    NVDA     4.23            8        75.0%      $338.40
5    AAPL     3.89            14       78.6%      $544.60
```

## 🔄 Data Updates

The trading system automatically updates prime scores when trades close:
1. Trade closes with profit/loss
2. Prime score calculated
3. Added to symbol's trade history
4. 200-trade rolling average updated
5. Rankings recalculated
6. Data saved to `../symbol_scores.json`

## 📝 Notes

- Data is automatically recorded during trading hours
- No manual intervention required
- Rankings update in real-time after each trade closure
- All tools work with the same data source
- Data persists across system restarts
