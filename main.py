#!/usr/bin/env python3
"""
Improved Main Entry Point
High-performance entry point using the integrated trading system
Consolidates all functionality and eliminates redundancy
"""

from __future__ import annotations
import os
import sys
import logging
import argparse
import asyncio
import signal
from typing import Optional
from datetime import datetime

# --- Prime System Imports ---
from modules.prime_trading_system import (
    get_prime_trading_system, PrimeTradingSystem, TradingConfig, SystemMode
)
from modules.prime_market_manager import (
    get_prime_market_manager, PrimeMarketManager, MarketSession
)
from modules.production_signal_generator import get_enhanced_production_signal_generator, EnhancedProductionSignalGenerator
from modules.etrade_oauth_integration import get_etrade_oauth_integration
from modules.prime_etrade_trading import PrimeETradeTrading
from modules.prime_models import StrategyMode
from modules.config_loader import load_configuration, get_config_value

# OAuth keep-alive handled by Cloud Scheduler (no local keep-alive needed)

# --- Google Cloud specific imports ---
try:
    from google.cloud import logging as gcp_logging
    GCP_LOGGING_AVAILABLE = True
except ImportError:
    GCP_LOGGING_AVAILABLE = False

# --- Load configuration based on command line args or environment ---
def load_app_config():
    parser = argparse.ArgumentParser(description='ETrade Strategy Trading Bot - Improved')
    parser.add_argument('--strategy-mode', default=os.getenv('STRATEGY_MODE', 'standard'),
                       choices=['standard', 'advanced', 'quantum'],
                       help='Trading strategy mode')
    parser.add_argument('--system-mode', default=os.getenv('SYSTEM_MODE', 'full_trading'),
                       choices=['signal_only', 'scanner_only', 'full_trading', 'alert_only'],
                       help='System operation mode')
    parser.add_argument('--environment', default=os.getenv('ENVIRONMENT', 'development'),
                       choices=['development', 'production', 'sandbox'],
                       help='Deployment environment')
    parser.add_argument('--etrade-mode', default=os.getenv('ETRADE_MODE', 'demo'),
                       choices=['demo', 'live'],
                       help='ETrade trading mode (demo or live)')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 8080)),
                       help='Port for HTTP server (cloud mode)')
    parser.add_argument('--host', default=os.getenv('HOST', '0.0.0.0'),
                       help='Host for HTTP server (cloud mode)')
    parser.add_argument('--cloud-mode', action='store_true',
                       help='Enable cloud deployment mode with HTTP server')
    parser.add_argument('--enable-premarket', action='store_true',
                       help='Enable pre-market news analysis')
    parser.add_argument('--enable-confluence', action='store_true',
                       help='Enable confluence trading system')
    parser.add_argument('--enable-multi-strategy', action='store_true',
                       help='Enable multi-strategy engine')
    parser.add_argument('--enable-news-sentiment', action='store_true',
                       help='Enable news sentiment analysis')
    parser.add_argument('--enable-enhanced-signals', action='store_true',
                       help='Enable enhanced signal generation')
    parser.add_argument('--enable-production-signals', action='store_true',
                       help='Enable Production Signal Generator (THE ONE AND ONLY)')
    parser.add_argument('--enable-signal-optimization', action='store_true',
                       help='Enable signal optimization and quality monitoring')
    parser.add_argument('--log-level', default=os.getenv('LOG_LEVEL', 'INFO'),
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Set logging level')
    parser.add_argument('--max-positions', type=int, default=int(os.getenv('MAX_POSITIONS', '10')),
                       help='Maximum number of positions')
    parser.add_argument('--scan-frequency', type=int, default=int(os.getenv('SCAN_FREQUENCY', '30')),
                       help='Scan frequency in seconds')
    
    args = parser.parse_args()
    
    # Load unified configuration
    config = load_configuration(args.strategy_mode, 'live', args.environment)
    
    # Set environment variables for backward compatibility
    for key, value in config.items():
        os.environ[key] = str(value)
    
    return config, args

# --- Initialize configuration ---
try:
    CONFIG, ARGS = load_app_config()
except Exception as e:
    print(f"Failed to load configuration: {e}")
    sys.exit(1)

# --- Logging Configuration ---
def setup_logging():
    """Setup optimized logging for all environments"""
    # Get log level from args or config
    log_level = ARGS.log_level.upper() if hasattr(ARGS, 'log_level') else get_config_value("SESSION_LOG_LEVEL", "INFO").upper()
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
    
    # Console handler (required for all environments)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)
    
    # Optional file handler for local development
    if ARGS.environment == 'development' and get_config_value("FILE_LOGGING", True):
        log_path = get_config_value("LOG_PATH", "logs/signals.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    
    return logger

# --- Google Cloud Logging Setup ---
def setup_cloud_logging():
    """Setup Google Cloud Logging if available"""
    if GCP_LOGGING_AVAILABLE and ARGS.environment == 'production':
        try:
            client = gcp_logging.Client()
            client.setup_logging()
            print("Google Cloud Logging initialized")
            return True
        except Exception as e:
            print(f"Failed to initialize GCP logging: {e}")
            return False
    return False

# --- Global System Instance ---
_system_instance = None

def get_integrated_system():
    """Get or create the integrated system instance"""
    global _system_instance
    if _system_instance is None:
        # Create system configuration
        system_config = TradingConfig(
            mode=SystemMode(ARGS.system_mode),
            strategy_mode=StrategyMode(ARGS.strategy_mode),
            enable_premarket_analysis=ARGS.enable_premarket,
            enable_confluence_trading=ARGS.enable_confluence,
            enable_multi_strategy=ARGS.enable_multi_strategy,
            enable_news_sentiment=ARGS.enable_news_sentiment,
            enable_enhanced_signals=ARGS.enable_enhanced_signals,
            max_positions=ARGS.max_positions,
            scan_frequency=ARGS.scan_frequency
        )
        _system_instance = get_prime_trading_system(system_config)
    return _system_instance

# --- Health Check Endpoint ---
async def health_check():
    """Comprehensive health check endpoint using integrated system"""
    try:
        # Get integrated system instance
        system = get_integrated_system()
        
        # Get system metrics
        metrics = system.get_metrics()
        
        # Determine health status
        health_status = "healthy"
        if metrics["system_metrics"]["errors"] > 10:
            health_status = "degraded"
        if metrics["system_metrics"]["errors"] > 50:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": ARGS.environment,
            "strategy_mode": ARGS.strategy_mode,
            "system_mode": ARGS.system_mode,
            "uptime_hours": metrics["system_metrics"]["uptime_hours"],
            "current_phase": metrics["current_phase"],
            "running": metrics["running"],
            "system_metrics": metrics["system_metrics"],
            "trading_metrics": metrics["trading_metrics"],
            "scanner_metrics": metrics["scanner_metrics"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# --- HTTP Server for Cloud Mode ---
async def check_and_build_stale_watchlist():
    """Check if watchlist is stale and build a fresh one if needed"""
    logger = logging.getLogger("improved_main")
    try:
        import os
        from datetime import datetime, timedelta
        
        watchlist_path = "data/watchlist/dynamic_watchlist.csv"
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if watchlist exists and is from today
        if os.path.exists(watchlist_path):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(watchlist_path))
            file_date = file_mtime.strftime("%Y-%m-%d")
            
            if file_date == today:
                logger.info(f"✅ Watchlist is fresh (built today: {file_date})")
                return
        
        # Watchlist is stale or missing - build a fresh one
        logger.info(f"🔄 Watchlist is stale or missing (today: {today}), building fresh watchlist...")
        
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
                logger.info("✅ Fresh watchlist built successfully for mid-day initialization")
                
                # Count symbols in watchlist
                try:
                    import pandas as pd
                    df = pd.read_csv(watchlist_path)
                    symbol_count = len(df)
                    logger.info(f"📊 Watchlist contains {symbol_count} symbols")
                except:
                    symbol_count = 0
            else:
                logger.warning(f"⚠️ Watchlist build failed: {result.stderr}")
                logger.info("📋 System will use fallback symbol list")
        else:
            logger.warning(f"⚠️ Watchlist script not found: {watchlist_script}")
            logger.info("📋 System will use fallback symbol list")
            
    except Exception as e:
        logger.error(f"❌ Error checking/building watchlist: {e}")
        logger.info("📋 System will use fallback symbol list")

async def start_http_server():
    """Start HTTP server for cloud deployment"""
    try:
        try:
            from aiohttp import web
        except ImportError:
            logger = logging.getLogger("improved_main")
            logger.error("aiohttp not available. Install with: pip install aiohttp")
            return None
        
        async def handle_health(request):
            health_data = await health_check()
            status_code = 200 if health_data["status"] in ["healthy", "degraded"] else 503
            return web.json_response(health_data, status=status_code)
        
        async def handle_metrics(request):
            system = get_integrated_system()
            metrics = system.get_metrics()
            return web.json_response(metrics)
        
        async def handle_status(request):
            health_data = await health_check()
            return web.json_response(health_data)
        
        async def handle_control(request):
            """Control endpoint for system management"""
            data = await request.json()
            action = data.get('action')
            
            if action == 'shutdown':
                system = get_integrated_system()
                await system.shutdown()
                return web.json_response({"status": "shutdown_initiated"})
            elif action == 'restart':
                # Restart would be handled by the container orchestrator
                return web.json_response({"status": "restart_initiated"})
            else:
                return web.json_response({"error": "unknown_action"}, status=400)
        

        async def handle_build_watchlist(request):
            """Build fresh dynamic watchlist (triggered by Cloud Scheduler at 7 AM ET)"""
            try:
                logger = logging.getLogger("improved_main")
                logger.info("📊 Watchlist build triggered by Cloud Scheduler")
                
                import subprocess
                import os
                from datetime import datetime
                
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
                        
                        return web.json_response({
                            "status": "success",
                            "message": f"Watchlist built successfully with {symbol_count} symbols",
                            "timestamp": datetime.utcnow().isoformat(),
                            "output": result.stdout[:500]
                        })
                    else:
                        logger.error(f"❌ Watchlist build failed: {result.stderr}")
                        return web.json_response({
                            "status": "error",
                            "message": "Watchlist build failed",
                            "error": result.stderr[:500]
                        }, status=500)
                else:
                    logger.error(f"❌ Watchlist script not found: {watchlist_script}")
                    return web.json_response({
                        "status": "error",
                        "message": f"Watchlist script not found: {watchlist_script}"
                    }, status=404)
                    
            except Exception as e:
                logger = logging.getLogger("improved_main")
                logger.error(f"❌ Watchlist build endpoint error: {e}")
                return web.json_response({
                    "status": "error",
                    "message": str(e)
                }, status=500)
        
        app = web.Application()
        app.router.add_get('/health', handle_health)
        app.router.add_get('/metrics', handle_metrics)
        app.router.add_get('/status', handle_status)
        app.router.add_post('/control', handle_control)
        app.router.add_post('/api/build-watchlist', handle_build_watchlist)  # New endpoint for Cloud Scheduler
        app.router.add_get('/', handle_health)  # Root endpoint
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, ARGS.host, ARGS.port)
        await site.start()
        
        logger = logging.getLogger("improved_main")
        logger.info(f"HTTP server started on {ARGS.host}:{ARGS.port}")
        
        return runner
        
    except Exception as e:
        logger = logging.getLogger("improved_main")
        logger.error(f"Failed to start HTTP server: {e}")
        return None

# --- Graceful Shutdown ---
async def graceful_shutdown(http_runner=None, trading_task=None):
    """Graceful shutdown for all services"""
    logger = logging.getLogger("improved_main")
    logger.info("Initiating graceful shutdown...")
    
    try:
        # Cancel trading task if running
        if trading_task and not trading_task.done():
            logger.info("🛑 Stopping trading system...")
            trading_task.cancel()
            try:
                await trading_task
            except asyncio.CancelledError:
                logger.info("✅ Trading system stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping trading system: {e}")
        
        # OAuth keep-alive handled by Cloud Scheduler (no shutdown needed)
        logger.info("ℹ️  OAuth keep-alive runs automatically via Cloud Scheduler")
        
        # Shutdown HTTP server
        if http_runner:
            await http_runner.cleanup()
        
        # Shutdown integrated system
        system = get_integrated_system()
        await system.shutdown()
        
        logger.info("Graceful shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# --- Signal Handlers ---
def setup_signal_handlers(http_runner=None, trading_task=None):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger = logging.getLogger("improved_main")
        logger.info(f"Received signal {signum}, initiating shutdown...")
        
        # Create new event loop for shutdown
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(graceful_shutdown(http_runner, trading_task))
        loop.close()
        
        sys.exit(0)
    
    # Only setup signal handlers in the main thread
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        logger.info("Signal handlers setup successfully")
    except ValueError as e:
        logger.warning(f"Cannot setup signal handlers: {e} (not in main thread)")
        # In Cloud Run, signal handling is managed by the platform

# --- Main Function ---
async def main():
    """Main async function"""
    # Setup logging
    logger = setup_logging()
    
    # Setup Google Cloud logging if available
    setup_cloud_logging()
    
    # Detect cloud deployment
    is_cloud_deployment = (
        ARGS.cloud_mode or 
        os.getenv('K_SERVICE') or  # Cloud Run
        os.getenv('GAE_APPLICATION') or  # App Engine
        os.getenv('FUNCTION_NAME') or  # Cloud Functions
        os.getenv('CLOUD_RUN_JOB')  # Cloud Run Jobs
    )
    
    logger.info("🚀 Starting ETrade Strategy - Improved")
    logger.info(f"Strategy Mode: {ARGS.strategy_mode}")
    logger.info(f"System Mode: {ARGS.system_mode}")
    logger.info(f"Environment: {ARGS.environment}")
    logger.info(f"ETrade Mode: {ARGS.etrade_mode}")
    logger.info(f"Cloud Mode: {ARGS.cloud_mode}")
    logger.info(f"Cloud Deployment Detected: {is_cloud_deployment}")
    logger.info(f"Pre-market Analysis: {ARGS.enable_premarket}")
    logger.info(f"Confluence Trading: {ARGS.enable_confluence}")
    logger.info(f"Multi-Strategy: {ARGS.enable_multi_strategy}")
    logger.info(f"News Sentiment: {ARGS.enable_news_sentiment}")
    logger.info(f"Enhanced Signals: {ARGS.enable_enhanced_signals}")
    logger.info(f"Production Signals: {ARGS.enable_production_signals}")
    logger.info(f"Signal Optimization: {ARGS.enable_signal_optimization}")
    logger.info(f"OAuth Keep-Alive: Managed by Cloud Scheduler")
    
    # Initialize ETrade OAuth and Trader
    logger.info("Initializing ETrade integration...")
    try:
        # Map etrade_mode to correct environment for Secret Manager
        # 'demo' → 'sandbox', 'live' → 'prod'
        secret_manager_env = 'sandbox' if ARGS.etrade_mode == 'demo' else 'prod'
        logger.info(f"ETrade Mode: {ARGS.etrade_mode} → Secret Manager: {secret_manager_env}")
        
        etrade_oauth = get_etrade_oauth_integration(secret_manager_env)
        
        # Check OAuth status
        oauth_status = etrade_oauth.get_auth_status()
        logger.info(f"OAuth Status: {oauth_status}")
        
        if not etrade_oauth.is_authenticated():
            logger.warning("⚠️  OAuth not authenticated. Please setup tokens first.")
            logger.info(f"Run: cd modules && python3 keepalive_oauth.py {ARGS.etrade_mode}")
            if ARGS.etrade_mode == 'live':
                logger.warning("⚠️  Live trading requires proper OAuth setup")
            return
        
        logger.info("✅ OAuth authentication ready")
        
        # Use mapped environment for ETrade trader
        etrade_trader = PrimeETradeTrading(environment=secret_manager_env)
        
        if etrade_trader.initialize():
            logger.info(f"✅ ETrade {ARGS.etrade_mode} trader initialized successfully")
        else:
            logger.error(f"❌ Failed to initialize ETrade {ARGS.etrade_mode} trader")
            if ARGS.etrade_mode == 'live':
                logger.warning("⚠️  Live trading requires proper OAuth setup")
                logger.info("Run: cd modules && python3 keepalive_oauth.py prod")
                return
        
        # OAuth keep-alive handled automatically by Cloud Scheduler
        # No local keep-alive needed - Cloud Scheduler hits backend every hour
        logger.info("ℹ️  OAuth keep-alive managed by Cloud Scheduler (hourly at :00 and :30)")
    except Exception as e:
        logger.error(f"ETrade initialization failed: {e}")
        if ARGS.etrade_mode == 'live':
            logger.warning("⚠️  Live trading requires proper OAuth setup")
            logger.info("Run: cd modules && python3 keepalive_oauth.py prod")
            return
    
    http_runner = None
    
    try:
        # Create system configuration
        system_config = TradingConfig(
            mode=SystemMode(ARGS.system_mode),
            strategy_mode=StrategyMode(ARGS.strategy_mode),
            enable_premarket_analysis=ARGS.enable_premarket,
            enable_confluence_trading=ARGS.enable_confluence,
            enable_multi_strategy=ARGS.enable_multi_strategy,
            enable_news_sentiment=ARGS.enable_news_sentiment,
            enable_enhanced_signals=ARGS.enable_enhanced_signals,
            max_positions=ARGS.max_positions,
            scan_frequency=ARGS.scan_frequency
        )
        
        # Initialize prime system
        system = get_prime_trading_system(system_config)
        
        # Start HTTP server if in cloud mode
        if ARGS.cloud_mode:
            http_runner = await start_http_server()
        
        # Initialize trading task variable
        trading_task = None
        
        # Initialize system components using unified services architecture
        logger.info("🔧 Initializing system components using unified services architecture...")
        
        # Import and initialize unified services manager
        from services.unified_services_manager import UnifiedServicesManager
        
        # Create unified services manager
        services_manager = UnifiedServicesManager()
        
        # Start all services
        logger.info("🚀 Starting all Prime services...")
        services_started = services_manager.start_all_services()
        if services_started:
            logger.info("✅ All services started successfully")
        else:
            logger.warning("⚠️ Some services failed to start")
        
        # Get service components for legacy system integration
        data_service = services_manager.services.get('data_service')
        signal_service = services_manager.services.get('signal_service')
        trading_service = services_manager.services.get('trading_service')
        
        # Initialize legacy system with service components
        components = {
            'data_manager': data_service.data_manager if data_service else None,
            'signal_generator': signal_service.signal_generator if signal_service else None,
            'risk_manager': None,  # Will be initialized by system
            'trade_manager': trading_service.trading_manager if trading_service else None,
            'stealth_trailing': None,  # Will be initialized by system
            'alert_manager': None  # Will be initialized by system
        }
        
        # Initialize system with components
        logger.info("🔧 Initializing trading system with service components...")
        try:
            await system.initialize(components)
            logger.info("✅ Trading system initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize trading system: {e}")
            # Try to initialize with minimal components
            logger.info("🔄 Attempting to initialize with minimal components...")
            minimal_components = {
                'data_manager': None,
                'signal_generator': None,
                'risk_manager': None,
                'trade_manager': None,
                'stealth_trailing': None,
                'alert_manager': None
            }
            await system.initialize(minimal_components)
            logger.info("✅ Trading system initialized with minimal components")
        
        # Check for stale watchlist and build if needed
        await check_and_build_stale_watchlist()
        
        # Start trading system in background thread to avoid blocking HTTP server
        logger.info("🚀 Starting prime trading system with watchlist scanning...")
        logger.info("📊 System will build watchlist 1 hour before market open (8:30 AM ET)")
        logger.info("🔍 System will continuously scan symbols for high-quality Buy signals")
        
        # Start trading system in background task
        trading_task = asyncio.create_task(system.start())
        
        # Setup signal handlers with trading task
        setup_signal_handlers(http_runner, trading_task)
        
        logger.info("✅ Trading system started in background thread")
        
        # Keep main thread alive to handle HTTP requests
        if ARGS.cloud_mode:
            logger.info("🌐 HTTP server running, keeping main thread alive...")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received KeyboardInterrupt, shutting down...")
        else:
            # In non-cloud mode, wait for trading task to complete
            await trading_task
        
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        sys.exit(1)
    finally:
        await graceful_shutdown(http_runner, trading_task)

# --- Entry Point ---
if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
