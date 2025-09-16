# services/position_tracking_service.py
"""
Position Tracking Service for ETrade Strategy
Dedicated position tracking service for live trading
"""

from __future__ import annotations
import time
import logging
import datetime as dt
from typing import Dict, List, Optional, Any

from .base_service import BaseService, ServiceHealth
from modules.config_loader import get_config_value
from modules.etrade_client import ETradeClient
from modules.etrade_oauth import OAuthManager
from modules.prime_trading_manager import get_prime_trading_manager
from modules.prime_trading_manager import get_prime_trading_manager
from modules.alerting import AlertManager

log = logging.getLogger("position_tracking_service")

class PositionTrackingService(BaseService):
    """Dedicated position tracking service for live trading"""
    
    def __init__(self):
        super().__init__("position_tracking_service")
        
        # Position tracking configuration
        self.sync_interval = get_config_value("POSITION_SYNC_INTERVAL", 10)
        self.alert_thresholds = {
            'pnl_alert': get_config_value("PNL_ALERT_THRESHOLD", 0.05),
            'position_alert': get_config_value("POSITION_ALERT_THRESHOLD", 0.1),
            'risk_alert': get_config_value("RISK_ALERT_THRESHOLD", 0.8)
        }
        
        # Initialize ETRADE components
        self._initialize_etrade_components()
        
        # Initialize tracking components
        self.position_manager = PositionManager()
        self.position_synchronizer = PositionSynchronizer(self.etrade_client, self.position_manager)
        self.alert_manager = AlertManager()
        
        # Alert tracking
        self.position_alerts = []
        self.last_positions = {}
        self.last_pnl = 0.0
        
        log.info("PositionTrackingService initialized")
    
    def _initialize_etrade_components(self):
        """Initialize ETRADE OAuth and client"""
        try:
            import os
            self.oauth_manager = OAuthManager(
                consumer_key=os.getenv("ETRADE_CONSUMER_KEY"),
                consumer_secret=os.getenv("ETRADE_CONSUMER_SECRET"),
                tokens_path="data/etrade_tokens.json"
            )
            
            self.etrade_client = ETradeClient(
                oauth=self.oauth_manager,
                account_id_key=os.getenv("ETRADE_ACCOUNT_ID"),
                tag_prefix="TRACK"
            )
            
            log.info("ETRADE components initialized for position tracking")
            
        except Exception as e:
            log.error(f"ETRADE initialization failed: {e}")
            raise
    
    def _start_service(self) -> bool:
        """Start position tracking service"""
        try:
            log.info("Starting Position Tracking Service...")
            self._start_position_monitoring()
            return True
            
        except Exception as e:
            log.error(f"Error starting position tracking service: {e}")
            return False
    
    def _stop_service(self) -> bool:
        """Stop position tracking service"""
        try:
            log.info("Stopping Position Tracking Service...")
            self.stop_event.set()
            return True
            
        except Exception as e:
            log.error(f"Error stopping position tracking service: {e}")
            return False
    
    def _check_health(self) -> ServiceHealth:
        """Check position tracking service health"""
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
            
            # Check ETRADE connectivity
            try:
                account_cash = self.etrade_client.account_cash()
                etrade_healthy = account_cash >= 0
            except:
                etrade_healthy = False
            
            return ServiceHealth(
                name=self.name,
                status="healthy" if etrade_healthy else "unhealthy",
                uptime=time.time() - self.start_time,
                last_check=time.time(),
                error_count=self.error_count,
                message="Position tracking operational" if etrade_healthy else "ETRADE connectivity issues",
                metadata={
                    'etrade_healthy': etrade_healthy,
                    'positions_tracked': len(self.position_manager.get_all_positions()),
                    'alerts_generated': len(self.position_alerts)
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
    
    def _start_position_monitoring(self):
        """Start real-time position monitoring"""
        log.info("Starting position monitoring...")
        
        while not self.stop_event.is_set():
            try:
                # Sync with ETRADE
                sync_results = self.position_synchronizer.sync_positions()
                
                # Check for alerts
                self._check_position_alerts(sync_results)
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Wait for next check
                self.stop_event.wait(self.sync_interval)
                
            except Exception as e:
                log.error(f"Position monitoring error: {e}")
                self.stop_event.wait(5)
        
        log.info("Position monitoring stopped")
    
    def _check_position_alerts(self, sync_results: Dict[str, Any]):
        """Check for position-related alerts"""
        try:
            current_positions = self.position_manager.get_all_positions()
            current_pnl = self.position_manager.get_total_pnl()
            
            # Check for new positions
            for symbol, position in current_positions.items():
                if symbol not in self.last_positions:
                    self._generate_alert(
                        symbol=symbol,
                        alert_type="NEW_POSITION",
                        message=f"New position: {position.side} {position.quantity} @ {position.entry_price}"
                    )
            
            # Check for closed positions
            for symbol in self.last_positions:
                if symbol not in current_positions:
                    self._generate_alert(
                        symbol=symbol,
                        alert_type="POSITION_CLOSED",
                        message=f"Position closed: {symbol}"
                    )
            
            # Check for PnL changes
            if self.last_pnl != 0:
                pnl_change = abs(current_pnl - self.last_pnl) / abs(self.last_pnl)
                if pnl_change > self.alert_thresholds['pnl_alert']:
                    self._generate_alert(
                        symbol="PORTFOLIO",
                        alert_type="PNL_CHANGE",
                        message=f"PnL change: {current_pnl:.2f} ({((current_pnl - self.last_pnl) / abs(self.last_pnl) * 100):.1f}%)"
                    )
            
            # Update last positions
            self.last_positions = current_positions.copy()
            self.last_pnl = current_pnl
            
        except Exception as e:
            log.error(f"Position alert check failed: {e}")
    
    def _generate_alert(self, symbol: str, alert_type: str, message: str):
        """Generate position alert"""
        try:
            alert = {
                'symbol': symbol,
                'alert_type': alert_type,
                'message': message,
                'timestamp': dt.datetime.utcnow()
            }
            
            self.position_alerts.append(alert)
            
            # Keep only last 1000 alerts
            if len(self.position_alerts) > 1000:
                self.position_alerts = self.position_alerts[-1000:]
            
            # Send alert via alert manager
            self.alert_manager.send_alert(
                title=f"Position Alert: {alert_type}",
                message=f"{symbol}: {message}",
                severity="info"
            )
            
            log.info(f"Position alert: {symbol} - {alert_type}")
            
        except Exception as e:
            log.error(f"Alert generation failed: {e}")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            portfolio_summary = self.position_manager.get_portfolio_summary()
            if portfolio_summary:
                log.info(f"Portfolio: {portfolio_summary['total_positions']} positions, "
                        f"PnL: {portfolio_summary['total_unrealized_pnl']:.2f}")
            
        except Exception as e:
            log.error(f"Performance metrics update failed: {e}")
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get comprehensive position summary"""
        try:
            portfolio_summary = self.position_manager.get_portfolio_summary()
            sync_status = self.position_synchronizer.get_sync_status()
            
            return {
                'portfolio': portfolio_summary,
                'sync_status': sync_status,
                'recent_alerts': self.position_alerts[-10:] if self.position_alerts else [],
                'alert_count': len(self.position_alerts),
                'service_uptime': time.time() - self.start_time if self.start_time else 0
            }
            
        except Exception as e:
            log.error(f"Position summary failed: {e}")
            return {}

# Service entry points
def start():
    """Start the position tracking service"""
    service = PositionTrackingService()
    service.start()

def main():
    """Main entry point"""
    start()

def serve():
    """Serve entry point for web deployment"""
    start()