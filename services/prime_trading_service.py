# services/prime_trading_service.py
"""
Prime Trading Service for ETrade Strategy V2
High-performance trading service using Prime Trading Manager
"""

from __future__ import annotations
import time
import logging
import threading
import datetime as dt
from typing import Dict, List, Optional, Any

from .base_service import BaseService, ServiceHealth
from modules.prime_unified_trade_manager import get_prime_unified_trade_manager
from modules.prime_data_manager import get_prime_data_manager
from modules.production_signal_generator import get_enhanced_production_signal_generator
from modules.prime_models import PrimeSignal, PrimePosition, PrimeTrade, StrategyMode
from modules.config_loader import get_config_value

log = logging.getLogger("prime_trading_service")

class PrimeTradingService(BaseService):
    """High-performance trading service using Prime architecture"""
    
    def __init__(self):
        super().__init__("prime_trading_service")
        
        # Initialize Prime components (will be initialized when service starts)
        self.trading_manager = None
        self.data_manager = None
        self.signal_generator = None
        
        # Service configuration
        self.trading_interval = get_config_value("TRADING_INTERVAL_SECONDS", 10)
        self.max_positions = get_config_value("MAX_OPEN_POSITIONS", 10)
        
        # Performance tracking
        self.trades_executed = 0
        self.positions_opened = 0
        self.positions_closed = 0
        
        log.info("PrimeTradingService initialized")
    
    def _start_service(self) -> bool:
        """Start Prime trading service"""
        try:
            log.info("Starting Prime Trading Service...")
            
            # Initialize Prime components (lazy initialization)
            if not self.trading_manager:
                self.trading_manager = get_prime_unified_trade_manager()
            if not self.data_manager:
                self.data_manager = get_prime_data_manager()
            if not self.signal_generator:
                self.signal_generator = get_enhanced_production_signal_generator()
            
            # Start trading loop in background thread
            self.trading_thread = threading.Thread(target=self._start_trading_loop, daemon=True)
            self.trading_thread.start()
            
            return True
        except Exception as e:
            log.error(f"Error starting Prime trading service: {e}")
            return False
    
    def _stop_service(self) -> bool:
        """Stop Prime trading service"""
        try:
            log.info("Stopping Prime Trading Service...")
            self.stop_event.set()
            return True
        except Exception as e:
            log.error(f"Error stopping Prime trading service: {e}")
            return False
    
    def _check_health(self) -> ServiceHealth:
        """Check Prime trading service health"""
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
            
            # Check trading manager health
            trading_healthy = self.trading_manager.is_healthy() if hasattr(self.trading_manager, 'is_healthy') else True
            
            return ServiceHealth(
                name=self.name,
                status="healthy" if trading_healthy else "degraded",
                uptime=time.time() - self.start_time,
                last_check=time.time(),
                error_count=self.error_count,
                message="Prime trading service operational" if trading_healthy else "Trading manager issues",
                metadata={
                    'trades_executed': self.trades_executed,
                    'positions_opened': self.positions_opened,
                    'positions_closed': self.positions_closed,
                    'trading_healthy': trading_healthy
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
    
    def _start_trading_loop(self):
        """Start trading loop"""
        log.info("Starting trading loop...")
        
        while not self.stop_event.is_set():
            try:
                # Check for new signals
                self._process_signals()
                
                # Manage existing positions
                self._manage_positions()
                
                # Wait for next iteration
                self.stop_event.wait(self.trading_interval)
                
            except Exception as e:
                log.error(f"Trading loop error: {e}")
                self.stop_event.wait(5)
        
        log.info("Trading loop stopped")
    
    def _process_signals(self):
        """Process incoming signals"""
        try:
            # Get signals from signal generator
            signals = self._get_pending_signals()
            
            for signal in signals:
                if self._should_execute_signal(signal):
                    self._execute_signal(signal)
            
        except Exception as e:
            log.error(f"Error processing signals: {e}")
    
    def _manage_positions(self):
        """Manage existing positions"""
        try:
            # Get current positions
            positions = self._get_current_positions()
            
            for position in positions:
                if self._should_close_position(position):
                    self._close_position(position)
            
        except Exception as e:
            log.error(f"Error managing positions: {e}")
    
    def _get_pending_signals(self) -> List[PrimeSignal]:
        """Get pending signals"""
        # Implementation would get signals from signal generator
        return []
    
    def _should_execute_signal(self, signal: PrimeSignal) -> bool:
        """Check if signal should be executed"""
        # Check position limits, risk management, etc.
        return True
    
    def _execute_signal(self, signal: PrimeSignal):
        """Execute a trading signal"""
        try:
            # Use Prime trading manager to execute signal
            if hasattr(self.trading_manager, 'execute_signal'):
                result = self.trading_manager.execute_signal(signal)
                if result:
                    self.trades_executed += 1
                    self.positions_opened += 1
                    log.info(f"Signal executed for {signal.symbol}")
            
        except Exception as e:
            log.error(f"Error executing signal: {e}")
    
    def _get_current_positions(self) -> List[PrimePosition]:
        """Get current positions"""
        # Implementation would get positions from trading manager
        return []
    
    def _should_close_position(self, position: PrimePosition) -> bool:
        """Check if position should be closed"""
        # Check stop loss, take profit, time-based exits, etc.
        return False
    
    def _close_position(self, position: PrimePosition):
        """Close a position"""
        try:
            # Use Prime trading manager to close position
            if hasattr(self.trading_manager, 'close_position'):
                result = self.trading_manager.close_position(position)
                if result:
                    self.positions_closed += 1
                    log.info(f"Position closed for {position.symbol}")
            
        except Exception as e:
            log.error(f"Error closing position: {e}")

# Service entry points
def start():
    """Start the Prime trading service"""
    service = PrimeTradingService()
    service.start()

def main():
    """Main entry point"""
    start()

def serve():
    """Serve entry point for web deployment"""
    start()
