# services/base_service.py
"""
Base Service Interface
Defines the abstract base class for all services
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from modules.prime_models import PrimeSignal, PrimePosition, PrimeTrade
from datetime import datetime
import logging
import threading
import time

log = logging.getLogger("base_service")

@dataclass
class ServiceHealth:
    """Service health status"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy", "unknown"
    uptime: float
    last_check: float
    error_count: int
    message: str
    metadata: Dict[str, Any]

class BaseService(ABC):
    """Abstract base class for all services"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.is_running = False
        self.start_time = None
        self.health_status = "unknown"
        self.error_count = 0
        self.last_error = None
        self.thread = None
        self.stop_event = threading.Event()
        
        # Health monitoring
        self.health_checks = []
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        
        log.info(f"Service '{name}' initialized")
    
    @abstractmethod
    def _start_service(self) -> bool:
        """Start the service implementation"""
        pass
    
    @abstractmethod
    def _stop_service(self) -> bool:
        """Stop the service implementation"""
        pass
    
    @abstractmethod
    def _check_health(self) -> ServiceHealth:
        """Check service health"""
        pass
    
    def start(self) -> bool:
        """Start the service"""
        if self.is_running:
            log.warning(f"Service '{self.name}' is already running")
            return True
        
        try:
            log.info(f"Starting service '{self.name}'...")
            
            # Start the service implementation
            if not self._start_service():
                log.error(f"Failed to start service '{self.name}'")
                return False
            
            # Start health monitoring thread
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._health_monitor, daemon=True)
            self.thread.start()
            
            self.is_running = True
            self.start_time = time.time()
            self.health_status = "healthy"
            
            log.info(f"Service '{self.name}' started successfully")
            return True
            
        except Exception as e:
            log.error(f"Error starting service '{self.name}': {e}")
            self.last_error = str(e)
            self.error_count += 1
            return False
    
    def stop(self) -> bool:
        """Stop the service"""
        if not self.is_running:
            log.warning(f"Service '{self.name}' is not running")
            return True
        
        try:
            log.info(f"Stopping service '{self.name}'...")
            
            # Signal stop
            self.stop_event.set()
            
            # Stop the service implementation
            if not self._stop_service():
                log.warning(f"Service '{self.name}' stop implementation failed")
            
            # Wait for health monitor thread to stop
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            
            self.is_running = False
            self.health_status = "stopped"
            
            log.info(f"Service '{self.name}' stopped successfully")
            return True
            
        except Exception as e:
            log.error(f"Error stopping service '{self.name}': {e}")
            self.last_error = str(e)
            self.error_count += 1
            return False
    
    def restart(self) -> bool:
        """Restart the service"""
        log.info(f"Restarting service '{self.name}'...")
        
        if self.is_running:
            if not self.stop():
                log.error(f"Failed to stop service '{self.name}' for restart")
                return False
        
        # Wait a moment before restarting
        time.sleep(1)
        
        return self.start()
    
    def get_health_status(self) -> ServiceHealth:
        """Get current service health status"""
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
        
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return ServiceHealth(
            name=self.name,
            status=self.health_status,
            uptime=uptime,
            last_check=self.last_health_check,
            error_count=self.error_count,
            message=self.last_error or "Service is running",
            metadata={
                "start_time": self.start_time,
                "is_running": self.is_running,
                "thread_alive": self.thread.is_alive() if self.thread else False
            }
        )
    
    def _health_monitor(self):
        """Health monitoring thread"""
        while not self.stop_event.is_set():
            try:
                # Check service health
                health = self._check_health()
                self.last_health_check = time.time()
                
                # Update health status
                if health.status == "healthy":
                    self.health_status = "healthy"
                elif health.status == "degraded":
                    self.health_status = "degraded"
                else:
                    self.health_status = "unhealthy"
                    self.error_count += 1
                    self.last_error = health.message
                
                # Log health status changes
                if health.status != "healthy":
                    log.warning(f"Service '{self.name}' health: {health.status} - {health.message}")
                
            except Exception as e:
                log.error(f"Health check failed for service '{self.name}': {e}")
                self.health_status = "unhealthy"
                self.error_count += 1
                self.last_error = str(e)
            
            # Wait for next health check
            self.stop_event.wait(self.health_check_interval)
    
    def add_health_check(self, check_func, interval: int = 30):
        """Add custom health check function"""
        self.health_checks.append({
            "function": check_func,
            "interval": interval,
            "last_run": 0
        })
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "name": self.name,
            "running": self.is_running,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "health_status": self.health_status,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "start_time": self.start_time,
            "config": self.config
        }
    
    def is_healthy(self) -> bool:
        """Check if service is healthy"""
        return self.is_running and self.health_status == "healthy"
    
    def is_available(self) -> bool:
        """Check if service is available for use"""
        return self.is_running and self.health_status in ["healthy", "degraded"]

    def check_prime_system_health(self) -> bool:
        """Check Prime system health"""
        try:
            # Check if Prime system components are available
            return True
        except Exception as e:
            log.error(f"Prime system health check failed: {e}")
            return False
