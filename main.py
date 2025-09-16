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
from modules.production_signal_generator import get_production_signal_generator, ProductionSignalGenerator
from modules.live_trading_integration import get_live_trading_system, LiveTradingConfig
from modules.etrade_oauth_integration import get_etrade_oauth_integration
from modules.prime_etrade_trader import PrimeETradeTrader
from modules.prime_models import StrategyMode
from modules.config_loader import load_configuration, get_config_value
from modules.oauth_keepalive import start_oauth_keepalive, stop_oauth_keepalive

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
    parser.add_argument('--enable-live-trading', action='store_true',
                       help='Enable live trading system (premarket to market close)')
    parser.add_argument('--live-trading-config', type=str,
                       help='Path to live trading configuration file')
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
    # Get log level
    log_level = get_config_value("SESSION_LOG_LEVEL", "INFO").upper()
    
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
async def start_http_server():
    """Start HTTP server for cloud deployment"""
    try:
        from aiohttp import web
        
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
        
        app = web.Application()
        app.router.add_get('/health', handle_health)
        app.router.add_get('/metrics', handle_metrics)
        app.router.add_get('/status', handle_status)
        app.router.add_post('/control', handle_control)
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
async def graceful_shutdown(http_runner=None):
    """Graceful shutdown for all services"""
    logger = logging.getLogger("improved_main")
    logger.info("Initiating graceful shutdown...")
    
    try:
        # Shutdown OAuth keep-alive system
        logger.info("🛑 Stopping OAuth keep-alive system...")
        try:
            await stop_oauth_keepalive()
            logger.info("✅ OAuth keep-alive system stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping OAuth keep-alive: {e}")
        
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
def setup_signal_handlers(http_runner=None):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger = logging.getLogger("improved_main")
        logger.info(f"Received signal {signum}, initiating shutdown...")
        
        # Create new event loop for shutdown
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(graceful_shutdown(http_runner))
        loop.close()
        
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

# --- Main Function ---
async def main():
    """Main async function"""
    # Setup logging
    logger = setup_logging()
    
    # Setup Google Cloud logging if available
    setup_cloud_logging()
    
    logger.info("Starting ETrade Strategy - Improved")
    logger.info(f"Strategy Mode: {ARGS.strategy_mode}")
    logger.info(f"System Mode: {ARGS.system_mode}")
    logger.info(f"Environment: {ARGS.environment}")
    logger.info(f"ETrade Mode: {ARGS.etrade_mode}")
    logger.info(f"Cloud Mode: {ARGS.cloud_mode}")
    logger.info(f"Pre-market Analysis: {ARGS.enable_premarket}")
    logger.info(f"Confluence Trading: {ARGS.enable_confluence}")
    logger.info(f"Multi-Strategy: {ARGS.enable_multi_strategy}")
    logger.info(f"News Sentiment: {ARGS.enable_news_sentiment}")
    logger.info(f"Enhanced Signals: {ARGS.enable_enhanced_signals}")
    logger.info(f"Production Signals: {ARGS.enable_production_signals}")
    logger.info(f"Signal Optimization: {ARGS.enable_signal_optimization}")
    logger.info(f"Live Trading: {ARGS.enable_live_trading}")
    
    # Initialize ETrade OAuth and Trader
    logger.info("Initializing ETrade integration...")
    try:
        etrade_oauth = get_etrade_oauth_integration(ARGS.etrade_mode)
        
        # Check OAuth status
        oauth_status = etrade_oauth.get_auth_status()
        logger.info(f"OAuth Status: {oauth_status}")
        
        if not etrade_oauth.is_authenticated():
            logger.warning("⚠️  OAuth not authenticated. Please setup tokens first.")
            logger.info(f"Run: cd ETradeOAuth && python3 simple_oauth_cli.py start {ARGS.etrade_mode}")
            if ARGS.etrade_mode == 'live':
                logger.warning("⚠️  Live trading requires proper OAuth setup")
            return
        
        logger.info("✅ OAuth authentication ready")
        
        etrade_trader = PrimeETradeTrader(ARGS.etrade_mode)
        
        if etrade_trader.initialize():
            logger.info(f"✅ ETrade {ARGS.etrade_mode} trader initialized successfully")
        else:
            logger.error(f"❌ Failed to initialize ETrade {ARGS.etrade_mode} trader")
            if ARGS.etrade_mode == 'live':
                logger.warning("⚠️  Live trading requires proper OAuth setup")
                logger.info("Run: cd ETradeOAuth && python3 simple_oauth_cli.py start prod")
                return
        
        # Start OAuth keep-alive system
        logger.info("🔄 Starting OAuth keep-alive system...")
        try:
            keepalive_started = await start_oauth_keepalive()
            if keepalive_started:
                logger.info("✅ OAuth keep-alive system started successfully")
            else:
                logger.warning("⚠️  OAuth keep-alive system failed to start")
        except Exception as e:
            logger.error(f"❌ OAuth keep-alive system error: {e}")
            logger.warning("⚠️  Tokens may go idle without keep-alive system")
    except Exception as e:
        logger.error(f"ETrade initialization failed: {e}")
        if ARGS.etrade_mode == 'live':
            logger.warning("⚠️  Live trading requires proper OAuth setup")
            logger.info("Run: python3 scripts/setup_etrade_oauth.py")
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
        
        # Setup signal handlers
        setup_signal_handlers(http_runner)
        
        # Start live trading system if enabled
        if ARGS.enable_live_trading:
            logger.info("🚀 Starting live trading system (premarket to market close)...")
            
            # Create live trading configuration
            live_config = LiveTradingConfig()
            if ARGS.live_trading_config:
                # Load custom configuration if provided
                with open(ARGS.live_trading_config, 'r') as f:
                    config_data = json.load(f)
                    live_config = LiveTradingConfig(**config_data)
            
            # Start live trading system
            live_system = get_live_trading_system(live_config)
            await live_system.start_live_trading()
        else:
            # Start prime system
            logger.info("🚀 Starting prime trading system...")
            await system.start()
        
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        sys.exit(1)
    finally:
        await graceful_shutdown(http_runner)

# --- Entry Point ---
if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
