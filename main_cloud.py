#!/usr/bin/env python3
"""
Cloud Deployment Entry Point for Easy ETrade Strategy
====================================================

This is the entry point for Google Cloud Run deployment of the main trading system.
It sets up the cloud environment and runs the main trading bot with continuous operation.
"""

import os
import sys
import asyncio
import logging
import threading
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import uvicorn
import aiohttp

# Set cloud environment variables
os.environ.setdefault('ENVIRONMENT', 'production')
os.environ.setdefault('SYSTEM_MODE', 'full_trading')
os.environ.setdefault('AUTOMATION_MODE', 'demo')
os.environ.setdefault('ETRADE_MODE', 'demo')
os.environ.setdefault('CLOUD_MODE', 'true')
os.environ.setdefault('PORT', '8080')

# Import the main application
from main import main, ARGS

# Global trading system thread
_trading_thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global _trading_thread
    try:
        logger.info("🚀 Cloud Run startup - Starting trading system...")
        
        # Start trading system in background thread
        _trading_thread = threading.Thread(target=start_trading_system, daemon=True)
        _trading_thread.start()
        
        logger.info("✅ Trading system started in background thread")
        
    except Exception as e:
        logger.error(f"❌ Failed to start trading system: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cloud Run shutdown - Stopping trading system...")
    logger.info("✅ Trading system shutdown completed")

# Create FastAPI app for Cloud Run
app = FastAPI(title="Easy ETrade Strategy", version="1.0.0", lifespan=lifespan)

# Setup logging for cloud
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    return {
        "message": "Easy ETrade Strategy - Cloud Deployment",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('ENVIRONMENT'),
        "system_mode": os.getenv('SYSTEM_MODE'),
        "automation_mode": os.getenv('AUTOMATION_MODE'),
        "etrade_mode": os.getenv('ETRADE_MODE'),
        "trading_thread_active": _trading_thread is not None and _trading_thread.is_alive()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "trading_system": "active" if _trading_thread and _trading_thread.is_alive() else "inactive"
    }

@app.get("/status")
async def status():
    return {
        "service": "Easy ETrade Strategy",
        "status": "active",
        "uptime": "running",
        "cloud_mode": True,
        "trading_thread_active": _trading_thread is not None and _trading_thread.is_alive()
    }

@app.post("/api/alerts/midnight-token-expiry")
async def midnight_token_expiry_alert(request: Request):
    """Handle midnight ET token expiry alert from Cloud Scheduler"""
    try:
        logger.info("🌙 Midnight token expiry alert triggered")
        
        # Import the alert manager
        from modules.prime_alert_manager import PrimeAlertManager
        
        # Initialize alert manager
        alert_manager = PrimeAlertManager()
        
        # Send the midnight OAuth alert
        success = await alert_manager.send_oauth_morning_alert()
        
        return {
            "success": success,
            "message": "Midnight token expiry alert sent" if success else "Failed to send midnight alert",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Midnight alert error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/alerts/market-open")
async def market_open_alert(request: Request):
    """Handle market open alert from Cloud Scheduler"""
    try:
        logger.info("🌅 Market open alert triggered")
        
        # Import the alert manager
        from modules.prime_alert_manager import PrimeAlertManager
        
        # Initialize alert manager
        alert_manager = PrimeAlertManager()
        
        # Send the market open OAuth alert
        success = await alert_manager.send_oauth_market_open_alert()
        
        return {
            "success": success,
            "message": "Market open alert sent" if success else "Failed to send market open alert",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Market open alert error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/build-watchlist")
async def build_watchlist_endpoint(request: Request):
    """Build fresh dynamic watchlist (triggered by Cloud Scheduler at 7 AM ET)"""
    try:
        logger.info("📊 Watchlist build triggered by Cloud Scheduler")
        
        import subprocess
        
        # Run build_dynamic_watchlist.py
        watchlist_script = "build_dynamic_watchlist.py"
        
        if os.path.exists(watchlist_script):
            logger.info(f"🔄 Running {watchlist_script}...")
            
            result = subprocess.run(
                ["python3", watchlist_script],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ Dynamic watchlist built successfully")
                
                # Count symbols in watchlist
                try:
                    import pandas as pd
                    df = pd.read_csv("data/watchlist/dynamic_watchlist.csv")
                    symbol_count = len(df)
                except:
                    symbol_count = 0
                
                return {
                    "status": "success",
                    "message": f"Watchlist built successfully with {symbol_count} symbols",
                    "timestamp": datetime.now().isoformat(),
                    "output": result.stdout[:500]
                }
            else:
                logger.error(f"❌ Watchlist build failed: {result.stderr}")
                return {
                    "status": "error",
                    "message": "Watchlist build failed",
                    "error": result.stderr[:500]
                }
        else:
            logger.error(f"❌ Watchlist script not found: {watchlist_script}")
            return {
                "status": "error",
                "message": f"Watchlist script not found: {watchlist_script}"
            }
            
    except Exception as e:
        logger.error(f"❌ Watchlist build endpoint error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def start_trading_system():
    """Start the trading system in a background thread"""
    try:
        logger.info("🚀 Starting Easy ETrade Strategy trading system...")
        
        # Set up environment for trading
        os.environ['AUTOMATION_MODE'] = 'demo'
        os.environ['ETRADE_MODE'] = 'demo'
        os.environ['SYSTEM_MODE'] = 'full_trading'
        os.environ['CLOUD_MODE'] = 'true'
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start the main trading system
        loop.run_until_complete(main())
        
    except Exception as e:
        logger.error(f"❌ Trading system error: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise

def run_cloud_server():
    """Run the FastAPI server for Cloud Run"""
    try:
        # Get port from environment (Cloud Run sets PORT)
        port = int(os.getenv('PORT', 8080))
        
        logger.info(f"🌐 Starting Cloud Run server on port {port}")
        
        # Run FastAPI server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Cloud server error: {e}")
        raise

if __name__ == "__main__":
    run_cloud_server()