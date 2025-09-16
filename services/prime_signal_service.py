# services/prime_signal_service.py
"""
Prime Signal Service for ETrade Strategy V2
High-performance signal generation service using Production Signal Generator
"""

from __future__ import annotations
import time
import logging
import datetime as dt
from typing import Dict, List, Optional, Any

from .base_service import BaseService, ServiceHealth
from modules.prime_data_manager import get_prime_data_manager
from modules.production_signal_generator import get_enhanced_production_signal_generator
from modules.prime_models import PrimeSignal, StrategyMode
from modules.config_loader import get_config_value

log = logging.getLogger("prime_signal_service")

class PrimeSignalService(BaseService):
    """High-performance signal generation service using Prime architecture"""
    
    def __init__(self):
        super().__init__("prime_signal_service")
        
        # Initialize Prime components
        self.data_manager = get_prime_data_manager()
        self.signal_generator = get_enhanced_production_signal_generator()
        
        # Service configuration
        self.signal_interval = get_config_value("SIGNAL_INTERVAL_SECONDS", 30)
        self.watchlist_size = get_config_value("MAX_WATCHLIST_SIZE", 65)
        
        # Performance tracking
        self.signals_generated = 0
        self.signals_by_strategy = {mode.value: 0 for mode in StrategyMode}
        
        log.info("PrimeSignalService initialized")
    
    def _start_service(self) -> bool:
        """Start Prime signal service"""
        try:
            log.info("Starting Prime Signal Service...")
            self._start_signal_generation()
            return True
        except Exception as e:
            log.error(f"Error starting Prime signal service: {e}")
            return False
    
    def _stop_service(self) -> bool:
        """Stop Prime signal service"""
        try:
            log.info("Stopping Prime Signal Service...")
            self.stop_event.set()
            return True
        except Exception as e:
            log.error(f"Error stopping Prime signal service: {e}")
            return False
    
    def _check_health(self) -> ServiceHealth:
        """Check Prime signal service health"""
        try:
            if not self.is_running:
                return ServiceHealth(
                    name=self.name,
                    status="stopped",
                    uptime=0,
                    last_check=time.time(),
                    error_count=self.error_count,
                    message="Service is not running",
                    metadata={}
                )
            
            # Check data manager health
            data_healthy = self.data_manager.is_healthy() if hasattr(self.data_manager, 'is_healthy') else True
            
            return ServiceHealth(
                name=self.name,
                status="healthy" if data_healthy else "degraded",
                uptime=time.time() - self.start_time,
                last_check=time.time(),
                error_count=self.error_count,
                message="Prime signal service operational" if data_healthy else "Data manager issues",
                metadata={
                    'signals_generated': self.signals_generated,
                    'signals_by_strategy': self.signals_by_strategy,
                    'data_healthy': data_healthy
                }
            )
            
        except Exception as e:
            log.error(f"Health check failed: {e}")
            return ServiceHealth(
                name=self.name,
                status="unhealthy",
                uptime=time.time() - self.start_time,
                last_check=time.time(),
                error_count=self.error_count + 1,
                message=f"Health check error: {e}",
                metadata={}
            )
    
    def _start_signal_generation(self):
        """Start signal generation loop"""
        log.info("Starting signal generation...")
        
        while not self.stop_event.is_set():
            try:
                # Get watchlist
                watchlist = self._get_watchlist()
                
                # Generate signals for each symbol
                for symbol in watchlist:
                    self._generate_signals_for_symbol(symbol)
                
                # Wait for next iteration
                self.stop_event.wait(self.signal_interval)
                
            except Exception as e:
                log.error(f"Signal generation error: {e}")
                self.stop_event.wait(5)
        
        log.info("Signal generation stopped")
    
    def _get_watchlist(self) -> List[str]:
        """Get current watchlist"""
        try:
            # Use Prime data manager to get watchlist
            return self.data_manager.get_watchlist() if hasattr(self.data_manager, 'get_watchlist') else []
        except Exception as e:
            log.error(f"Error getting watchlist: {e}")
            return []
    
    def _generate_signals_for_symbol(self, symbol: str):
        """Generate signals for a specific symbol"""
        try:
            # Get market data
            market_data = self._get_market_data(symbol)
            if not market_data:
                return
            
            # Generate signals for each strategy
            for strategy in StrategyMode:
                signal = self.signal_generator.generate_profitable_signal(
                    symbol=symbol,
                    market_data=market_data,
                    strategy=strategy
                )
                
                if signal:
                    self.signals_generated += 1
                    self.signals_by_strategy[strategy.value] += 1
                    log.info(f"Signal generated for {symbol} using {strategy.value} strategy")
            
        except Exception as e:
            log.error(f"Error generating signals for {symbol}: {e}")
    
    def _get_market_data(self, symbol: str) -> Optional[List[Dict]]:
        """Get market data for symbol"""
        try:
            # Use Prime data manager to get market data
            return self.data_manager.get_market_data(symbol) if hasattr(self.data_manager, 'get_market_data') else None
        except Exception as e:
            log.error(f"Error getting market data for {symbol}: {e}")
            return None

# Service entry points
def start():
    """Start the Prime signal service"""
    service = PrimeSignalService()
    service.start()

def main():
    """Main entry point"""
    start()

def serve():
    """Serve entry point for web deployment"""
    start()
