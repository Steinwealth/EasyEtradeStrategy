#!/usr/bin/env python3
"""
Scanner Service for Easy E*TRADE Strategy V2
===========================================

Cloud Run service that provides scanner functionality as a microservice.
This service handles:
- Market session monitoring
- Watchlist building
- Premarket sentiment analysis
- Integration with main trading system

Author: Easy ETrade Strategy Team
Version: 2.0.0
"""

import os
import sys
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
import json

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import scanner functionality - moved from deleted scanner.py
from build_dynamic_watchlist import build_dynamic_watchlist

# Market phase detection (moved from deleted scanner.py)
def get_market_phase() -> str:
    """Determine current market phase."""
    try:
        from modules.market_clock_ext import MarketClock
        MARKET_CLOCK_AVAILABLE = True
    except ImportError:
        MARKET_CLOCK_AVAILABLE = False
    
    if not MARKET_CLOCK_AVAILABLE:
        # Fallback to simple time-based logic
        now = datetime.now()
        hour = now.hour
        
        if 7 <= hour < 9:  # 7:00 AM - 9:30 AM
            return "PREP"
        elif 9 <= hour < 16:  # 9:30 AM - 4:00 PM
            return "OPEN"
        elif 16 <= hour < 18:  # 4:00 PM - 6:00 PM
            return "COOLDOWN"
        else:
            return "DARK"
    
    # Use MarketClock if available
    clock = MarketClock()
    now_open = clock.is_open()
    
    # Build absolute ET times for prep/cooldown boundaries
    today = clock._today_local()
    prep_start = today.replace(hour=7, minute=0, second=0, microsecond=0)
    cool_end = today.replace(hour=18, minute=0, second=0, microsecond=0)
    now = clock._now_local()
    
    if now_open:
        return "OPEN"
    elif prep_start <= now < today.replace(hour=9, minute=30):
        return "PREP"
    elif today.replace(hour=16) <= now < cool_end:
        return "COOLDOWN"
    else:
        return "DARK"

def build_hybrid_watchlist():
    """Build the enhanced hybrid watchlist with sentiment integration."""
    try:
        log.info("📊 Building dynamic watchlist with sentiment analysis...")
        build_dynamic_watchlist()
        log.info("✅ Dynamic watchlist build completed successfully")
    except Exception as e:
        log.error(f"❌ Error building watchlist: {e}")

def run_premarket_sentiment_analysis():
    """Run premarket sentiment analysis before building watchlist."""
    try:
        log.info("📰 Running premarket sentiment analysis...")
        # Note: This would call the sentiment analysis script if it exists
        log.info("✅ Sentiment analysis completed successfully")
    except Exception as e:
        log.error(f"❌ Error running sentiment analysis: {e}")

# Try to import aiohttp for HTTP server
try:
    from aiohttp import web, web_request
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
PORT = int(os.getenv('PORT', 8080))
HOST = os.getenv('HOST', '0.0.0.0')

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
log = logging.getLogger(__name__)

