# build_watchlist.py

import os, time
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import yfinance as yf
except Exception:
    yf = None

CORE = os.getenv("CORE_LIST_PATH","data/core_25.csv")
OUT  = os.getenv("HYBRID_LIST_PATH","data/hybrid_watchlist.csv")
MAX_WATCHLIST_SIZE = int(os.getenv("MAX_WATCHLIST_SIZE","40"))
PERFORMANCE_LOG = os.getenv("SYMBOL_PERFORMANCE_LOG", "data/symbol_performance.json")

# Lookback & weights (robust parsing)
VOLATILITY_LOOKBACK_DAYS = max(5, int(os.getenv("VOLATILITY_LOOKBACK_DAYS","20")))
def _parse_weights(s: str):
    try:
        w = [float(x) for x in s.split(",")]
        while len(w) < 3: w.append(0.0)
        return w[:3]
    except Exception:
        return [1.0, 1.0, 0.5]
W_ATR, W_HV, W_BETA = _parse_weights(os.getenv("VOL_SCORE_WEIGHTS","1.0,1.0,0.5"))

# Gentle Yahoo pacing
YF_SLEEP = float(os.getenv("YAHOO_MIN_INTERVAL","0.2"))

# Enhanced universe aligned with documented strategy (60+ symbols)
UNIVERSE = [
    # Core ETFs and indices
    "SPY","QQQ","IWM","DIA","VTI","VOO","VEA","VWO",
    
    # Tech giants
    "TSLA","NVDA","AAPL","AMD","MSFT","META","AMZN","GOOGL","NFLX","ADBE",
    
    # Crypto and Bitcoin ETFs
    "BTGD","BITX",
    
    # Leveraged ETFs
    "TQQQ","SQQQ","SOXL","SOXS","LABU","LABD","FNGU","FNGD",
    "UPRO","SPXU","TECL","FAS","FAZ","TNA","TZA","ERX","ERY",
    "TSLL","GOOGL2L","QLD","SSO","UDOW",
    
    # Sector ETFs
    "XLF","XLE","XLC","XLB","XLV","XLK","XLI","XLY","XLP","XLRE","XLU",
    
    # Crypto and growth
    "COIN","MARA","RIOT","PLTR","SNOW","CRWD","SMCI","NIO","BABA",
    
    # ARK funds
    "ARKK","ARKW","ARKG","ARKQ","ARKF",
    
    # Volatility
    "UVXY","VIXY","VXX",
    
    # Commodities
    "GLD","SLV","USO","UNG"
]

# Core symbols (20 symbols - always included)
CORE_SYMBOLS = [
    "SPY","QQQ","IWM","DIA","VTI",  # Major ETFs
    "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA",  # Tech Giants
    "TQQQ","SQQQ","SOXL","SOXS",  # Leveraged ETFs
    "XLF","XLE","XLK","XLV","XLI","XLY"  # Sector ETFs
]

