#!/usr/bin/env python3
"""
Unified Services Manager for Easy E*TRADE Strategy V2
====================================================

Manages and coordinates all Prime services for the trading system.
Provides a unified interface to start, stop, and monitor all services.

Author: Easy ETrade Strategy Team
Version: 2.0.0
"""

import os
import sys
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

from .base_service import BaseService, ServiceHealth
from .prime_data_service import PrimeDataService
from .prime_signal_service import PrimeSignalService
from .prime_trading_service import PrimeTradingService

# Try to import aiohttp for HTTP server
try:
    from aiohttp import web, web_request
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

log = logging.getLogger(__name__)

@dataclass
class ServicesStatus:
    """Overall services status"""
    all_healthy: bool
    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    stopped_services: int
    services: Dict[str, ServiceHealth]
    uptime_seconds: float
    last_check: float

class UnifiedServicesManager:
    """Unified manager for all Prime services"""
    
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.start_time = time.time()
        self.running = False
        
        # Initialize services
        self._initialize_services()
        
        log.info("UnifiedServicesManager initialized")
    
    def _initialize_services(self):
        """Initialize all services"""
        try:
            # Create service instances
            self.services = {
                'data_service': PrimeDataService(),
                'signal_service': PrimeSignalService(),
                'trading_service': PrimeTradingService()
            }
            
            log.info(f"✅ Initialized {len(self.services)} services")
            
        except Exception as e:
            log.error(f"❌ Error initializing services: {e}")
            raise
    
    def start_all_services(self) -> bool:
        """Start all services"""
        try:
            log.info("🚀 Starting all Prime services...")
            
            success_count = 0
            for name, service in self.services.items():
                try:
                    if service.start():
                        success_count += 1
                        log.info(f"✅ {name} started successfully")
                    else:
                        log.error(f"❌ Failed to start {name}")
                except Exception as e:
                    log.error(f"❌ Error starting {name}: {e}")
            
            self.running = True
            
            if success_count == len(self.services):
                log.info(f"🎯 All {success_count} services started successfully")
                return True
            else:
                log.warning(f"⚠️ {success_count}/{len(self.services)} services started successfully")
                return False
                
        except Exception as e:
            log.error(f"❌ Error starting services: {e}")
            return False
    
    def stop_all_services(self) -> bool:
        """Stop all services"""
        try:
            log.info("🛑 Stopping all Prime services...")
            
            success_count = 0
            for name, service in self.services.items():
                try:
                    if service.stop():
                        success_count += 1
                        log.info(f"✅ {name} stopped successfully")
                    else:
                        log.warning(f"⚠️ Failed to stop {name}")
                except Exception as e:
                    log.error(f"❌ Error stopping {name}: {e}")
            
            self.running = False
            
            log.info(f"🎯 {success_count}/{len(self.services)} services stopped")
            return success_count == len(self.services)
                
        except Exception as e:
            log.error(f"❌ Error stopping services: {e}")
            return False
    
    def restart_all_services(self) -> bool:
        """Restart all services"""
        log.info("🔄 Restarting all Prime services...")
        
        if not self.stop_all_services():
            log.warning("⚠️ Some services failed to stop during restart")
        
        # Wait a moment before restarting
        time.sleep(2)
        
        return self.start_all_services()
    
    def get_services_status(self) -> ServicesStatus:
        """Get comprehensive services status"""
        services_health = {}
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        stopped_count = 0
        
        for name, service in self.services.items():
            try:
                health = service.get_health_status()
                services_health[name] = health
                
                if health.status == "healthy":
                    healthy_count += 1
                elif health.status == "degraded":
                    degraded_count += 1
                elif health.status == "unhealthy":
                    unhealthy_count += 1
                else:
                    stopped_count += 1
                    
            except Exception as e:
                log.error(f"Error getting health status for {name}: {e}")
                services_health[name] = ServiceHealth(
                    name=name,
                    status="unknown",
                    uptime=0,
                    last_check=time.time(),
                    error_count=1,
                    message=f"Health check error: {e}",
                    metadata={}
                )
                stopped_count += 1
        
        all_healthy = (unhealthy_count == 0 and stopped_count == 0)
        
        return ServicesStatus(
            all_healthy=all_healthy,
            total_services=len(self.services),
            healthy_services=healthy_count,
            degraded_services=degraded_count,
            unhealthy_services=unhealthy_count,
            stopped_services=stopped_count,
            services=services_health,
            uptime_seconds=time.time() - self.start_time,
            last_check=time.time()
        )
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive service metrics"""
        metrics = {
            'manager': {
                'running': self.running,
                'uptime_seconds': time.time() - self.start_time,
                'total_services': len(self.services)
            },
            'services': {}
        }
        
        for name, service in self.services.items():
            try:
                metrics['services'][name] = service.get_service_metrics()
            except Exception as e:
                log.error(f"Error getting metrics for {name}: {e}")
                metrics['services'][name] = {'error': str(e)}
        
        return metrics
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for monitoring"""
        status = self.get_services_status()
        
        return {
            'status': 'healthy' if status.all_healthy else 'unhealthy',
            'summary': {
                'total': status.total_services,
                'healthy': status.healthy_services,
                'degraded': status.degraded_services,
                'unhealthy': status.unhealthy_services,
                'stopped': status.stopped_services
            },
            'uptime_hours': status.uptime_seconds / 3600,
            'last_check': datetime.fromtimestamp(status.last_check).isoformat(),
            'services': {name: health.status for name, health in status.services.items()}
        }

