# services/alert_only_service.py
"""
Alert-Only Service for ETrade Strategy
Provides signal generation and alerts without actual trading execution
Perfect for monitoring and testing strategies safely
"""

from __future__ import annotations
import os
import time
import threading
import signal
import logging
import datetime as dt
from typing import Dict, List, Optional, Any

from modules import http_server
from modules import state_backend as state
from modules.config_loader import get_config_value, load_configuration
from modules.market_clock_ext import MarketClock
from modules.prime_data_manager import get_prime_data_manager
from modules.prime_data_manager import get_prime_data_manager
from modules.prime_data_manager import get_prime_data_manager
from modules.production_signal_generator import get_enhanced_production_signal_generator
from modules.alerting import AlertManager
from modules.performance_monitor import PerformanceMonitor

log = logging.getLogger("alert_only_service")

class AlertOnlyService:
    """Alert-only service for safe strategy monitoring"""
    
    def __init__(self):
        self.session_id = f"EES-ALERT-{int(time.time())}"
        self.start_time = dt.datetime.utcnow()
        self.running = threading.Event()
        self.running.set()
        
        # Load configuration
        self.strategy_mode = get_config_value("STRATEGY_MODE", "standard")
        self.automation_mode = "off"  # Always off for alert-only
        self.environment = get_config_value("ENVIRONMENT", "development")
        
        # Initialize components
        self.clock = MarketClock()
        self.performance_monitor = PerformanceMonitor()
        self.alert_manager = AlertManager()
        self.strategy_engine = StrategyEngine(self.strategy_mode)
        
        # Data providers
        self.primary_provider = PolygonProvider()
        self.fallback_provider = YFProvider()
        self.data_mux = DataMux(self.primary_provider, self.fallback_provider)
        
        # Session state
        self.signals_generated = 0
        self.alerts_sent = 0
        self.errors_count = 0
        
        # Initialize state backend
        state.init(self.session_id)
        
        log.info(f"Alert-Only Service initialized - Strategy: {self.strategy_mode}")
    
    def start(self):
        """Start the alert-only service"""
        log.info("Starting Alert-Only Service...")
        
        # Start HTTP server
        http_server.serve_async()
        
        # Load watchlist
        watchlist = self._load_watchlist()
        log.info(f"Loaded watchlist: {len(watchlist)} symbols")
        
        # Setup signal handlers
        def handle_sigterm(*_): 
            log.info("Received SIGTERM, shutting down gracefully...")
            self.running.clear()
        
        signal.signal(signal.SIGTERM, handle_sigterm)
        
        # Main monitoring loop
        self._main_monitoring_loop(watchlist)
    
    def _load_watchlist(self) -> List[str]:
        """Load trading watchlist from CSV file"""
        import csv
        watchlist_file = get_config_value("WATCHLIST_FILE", "data/hybrid_watchlist.csv")
        syms = []
        
        try:
            with open(watchlist_file) as f:
                for row in csv.reader(f):
                    if row and row[0].strip() and row[0].upper() != "SYMBOL":
                        syms.append(row[0].strip().upper())
        except Exception as e:
            log.warning(f"Failed to load watchlist: {e}")
            # Fallback to core symbols
            syms = ["SPY", "QQQ", "IWM", "TQQQ", "SQQQ", "SOXL", "SOXS"]
        
        max_symbols = get_config_value("MAX_WATCHLIST_SIZE", 50)
        return syms[:max_symbols]
    
    def _main_monitoring_loop(self, watchlist: List[str]):
        """Main monitoring loop for alert-only service"""
        log.info("Starting main monitoring loop...")
        
        while self.running.is_set():
            try:
                # Check market hours
                if not self.clock.is_open():
                    time.sleep(60)  # Check every minute when market is closed
                    continue
                
                # Process watchlist for signals
                self._process_watchlist_for_signals(watchlist)
                
                # Send periodic status alerts
                self._send_status_alert()
                
                # Sleep based on strategy mode
                sleep_time = self._get_sleep_time()
                time.sleep(sleep_time)
                
            except Exception as e:
                log.exception(f"Error in monitoring loop: {e}")
                self.errors_count += 1
                time.sleep(30)  # Wait longer on errors
        
        log.info("Monitoring loop stopped")
    
    def _process_watchlist_for_signals(self, watchlist: List[str]):
        """Process watchlist for signal generation and alerts"""
        now = dt.datetime.utcnow()
        
        for symbol in watchlist:
            try:
                # Get latest bar data
                bar_data = self._get_latest_bar(symbol, now)
                if not bar_data:
                    continue
                
                # Create market bar
                bar = self._create_market_bar(symbol, bar_data)
                
                # Get historical data for indicators
                historical_data = self._get_historical_data(symbol, 100)
                
                # Calculate technical indicators
                indicators = self._calculate_indicators(historical_data)
                
                # Generate signals using strategy engine
                signals = self.strategy_engine.generate_signals(bar, indicators)
                
                # Process signals (send alerts only)
                for signal in signals:
                    self._process_signal_alert(signal, bar)
                
            except Exception as e:
                log.error(f"Error processing symbol {symbol}: {e}")
                self.errors_count += 1
                continue
    
    def _get_latest_bar(self, symbol: str, now: dt.datetime) -> Optional[Dict]:
        """Get latest bar data for symbol"""
        try:
            # Try primary provider first
            bar_data = self.primary_provider.agg_minute(
                symbol, 
                now - dt.timedelta(minutes=2), 
                now, 
                limit=1
            )
            
            if bar_data:
                return bar_data[0]
            
            # Fallback to secondary provider
            bar_data = self.fallback_provider.agg_minute(
                symbol,
                now - dt.timedelta(minutes=2),
                now,
                limit=1
            )
            
            return bar_data[0] if bar_data else None
            
        except Exception as e:
            log.error(f"Error getting bar data for {symbol}: {e}")
            return None
    
    def _create_market_bar(self, symbol: str, bar_data: Dict) -> Any:
        """Create market bar object"""
        # Simple bar object
        class MarketBar:
            def __init__(self, symbol, timestamp, open, high, low, close, volume):
                self.symbol = symbol
                self.timestamp = timestamp
                self.open = open
                self.high = high
                self.low = low
                self.close = close
                self.volume = volume
        
        return MarketBar(
            symbol=symbol,
            timestamp=bar_data.get("timestamp", dt.datetime.utcnow()),
            open=bar_data.get("open", 0),
            high=bar_data.get("high", 0),
            low=bar_data.get("low", 0),
            close=bar_data.get("close", 0),
            volume=bar_data.get("volume", 0)
        )
    
    def _get_historical_data(self, symbol: str, bars: int) -> List[Dict]:
        """Get historical data for indicators"""
        try:
            return self.data_mux.history_1m_df(symbol, bars).to_dict('records')
        except Exception as e:
            log.error(f"Error getting historical data for {symbol}: {e}")
            return []
    
    def _calculate_indicators(self, data: List[Dict]) -> Dict[str, float]:
        """Calculate technical indicators"""
        if not data:
            return {}
        
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            
            indicators = {}
            
            # Simple moving averages
            if len(df) >= 20:
                indicators['sma_20'] = df['close'].rolling(20).mean().iloc[-1]
            if len(df) >= 50:
                indicators['sma_50'] = df['close'].rolling(50).mean().iloc[-1]
            
            # RSI
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                indicators['rsi'] = 100 - (100 / (1 + rs.iloc[-1]))
            
            # ATR
            if len(df) >= 14:
                high_low = df['high'] - df['low']
                high_close = (df['high'] - df['close'].shift()).abs()
                low_close = (df['low'] - df['close'].shift()).abs()
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                indicators['atr'] = true_range.rolling(14).mean().iloc[-1]
            
            return indicators
            
        except Exception as e:
            log.error(f"Error calculating indicators: {e}")
            return {}
    
    def _process_signal_alert(self, signal, bar):
        """Process signal and send alert (no trading)"""
        try:
            self.signals_generated += 1
            
            # Create alert message
            alert_message = f"📊 SIGNAL ALERT (Alert-Only Mode)\n"
            alert_message += f"Symbol: {signal.symbol}\n"
            alert_message += f"Type: {signal.type.upper()}\n"
            alert_message += f"Side: {signal.side.upper()}\n"
            alert_message += f"Price: ${signal.price:.2f}\n"
            alert_message += f"Confidence: {signal.confidence:.1%}\n"
            alert_message += f"Reason: {signal.reason}\n"
            alert_message += f"Strategy: {self.strategy_mode.title()}\n"
            alert_message += f"Mode: Alert-Only (No Trading)"
            
            # Send alert
            self.alert_manager._send_alert("SIGNAL", alert_message, signal.symbol)
            self.alerts_sent += 1
            
            log.info(f"Signal alert sent for {signal.symbol}: {signal.type} {signal.side} @ {signal.price}")
            
        except Exception as e:
            log.error(f"Error processing signal alert: {e}")
            self.errors_count += 1
    
    def _send_status_alert(self):
        """Send periodic status alerts"""
        try:
            # Send status every hour
            current_time = dt.datetime.utcnow()
            if current_time.minute == 0:  # Every hour
                status_message = f"📈 ETrade Strategy Status (Alert-Only)\n"
                status_message += f"Strategy: {self.strategy_mode.title()}\n"
                status_message += f"Uptime: {(current_time - self.start_time).total_seconds() / 3600:.1f} hours\n"
                status_message += f"Signals Generated: {self.signals_generated}\n"
                status_message += f"Alerts Sent: {self.alerts_sent}\n"
                status_message += f"Errors: {self.errors_count}\n"
                status_message += f"Market Status: {'Open' if self.clock.is_open() else 'Closed'}"
                
                self.alert_manager._send_alert("STATUS", status_message, "SYSTEM")
                
        except Exception as e:
            log.error(f"Error sending status alert: {e}")
    
    def _get_sleep_time(self) -> float:
        """Get sleep time based on strategy mode"""
        if self.strategy_mode == "quantum":
            return 30.0  # Check every 30 seconds for quantum mode
        elif self.strategy_mode == "advanced":
            return 60.0  # Check every minute for advanced mode
        else:  # standard
            return 120.0  # Check every 2 minutes for standard mode

# Entry points
def start():
    """Start the alert-only service"""
    service = AlertOnlyService()
    service.start()

def main():
    """Main entry point"""
    start()

def run():
    """Run entry point"""
    start()

def serve():
    """Serve entry point for web deployment"""
    start()