def _load_performance_data() -> Dict[str, Any]:
    """Load performance data for symbol filtering."""
    try:
        if os.path.exists(PERFORMANCE_LOG):
            with open(PERFORMANCE_LOG, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {'symbols': {}}

def _get_poor_performers(performance_data: Dict[str, Any]) -> List[str]:
    """Get list of symbols that should be excluded based on performance."""
    poor_performers = []
    
    for symbol, data in performance_data.get('symbols', {}).items():
        # Check exclusion criteria
        consecutive_losses = data.get('consecutive_losses', 0)
        total_trades = data.get('total_trades', 0)
        profitable_trades = data.get('profitable_trades', 0)
        
        if total_trades >= 5:  # Minimum trades for evaluation
            win_rate = profitable_trades / total_trades
            
            # Exclusion criteria
            if (consecutive_losses >= 8 or 
                (win_rate < 0.45 and total_trades >= 10)):
                poor_performers.append(symbol)
    
    return poor_performers

def _get_high_performers(performance_data: Dict[str, Any]) -> List[str]:
    """Get list of symbols that should be prioritized based on performance."""
    high_performers = []
    
    for symbol, data in performance_data.get('symbols', {}).items():
        total_trades = data.get('total_trades', 0)
        profitable_trades = data.get('profitable_trades', 0)
        total_pnl = data.get('total_pnl', 0)
        
        if total_trades >= 5:  # Minimum trades for evaluation
            win_rate = profitable_trades / total_trades
            avg_return = total_pnl / total_trades
            
            # High performer criteria
            if win_rate >= 0.60 and avg_return >= 0.02:
                high_performers.append(symbol)
    
    return high_performers

def _read_core(path: str):
    try:
        if os.path.exists(path):
            df = pd.read_csv(path)
            col = "symbol" if "symbol" in df.columns else df.columns[0]
            syms = df[col].dropna().astype(str).str.upper().tolist()
            
            # Filter out poor performers from core list
            performance_data = _load_performance_data()
            poor_performers = _get_poor_performers(performance_data)
            
            # Remove poor performers
            filtered_syms = [s for s in syms if s not in poor_performers]
            
            if len(filtered_syms) != len(syms):
                print(f"Removed {len(syms) - len(filtered_syms)} poor performers from core list")
            
            return filtered_syms
    except Exception:
        pass
    return []

def scan_movers(limit=20):
    if yf is None:
        return []
    data=[]
    for sym in UNIVERSE:
        try:
            df = yf.Ticker(sym).history(period="2d", interval="1d", auto_adjust=False)
            if df is None or df.empty or len(df) < 2:
                continue
            prev_close = float(df["Close"].iloc[-2])
            last_close = float(df["Close"].iloc[-1])
            if prev_close <= 0:
                continue
            chg = (last_close - prev_close) / prev_close * 100.0
            data.append((sym, chg))
            time.sleep(YF_SLEEP)
        except Exception:
            # continue silently on symbols with bad data
            pass
    data.sort(key=lambda x: abs(x[1]), reverse=True)
    return [s for s,_ in data[:limit]]

def hv_pct(log_returns: pd.Series) -> float:
    if log_returns is None or len(log_returns) < 5:
        return 0.0
    return float(np.std(log_returns, ddof=1) * np.sqrt(252) * 100.0)

# Pre-fetch SPY once (for beta)
def _spy_returns():
    if yf is None:
        return None
    try:
        spy_close = yf.Ticker("SPY").history(period="6mo", interval="1d", auto_adjust=False)["Close"]
        return spy_close.pct_change().dropna()
    except Exception:
        return None

def calculate_liquidity_score(volume: int, avg_volume_20d: int, price: float) -> float:
    """Calculate liquidity score (40% weight) based on volume metrics."""
    if avg_volume_20d <= 0:
        return 0.0
    
    # Volume trend score
    volume_trend = (volume - avg_volume_20d) / avg_volume_20d
    volume_score = min(50.0, max(0.0, volume_trend * 25 + 25))
    
    # Dollar volume score
    dollar_volume = volume * price
    dollar_score = min(50.0, max(0.0, np.log10(dollar_volume / 1e6) * 20))
    
    return volume_score + dollar_score

def calculate_volatility_score(atr_pct: float, historical_vol: float, recent_vol: float) -> float:
    """Calculate volatility score (30% weight) based on volatility metrics."""
    # ATR percentage score (normalized to 0-50)
    atr_score = min(50.0, max(0.0, atr_pct * 5))
    
    # Historical volatility score (normalized to 0-30)
    hv_score = min(30.0, max(0.0, historical_vol * 0.5))
    
    # Recent volatility vs historical (normalized to 0-20)
    vol_ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
    recent_score = min(20.0, max(0.0, (vol_ratio - 1) * 20))
    
    return atr_score + hv_score + recent_score

def calculate_momentum_score(price_change_1d: float, price_change_5d: float, 
                           rsi: float, macd: float) -> float:
    """Calculate momentum score (20% weight) based on momentum indicators."""
    # Price momentum score (1D and 5D)
    momentum_1d = min(30.0, max(0.0, abs(price_change_1d) * 300))
    momentum_5d = min(40.0, max(0.0, abs(price_change_5d) * 400))
    
    # RSI momentum score (prefer RSI 40-60 for trend continuation)
    rsi_score = 0.0
    if 40 <= rsi <= 60:
        rsi_score = 20.0
    elif 30 <= rsi <= 70:
        rsi_score = 10.0
    
    # MACD momentum score
    macd_score = min(10.0, max(0.0, abs(macd) * 1000))
    
    return momentum_1d + momentum_5d + rsi_score + macd_score

def calculate_spread_score(bid_ask_spread: float, price: float) -> float:
    """Calculate spread quality score (10% weight) - lower spread is better."""
    if price <= 0:
        return 0.0
    
    spread_pct = (bid_ask_spread / price) * 100
    # Score decreases as spread increases (0.1% = 100 points, 1% = 0 points)
    spread_score = max(0.0, 100.0 - spread_pct * 100)
    
    return min(100.0, spread_score)

def calc_unified_score(sym: str, spy_ret_cached: pd.Series | None) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate unified score aligned with documented strategy:
    40% liquidity + 30% volatility + 20% momentum + 10% spread quality
    """
    if yf is None:
        return 0.0, {}
    
    try:
        df = yf.Ticker(sym).history(period="6mo", interval="1d", auto_adjust=False)
        if df is None or df.empty:
            return 0.0, {}
        
        df = df.dropna()
        close = df["Close"]
        high, low = df["High"], df["Low"]
        volume = df["Volume"]
        
        # Calculate components
        last_close = float(close.iloc[-1])
        last_volume = int(volume.iloc[-1])
        avg_volume_20d = int(volume.tail(20).mean())
        
        # ATR calculation
        hl = (high - low)
        atr = hl.rolling(14, min_periods=1).mean()
        atr_pct = float((atr.iloc[-1] / last_close) * 100.0) if last_close > 0 else 0.0
        
        # Historical volatility
        rets_log = np.log(close / close.shift(1)).dropna()
        historical_vol = hv_pct(rets_log.tail(VOLATILITY_LOOKBACK_DAYS))
        recent_vol = hv_pct(rets_log.tail(5))
        
        # Price momentum
        price_change_1d = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)
        price_change_5d = float((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] * 100)
        
        # Technical indicators
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])
        
        # Simple MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        current_macd = float(macd.iloc[-1])
        
        # Spread estimation (using high-low as proxy)
        estimated_spread = float(high.iloc[-1] - low.iloc[-1])
        
        # Calculate component scores
        liquidity_score = calculate_liquidity_score(last_volume, avg_volume_20d, last_close)
        volatility_score = calculate_volatility_score(atr_pct, historical_vol, recent_vol)
        momentum_score = calculate_momentum_score(price_change_1d, price_change_5d, current_rsi, current_macd)
        spread_score = calculate_spread_score(estimated_spread, last_close)
        
        # Combined score with documented weights
        overall_score = (
            liquidity_score * 0.4 +      # 40% liquidity
            volatility_score * 0.3 +    # 30% volatility
            momentum_score * 0.2 +      # 20% momentum
            spread_score * 0.1          # 10% spread quality
        )
        
        return overall_score, {
            "liquidity": liquidity_score,
            "volatility": volatility_score,
            "momentum": momentum_score,
            "spread": spread_score,
            "atr_pct": atr_pct,
            "historical_vol": historical_vol,
            "rsi": current_rsi,
            "macd": current_macd
        }
        
    except Exception:
        return 0.0, {}

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    # Load performance data for enhanced filtering
    performance_data = _load_performance_data()
    poor_performers = _get_poor_performers(performance_data)
    high_performers = _get_high_performers(performance_data)
    
    print(f"Performance data: {len(performance_data.get('symbols', {}))} symbols tracked")
    print(f"Poor performers to exclude: {len(poor_performers)} symbols")
    print(f"High performers to prioritize: {len(high_performers)} symbols")

    core = _read_core(CORE)
    
    # Add high performers to core list if not already present
    for symbol in high_performers:
        if symbol not in core:
            core.append(symbol)
            print(f"Added high performer to core: {symbol}")
    
    # If yfinance not available, just write the core list (capped) and exit
    if yf is None:
        core = core[:MAX_WATCHLIST_SIZE]
        pd.DataFrame({"symbol": core}).to_csv(OUT, index=False)
        print(f"[NO-YF] Wrote {OUT} with {len(core)} core symbols at {datetime.utcnow().isoformat()}Z")
        return

    # Implement documented distribution: 20 core + 20 volume movers + 10 volatility
    print(f"\nImplementing documented symbol distribution:")
    print(f"  Core symbols: {len(core)} (always included)")
    
    # Get volume movers (top 20 by volume from extended universe)
    movers = scan_movers(limit=30)
    filtered_movers = [s for s in movers if s not in poor_performers and s not in core]
    volume_movers = filtered_movers[:20]  # Top 20 volume movers
    print(f"  Volume movers: {len(volume_movers)} (highest volume)")
    
    # Get volatility opportunities (remaining symbols, top 10 by volatility)
    remaining_universe = [s for s in UNIVERSE if s not in core and s not in volume_movers and s not in poor_performers]
    volatility_candidates = remaining_universe[:15]  # Scan top 15 for volatility
    print(f"  Volatility candidates: {len(volatility_candidates)} (scanning for best volatility)")
    
    # Combine all candidates
    all_candidates = core + volume_movers + volatility_candidates
    print(f"  Total candidates to score: {len(all_candidates)}")

    # Prefetch SPY returns once for beta calc
    spy_ret = _spy_returns()

    # Score all candidates using unified scoring system
    scored = []
    for s in all_candidates:
        sc, parts = calc_unified_score(s, spy_ret)
        
        # Apply performance boost/penalty
        performance_boost = 0
        if s in high_performers:
            performance_boost = 20  # Boost high performers
        elif s in poor_performers:
            performance_boost = -20  # Penalize poor performers
        
        final_score = sc + performance_boost
        scored.append((s, final_score, parts, performance_boost))
        time.sleep(YF_SLEEP)

    # Sort by unified score
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Select final watchlist maintaining distribution
    final_watchlist = []
    
    # Ensure core symbols are included (first 20)
    core_scored = [(s, sc, parts, boost) for s, sc, parts, boost in scored if s in core]
    final_watchlist.extend([s for s, _, _, _ in core_scored[:20]])
    
    # Add best volume movers (next 20)
    volume_scored = [(s, sc, parts, boost) for s, sc, parts, boost in scored if s in volume_movers]
    final_watchlist.extend([s for s, _, _, _ in volume_scored[:20]])
    
    # Add best volatility opportunities (final 10)
    volatility_scored = [(s, sc, parts, boost) for s, sc, parts, boost in scored if s in volatility_candidates]
    final_watchlist.extend([s for s, _, _, _ in volatility_scored[:10]])
    
    # Remove duplicates and limit to MAX_WATCHLIST_SIZE
    seen = set()
    unique_watchlist = []
    for s in final_watchlist:
        if s not in seen:
            unique_watchlist.append(s)
            seen.add(s)
    
    final_watchlist = unique_watchlist[:MAX_WATCHLIST_SIZE]

    # Log results with detailed scoring breakdown
    print(f"\nFinal watchlist composition:")
    print(f"  Core symbols: {len([s for s in final_watchlist if s in core])}")
    print(f"  Volume movers: {len([s for s in final_watchlist if s in volume_movers])}")
    print(f"  Volatility opportunities: {len([s for s in final_watchlist if s in volatility_candidates])}")
    
    print(f"\nTop 10 symbols with unified scoring:")
    for i, (symbol, score, parts, boost) in enumerate(scored[:10]):
        if symbol in final_watchlist:
            liquidity = parts.get('liquidity', 0)
            volatility = parts.get('volatility', 0)
            momentum = parts.get('momentum', 0)
            spread = parts.get('spread', 0)
            print(f"{i+1:2d}. {symbol:6s} Score: {score:6.1f} (Liq: {liquidity:5.1f}, Vol: {volatility:5.1f}, Mom: {momentum:5.1f}, Spr: {spread:5.1f})")

    pd.DataFrame({"symbol": final_watchlist}).to_csv(OUT, index=False)
    print(f"\nWrote {OUT} with {len(final_watchlist)} symbols using unified scoring (40% liquidity + 30% volatility + 20% momentum + 10% spread) at {datetime.utcnow().isoformat()}Z")

if __name__ == "__main__":
    main()