# Global services manager instance
services_manager = UnifiedServicesManager()

# HTTP API endpoints (if aiohttp is available)
async def handle_health(request: web_request.Request) -> web.Response:
    """Health check endpoint"""
    status = services_manager.get_services_status()
    return web.json_response({
        'status': 'healthy' if status.all_healthy else 'unhealthy',
        'services': status.__dict__
    })

async def handle_metrics(request: web_request.Request) -> web.Response:
    """Metrics endpoint"""
    metrics = services_manager.get_service_metrics()
    return web.json_response(metrics)

async def handle_status(request: web_request.Request) -> web.Response:
    """Status endpoint"""
    status = services_manager.get_health_summary()
    return web.json_response(status)

async def handle_start_services(request: web_request.Request) -> web.Response:
    """Start services endpoint"""
    try:
        success = services_manager.start_all_services()
        return web.json_response({
            'status': 'success' if success else 'partial',
            'message': 'Services started' if success else 'Some services failed to start'
        })
    except Exception as e:
        return web.json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)

async def handle_stop_services(request: web_request.Request) -> web.Response:
    """Stop services endpoint"""
    try:
        success = services_manager.stop_all_services()
        return web.json_response({
            'status': 'success' if success else 'partial',
            'message': 'Services stopped' if success else 'Some services failed to stop'
        })
    except Exception as e:
        return web.json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)

async def handle_restart_services(request: web_request.Request) -> web.Response:
    """Restart services endpoint"""
    try:
        success = services_manager.restart_all_services()
        return web.json_response({
            'status': 'success' if success else 'partial',
            'message': 'Services restarted' if success else 'Some services failed to restart'
        })
    except Exception as e:
        return web.json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)

async def create_app() -> web.Application:
    """Create aiohttp application"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/health', handle_health)
    app.router.add_get('/metrics', handle_metrics)
    app.router.add_get('/status', handle_status)
    app.router.add_post('/start', handle_start_services)
    app.router.add_post('/stop', handle_stop_services)
    app.router.add_post('/restart', handle_restart_services)
    app.router.add_get('/', handle_health)  # Root endpoint
    
    return app

async def main():
    """Main function for standalone operation"""
    log.info("🚀 Starting Unified Services Manager...")
    
    # Start all services
    if services_manager.start_all_services():
        log.info("✅ All services started successfully")
    else:
        log.error("❌ Some services failed to start")
    
    if AIOHTTP_AVAILABLE:
        # Create and start HTTP server
        app = await create_app()
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        
        log.info("🌐 HTTP server started on 0.0.0.0:8080")
        
        try:
            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            log.info("Received interrupt signal, shutting down...")
        finally:
            await runner.cleanup()
    else:
        log.warning("aiohttp not available, running in headless mode")
        try:
            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            log.info("Received interrupt signal, shutting down...")
    
    # Stop all services
    services_manager.stop_all_services()
    log.info("✅ Unified Services Manager stopped")

if __name__ == "__main__":
    asyncio.run(main())