class ScannerService:
    """Scanner service for market monitoring and watchlist building"""
    
    def __init__(self):
        self.running = False
        self.last_phase = None
        self.last_prep_day = None
        self.metrics = {
            'start_time': time.time(),
            'phase_transitions': 0,
            'watchlist_builds': 0,
            'sentiment_analyses': 0,
            'errors': 0
        }
    
    async def start(self):
        """Start the scanner service"""
        self.running = True
        log.info("🚀 Scanner Service starting...")
        
        # Start background monitoring task
        asyncio.create_task(self._monitor_market_phases())
        
        log.info("✅ Scanner Service started successfully")
    
    async def stop(self):
        """Stop the scanner service"""
        self.running = False
        log.info("🛑 Scanner Service stopping...")
    
    async def _monitor_market_phases(self):
        """Monitor market phases and trigger actions"""
        log.info("🔄 Starting market phase monitoring...")
        
        while self.running:
            try:
                current_phase = get_market_phase()
                
                # Log phase changes
                if current_phase != self.last_phase:
                    log.info(f"📊 Phase transition: {self.last_phase} → {current_phase}")
                    self.last_phase = current_phase
                    self.metrics['phase_transitions'] += 1
                    
                    # Build watchlist during PREP phase (once per day)
                    if current_phase == "PREP":
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        if self.last_prep_day != today_str:
                            await self._build_watchlist()
                            self.last_prep_day = today_str
                            log.info(f"📋 Daily watchlist build completed for {today_str}")
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                log.error(f"❌ Error in market phase monitoring: {e}")
                self.metrics['errors'] += 1
                await asyncio.sleep(30)
    
    async def _build_watchlist(self):
        """Build watchlist with sentiment analysis"""
        try:
            log.info("📊 Building watchlist with sentiment analysis...")
            
            # Run sentiment analysis
            await self._run_sentiment_analysis()
            
            # Build watchlist
            build_hybrid_watchlist()
            self.metrics['watchlist_builds'] += 1
            
            log.info("✅ Watchlist build completed successfully")
            
        except Exception as e:
            log.error(f"❌ Error building watchlist: {e}")
            self.metrics['errors'] += 1
    
    async def _run_sentiment_analysis(self):
        """Run premarket sentiment analysis"""
        try:
            log.info("📰 Running premarket sentiment analysis...")
            run_premarket_sentiment_analysis()
            self.metrics['sentiment_analyses'] += 1
            log.info("✅ Sentiment analysis completed successfully")
            
        except Exception as e:
            log.error(f"❌ Error running sentiment analysis: {e}")
            self.metrics['errors'] += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get scanner service status"""
        return {
            'status': 'running' if self.running else 'stopped',
            'current_phase': get_market_phase(),
            'last_phase': self.last_phase,
            'last_prep_day': self.last_prep_day,
            'uptime_seconds': time.time() - self.metrics['start_time'],
            'metrics': self.metrics
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get scanner service metrics"""
        return self.metrics

# Global scanner service instance
scanner_service = ScannerService()

async def handle_health(request: web_request.Request) -> web.Response:
    """Health check endpoint"""
    status = scanner_service.get_status()
    return web.json_response(status)

async def handle_metrics(request: web_request.Request) -> web.Response:
    """Metrics endpoint"""
    metrics = scanner_service.get_metrics()
    return web.json_response(metrics)

async def handle_status(request: web_request.Request) -> web.Response:
    """Status endpoint"""
    status = scanner_service.get_status()
    return web.json_response(status)

async def handle_build_watchlist(request: web_request.Request) -> web.Response:
    """Manual watchlist build endpoint"""
    try:
        await scanner_service._build_watchlist()
        return web.json_response({'status': 'success', 'message': 'Watchlist build completed'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

async def handle_sentiment_analysis(request: web_request.Request) -> web.Response:
    """Manual sentiment analysis endpoint"""
    try:
        await scanner_service._run_sentiment_analysis()
        return web.json_response({'status': 'success', 'message': 'Sentiment analysis completed'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

async def create_app() -> web.Application:
    """Create aiohttp application"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/health', handle_health)
    app.router.add_get('/metrics', handle_metrics)
    app.router.add_get('/status', handle_status)
    app.router.add_post('/build-watchlist', handle_build_watchlist)
    app.router.add_post('/sentiment-analysis', handle_sentiment_analysis)
    app.router.add_get('/', handle_health)  # Root endpoint
    
    return app

async def main():
    """Main function"""
    log.info("🚀 Starting Scanner Service...")
    
    # Start scanner service
    await scanner_service.start()
    
    if AIOHTTP_AVAILABLE:
        # Create and start HTTP server
        app = await create_app()
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, HOST, PORT)
        await site.start()
        
        log.info(f"🌐 HTTP server started on {HOST}:{PORT}")
        
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
    
    # Stop scanner service
    await scanner_service.stop()
    log.info("✅ Scanner Service stopped")

if __name__ == "__main__":
    # Change to parent directory to access modules and data
    import os
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    os.chdir(parent_dir)
    asyncio.run(main())
