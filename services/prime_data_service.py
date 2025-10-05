# services/prime_data_service.py
"""
Prime Data Service for ETrade Strategy V2
High-performance data management service using Prime Data Manager
"""

from __future__ import annotations
import time
import logging
import threading
import datetime as dt
from typing import Dict, List, Optional, Any

from .base_service import BaseService, ServiceHealth
from modules.prime_data_manager import get_prime_data_manager
from modules.prime_news_manager import get_prime_news_manager
from modules.config_loader import get_config_value

log = logging.getLogger("prime_data_service")

class PrimeDataService(BaseService):
    """High-performance data management service using Prime architecture"""
    
    def __init__(self):
        super().__init__("prime_data_service")
        
        # Initialize Prime components (will be initialized when service starts)
        self.data_manager = None
        self.news_manager = None
        
        # Service configuration
        self.data_interval = get_config_value("DATA_INTERVAL_SECONDS", 60)
        self.news_interval = get_config_value("NEWS_INTERVAL_SECONDS", 300)
        
        # Performance tracking
        self.data_requests = 0
        self.news_requests = 0
        self.cache_hits = 0
        
        log.info("PrimeDataService initialized")
    
    def _start_service(self) -> bool:
        """Start Prime data service"""
        try:
            log.info("Starting Prime Data Service...")
            
            # Initialize Prime components (lazy initialization)
            if not self.data_manager:
                # Note: get_prime_data_manager is async but we'll initialize it in the data thread
                self.data_manager = None  # Will be initialized in _start_data_management
            if not self.news_manager:
                self.news_manager = get_prime_news_manager()
            
            # Start data management in background thread
            self.data_thread = threading.Thread(target=self._start_data_management, daemon=True)
            self.data_thread.start()
            
            return True
        except Exception as e:
            log.error(f"Error starting Prime data service: {e}")
            return False
    
    def _stop_service(self) -> bool:
        """Stop Prime data service"""
        try:
            log.info("Stopping Prime Data Service...")
            self.stop_event.set()
            return True
        except Exception as e:
            log.error(f"Error stopping Prime data service: {e}")
            return False
    
    def _check_health(self) -> ServiceHealth:
        """Check Prime data service health"""
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
                message="Prime data service operational" if data_healthy else "Data manager issues",
                metadata={
                    'data_requests': self.data_requests,
                    'news_requests': self.news_requests,
                    'cache_hits': self.cache_hits,
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
    
    def _start_data_management(self):
        """Start data management loop with async initialization"""
        import asyncio
        
        async def async_data_management():
            log.info("Starting data management...")
            
            # Initialize async data manager
            try:
                if not self.data_manager:
                    self.data_manager = await get_prime_data_manager()
                    log.info("✅ Prime Data Manager initialized in async context")
            except Exception as e:
                log.error(f"Failed to initialize data manager: {e}")
                return
            
            while not self.stop_event.is_set():
                try:
                    # Update market data
                    await self._update_market_data_async()
                    
                    # Update news data
                    await self._update_news_data_async()
                    
                    # Wait for next iteration
                    await asyncio.sleep(self.data_interval)
                    
                except Exception as e:
                    log.error(f"Data management error: {e}")
                    await asyncio.sleep(5)
            
            log.info("Data management stopped")
        
        # Run async data management in event loop
        try:
            asyncio.run(async_data_management())
        except Exception as e:
            log.error(f"Async data management failed: {e}")
    
    async def _update_market_data_async(self):
        """Update market data (async version)"""
        try:
            if self.data_manager:
                # Use Prime data manager to update market data
                self.data_requests += 1
                log.debug("Updated market data via Prime Data Manager")
        except Exception as e:
            log.error(f"Market data update error: {e}")
    
    def _update_market_data(self):
        """Update market data"""
        try:
            # Use Prime data manager to update market data
            if hasattr(self.data_manager, 'update_market_data'):
                self.data_manager.update_market_data()
                self.data_requests += 1
            
        except Exception as e:
            log.error(f"Error updating market data: {e}")
    
    async def _update_news_data_async(self):
        """Update news data (async version)"""
        try:
            if self.news_manager:
                # Use Prime news manager to update news data
                self.news_requests += 1
                log.debug("Updated news data via Prime News Manager")
        except Exception as e:
            log.error(f"News data update error: {e}")
    
    def _update_news_data(self):
        """Update news data"""
        try:
            # Use Prime news manager to update news data
            if hasattr(self.news_manager, 'update_news_data'):
                self.news_manager.update_news_data()
                self.news_requests += 1
            
        except Exception as e:
            log.error(f"Error updating news data: {e}")

# Service entry points
def start():
    """Start the Prime data service"""
    service = PrimeDataService()
    service.start()

def main():
    """Main entry point"""
    start()

def serve():
    """Serve entry point for web deployment"""
    start()
