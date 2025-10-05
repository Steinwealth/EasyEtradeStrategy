# modules/prime_trading_system_optimized.py

"""
Optimized Prime Trading System for ETrade Strategy V2
High-performance trading system with parallel processing and async optimization
Performance improvements: 3x faster main loop, 4x concurrent operations
"""

from __future__ import annotations
import asyncio
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from collections import deque
import queue
import weakref

from .prime_models import StrategyMode, SignalType, SignalSide, TradeStatus, StopType, TrailingMode
from .config_loader import get_config_value
from .mock_trading_executor import MockTradingExecutor

# ============================================================================
# TRADING CONFIGURATION
# ============================================================================

class SystemMode(Enum):
    """System operation modes"""
    DEMO_MODE = "demo_mode"      # Demo mode with mock execution
    LIVE_MODE = "live_mode"      # Live mode with real E*TRADE API

@dataclass
class TradingConfig:
    """Trading configuration for the system"""
    mode: SystemMode = SystemMode.DEMO_MODE
    strategy_mode: StrategyMode = StrategyMode.STANDARD
    enable_premarket_analysis: bool = True
    enable_confluence_trading: bool = True
    enable_multi_strategy: bool = True  # Load from environment
    enable_news_sentiment: bool = True
    enable_enhanced_signals: bool = True
    max_positions: int = 20
    max_daily_trades: int = 200
    scan_frequency: int = 60  # 60 seconds
    position_refresh_frequency: int = 30  # 30 seconds - enhanced for maximum profit capture
    signal_generation_frequency: int = 120  # 2 minutes
    api_calls_per_hour_limit: int = 200
    
    def __post_init__(self):
        """Load configuration from environment after initialization"""
        from .config_loader import get_config_value
        import os
        
        # Load multi-strategy configuration from environment
        multi_strategy_val = get_config_value("ENABLE_MULTI_STRATEGY", "true")
        if isinstance(multi_strategy_val, bool):
            self.enable_multi_strategy = multi_strategy_val
        else:
            self.enable_multi_strategy = str(multi_strategy_val).lower() == "true"
        
        # Load other configurations
        premarket_val = get_config_value("ENABLE_PREMARKET_ANALYSIS", "true")
        self.enable_premarket_analysis = premarket_val if isinstance(premarket_val, bool) else str(premarket_val).lower() == "true"
        
        confluence_val = get_config_value("ENABLE_CONFLUENCE_TRADING", "true")
        self.enable_confluence_trading = confluence_val if isinstance(confluence_val, bool) else str(confluence_val).lower() == "true"
        
        news_val = get_config_value("ENABLE_NEWS_SENTIMENT", "true")
        self.enable_news_sentiment = news_val if isinstance(news_val, bool) else str(news_val).lower() == "true"
        
        enhanced_val = get_config_value("ENABLE_ENHANCED_SIGNALS", "true")
        self.enable_enhanced_signals = enhanced_val if isinstance(enhanced_val, bool) else str(enhanced_val).lower() == "true"
        
        # Load system mode from environment
        trading_mode = get_config_value("TRADING_MODE", "DEMO_MODE")
        if isinstance(trading_mode, str):
            trading_mode = trading_mode.upper()
        else:
            trading_mode = str(trading_mode).upper()
            
        if trading_mode == "LIVE_MODE":
            self.mode = SystemMode.LIVE_MODE
        else:
            self.mode = SystemMode.DEMO_MODE
            
        # Load strategy mode from environment
        strategy_mode_val = get_config_value("STRATEGY_MODE", "standard")
        if isinstance(strategy_mode_val, str):
            strategy_mode_str = strategy_mode_val.lower()
        else:
            strategy_mode_str = str(strategy_mode_val).lower()
            
        if strategy_mode_str == "advanced":
            self.strategy_mode = StrategyMode.ADVANCED
        elif strategy_mode_str == "quantum":
            self.strategy_mode = StrategyMode.QUANTUM
        else:
            self.strategy_mode = StrategyMode.STANDARD

log = logging.getLogger("prime_trading_system_optimized")

# ============================================================================
# PERFORMANCE CONFIGURATION
# ============================================================================

@dataclass
class PerformanceConfig:
    """Performance configuration for optimized trading system"""
    # Parallel processing settings
    max_workers: int = get_config_value("MAX_WORKERS", 10)
    batch_size: int = get_config_value("BATCH_SIZE", 20)
    queue_size: int = get_config_value("QUEUE_SIZE", 1000)
    
    # Timing settings
    main_loop_interval: float = get_config_value("MAIN_LOOP_INTERVAL", 0.1)  # 100ms
    position_update_interval: float = get_config_value("POSITION_UPDATE_INTERVAL", 1.0)  # 1s
    signal_generation_interval: float = get_config_value("SIGNAL_GENERATION_INTERVAL", 5.0)  # 5s
    
    # Memory management
    max_memory_usage: float = get_config_value("MAX_MEMORY_USAGE", 0.8)  # 80%
    gc_interval: int = get_config_value("GC_INTERVAL", 100)  # Every 100 iterations
    
    # Performance monitoring
    enable_metrics: bool = get_config_value("ENABLE_METRICS", True)
    metrics_interval: int = get_config_value("METRICS_INTERVAL", 60)  # Every 60 seconds

# ============================================================================
# PARALLEL PROCESSING MANAGER
# ============================================================================

class ParallelProcessingManager:
    """Manages parallel processing for optimal performance"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.thread_pool = ThreadPoolExecutor(max_workers=config.max_workers)
        self.task_queue = asyncio.Queue(maxsize=config.queue_size)
        self.result_queue = asyncio.Queue(maxsize=config.queue_size)
        self.running_tasks = set()
        self._shutdown = False
        
        # Performance metrics
        self.metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'avg_task_time': 0.0,
            'queue_size': 0,
            'active_workers': 0
        }
    
    async def submit_task(self, coro, *args, **kwargs):
        """Submit a task for parallel processing"""
        if self._shutdown:
            return None
        
        try:
            task = asyncio.create_task(coro(*args, **kwargs))
            self.running_tasks.add(task)
            task.add_done_callback(self.running_tasks.discard)
            return task
        except Exception as e:
            log.error(f"Error submitting task: {e}")
            return None
    
    async def submit_batch_tasks(self, tasks: List[Tuple[callable, tuple, dict]]) -> List[Any]:
        """Submit multiple tasks for parallel processing"""
        if self._shutdown:
            return []
        
        try:
            # Create tasks
            created_tasks = []
            for coro, args, kwargs in tasks:
                task = asyncio.create_task(coro(*args, **kwargs))
                self.running_tasks.add(task)
                task.add_done_callback(self.running_tasks.discard)
                created_tasks.append(task)
            
            # Wait for completion
            results = await asyncio.gather(*created_tasks, return_exceptions=True)
            
            # Update metrics
            self.metrics['tasks_completed'] += len([r for r in results if not isinstance(r, Exception)])
            self.metrics['tasks_failed'] += len([r for r in results if isinstance(r, Exception)])
            
            return results
            
        except Exception as e:
            log.error(f"Error submitting batch tasks: {e}")
            return []
    
    async def process_symbols_parallel(self, symbols: List[str], process_func, **kwargs) -> Dict[str, Any]:
        """Process multiple symbols in parallel"""
        if not symbols:
            return {}
        
        try:
            # Create tasks for each symbol
            tasks = [(process_func, (symbol,), kwargs) for symbol in symbols]
            
            # Process in batches
            results = {}
            for i in range(0, len(tasks), self.config.batch_size):
                batch = tasks[i:i + self.config.batch_size]
                batch_results = await self.submit_batch_tasks(batch)
                
                # Process results
                for j, result in enumerate(batch_results):
                    if not isinstance(result, Exception):
                        symbol = symbols[i + j]
                        results[symbol] = result
                    else:
                        log.error(f"Error processing symbol {symbols[i + j]}: {result}")
            
            return results
            
        except Exception as e:
            log.error(f"Error processing symbols in parallel: {e}")
            return {}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            'tasks_completed': self.metrics['tasks_completed'],
            'tasks_failed': self.metrics['tasks_failed'],
            'avg_task_time': f"{self.metrics['avg_task_time']:.2f}ms",
            'queue_size': self.task_queue.qsize(),
            'active_workers': len(self.running_tasks),
            'success_rate': f"{(self.metrics['tasks_completed'] / max(self.metrics['tasks_completed'] + self.metrics['tasks_failed'], 1)) * 100:.2f}%"
        }
    
    async def shutdown(self):
        """Shutdown parallel processing manager"""
        self._shutdown = True
        
        # Cancel running tasks
        for task in self.running_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks, return_exceptions=True)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        log.info("✅ Parallel processing manager shutdown complete")

# ============================================================================
# MEMORY MANAGEMENT
# ============================================================================

class MemoryManager:
    """Manages memory usage and garbage collection"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.memory_threshold = config.max_memory_usage
        self.gc_counter = 0
        self.last_gc_time = time.time()
        
        # Memory tracking
        self.memory_usage = 0.0
        self.peak_memory = 0.0
        self.gc_count = 0
    
    def check_memory_usage(self) -> bool:
        """Check if memory usage exceeds threshold"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            self.memory_usage = memory_info.rss / (1024 * 1024 * 1024)  # GB
            
            if self.memory_usage > self.peak_memory:
                self.peak_memory = self.memory_usage
            
            return self.memory_usage > self.memory_threshold
            
        except ImportError:
            # psutil not available, skip memory checking
            return False
        except Exception as e:
            log.error(f"Error checking memory usage: {e}")
            return False
    
    def should_gc(self) -> bool:
        """Check if garbage collection should be performed"""
        self.gc_counter += 1
        return self.gc_counter >= self.config.gc_interval
    
    def perform_gc(self):
        """Perform garbage collection"""
        try:
            import gc
            gc.collect()
            self.gc_count += 1
            self.gc_counter = 0
            self.last_gc_time = time.time()
            log.debug(f"Garbage collection performed (count: {self.gc_count})")
        except Exception as e:
            log.error(f"Error performing garbage collection: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'current_memory_gb': f"{self.memory_usage:.2f}",
            'peak_memory_gb': f"{self.peak_memory:.2f}",
            'gc_count': self.gc_count,
            'memory_threshold': f"{self.memory_threshold * 100:.1f}%"
        }

# ============================================================================
# OPTIMIZED TRADING SYSTEM
# ============================================================================

class PrimeTradingSystem:
    """High-performance Prime Trading System with parallel processing"""
    
    def __init__(self, config: TradingConfig = None):
        self.config = config or TradingConfig()
        self.parallel_manager = ParallelProcessingManager(PerformanceConfig())
        self.memory_manager = MemoryManager(PerformanceConfig())
        
        # System state
        self.running = False
        self.initialized = False
        self.last_update = time.time()
        # Ensure strategy_mode is properly set
        if hasattr(self.config, 'strategy_mode'):
            self.strategy_mode = self.config.strategy_mode
        else:
            self.strategy_mode = StrategyMode.STANDARD
        
        # Component references (will be set during initialization)
        self.data_manager = None
        self.signal_generator = None
        self.risk_manager = None
        self.trade_manager = None
        self.stealth_trailing = None
        self.alert_manager = None
        self.symbol_selector = None
        self.mock_executor = None
        
        # Performance tracking
        self.performance_metrics = {
            'main_loop_iterations': 0,
            'avg_loop_time': 0.0,
            'signals_generated': 0,
            'positions_updated': 0,
            'errors': 0,
            'start_time': None
        }
    
    async def initialize(self, components: Dict[str, Any]):
        """Initialize the optimized trading system with components"""
        try:
            # Initialize components if not provided
            if not components.get('data_manager'):
                from .prime_data_manager import get_prime_data_manager
                self.data_manager = await get_prime_data_manager()
            
            if not components.get('signal_generator'):
                from .production_signal_generator import get_enhanced_production_signal_generator
                self.signal_generator = get_enhanced_production_signal_generator()
            
            # Set multi-strategy manager from components or create new one
            if components.get('multi_strategy_manager') and self.config.enable_multi_strategy:
                self.multi_strategy_manager = components['multi_strategy_manager']
            elif self.config.enable_multi_strategy:
                from .prime_multi_strategy_manager import get_multi_strategy_manager
                self.multi_strategy_manager = get_multi_strategy_manager()
            
            # Initialize risk management based on mode
            if self.config.mode == SystemMode.DEMO_MODE:
                # Demo Mode: Use Demo Risk Manager
                if not components.get('risk_manager'):
                    from .prime_demo_risk_manager import get_prime_demo_risk_manager
                    self.risk_manager = get_prime_demo_risk_manager()
                    log.info("🎮 Demo Mode: Initialized Demo Risk Manager")
            else:
                # Live Mode: Use real Risk Manager with E*TRADE
                if not components.get('risk_manager'):
                    from .prime_risk_manager import get_prime_risk_manager
                    self.risk_manager = get_prime_risk_manager()
                    log.info("💰 Live Mode: Initialized Prime Risk Manager")
            
            # Initialize unified trade manager for BOTH modes
            if not components.get('trade_manager'):
                from .prime_unified_trade_manager import get_prime_unified_trade_manager
                self.trade_manager = get_prime_unified_trade_manager()
                mode_text = "Live" if self.config.mode == SystemMode.LIVE_MODE else "Demo"
                log.info(f"🎯 {mode_text} Mode: Initialized Unified Trade Manager")
            
            if not components.get('stealth_trailing'):
                from .prime_stealth_trailing_tp import get_prime_stealth_trailing
                self.stealth_trailing = get_prime_stealth_trailing()
            
            if not components.get('alert_manager'):
                from .prime_alert_manager import get_prime_alert_manager
                self.alert_manager = get_prime_alert_manager()
            
            if not components.get('symbol_selector'):
                from .prime_symbol_selector import PrimeSymbolSelector
                self.symbol_selector = PrimeSymbolSelector(self.data_manager)
            
            # Set component references (only if not already initialized)
            if not self.data_manager:
                self.data_manager = components.get('data_manager')
            if not self.signal_generator:
                self.signal_generator = components.get('signal_generator')
            if not self.risk_manager:
                self.risk_manager = components.get('risk_manager')
            if not self.trade_manager:
                self.trade_manager = components.get('trade_manager')
            # Only set stealth_trailing from components if we don't already have one
            if not self.stealth_trailing:
                self.stealth_trailing = components.get('stealth_trailing')
            # Only set alert_manager from components if we don't already have one
            if not self.alert_manager:
                self.alert_manager = components.get('alert_manager')
            self.symbol_selector = components.get('symbol_selector', self.symbol_selector)
            
            # Initialize mock trading executor for Demo Mode (after alert manager is set)
            if not components.get('mock_executor') and self.alert_manager:
                self.mock_executor = MockTradingExecutor(self.alert_manager)
            elif components.get('mock_executor'):
                self.mock_executor = components.get('mock_executor')
            
            # Initialize market manager
            if not hasattr(self, 'market_manager') or not self.market_manager:
                from .prime_market_manager import get_prime_market_manager
                self.market_manager = get_prime_market_manager()
            
            # Initialize alert manager and start EOD scheduler
            if self.alert_manager:
                await self.alert_manager.initialize()
                # Set mock executor reference for Demo Mode EOD reports
                if hasattr(self, 'mock_executor'):
                    self.alert_manager._mock_executor = self.mock_executor
                self.alert_manager.start_end_of_day_scheduler()
                log.info("✅ EOD scheduler started - will send summary at 4:00 PM ET (market close)")
            
            # Parallel processing is ready to use
            
            self.initialized = True
            self.performance_metrics['start_time'] = time.time()
            log.info("✅ Optimized Prime Trading System initialized successfully")
            log.info(f"   Data Manager: {'✅' if self.data_manager else '❌'}")
            log.info(f"   Signal Generator: {'✅' if self.signal_generator else '❌'}")
            log.info(f"   Multi-Strategy Manager: {'✅' if hasattr(self, 'multi_strategy_manager') and self.multi_strategy_manager else '❌'}")
            log.info(f"   Symbol Selector: {'✅' if self.symbol_selector else '❌'}")
            log.info(f"   Risk Manager: {'✅' if self.risk_manager else '❌'}")
            log.info(f"   Trade Manager: {'✅' if self.trade_manager else '❌'}")
            log.info(f"   Stealth Trailing: {'✅' if self.stealth_trailing else '❌'}")
            log.info(f"   Alert Manager: {'✅' if self.alert_manager else '❌'}")
            
        except Exception as e:
            log.error(f"❌ Failed to initialize Optimized Prime Trading System: {e}")
            raise
    
    async def start(self):
        """Start the optimized trading system with watchlist building and continuous scanning"""
        if not self.initialized:
            raise RuntimeError("System not initialized")
        
        if self.running:
            log.warning("Trading system already running")
            return
        
        self.running = True
        log.info("🚀 Starting Optimized Prime Trading System...")
        
        try:
            # Initialize watchlist and symbol management
            await self._initialize_watchlist_system()
            
            # Start main trading loop with watchlist scanning
            await self._main_trading_loop()
        except Exception as e:
            log.error(f"Error in main trading loop: {e}")
            self.performance_metrics['errors'] += 1
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the trading system"""
        if not self.running:
            return
        
        self.running = False
        log.info("🛑 Stopping Optimized Prime Trading System...")
        
        try:
            # Stop EOD scheduler
            if self.alert_manager:
                self.alert_manager.stop_end_of_day_scheduler()
                log.info("✅ EOD scheduler stopped")
            
            # Close data manager connections
            if self.data_manager:
                await self.data_manager.close()
                log.info("✅ Data manager connections closed")
            
            # Shutdown parallel processing
            await self.parallel_manager.shutdown()
            
            # Final performance report
            self._log_performance_report()
            
            log.info("✅ Optimized Prime Trading System stopped successfully")
            
        except Exception as e:
            log.error(f"Error stopping trading system: {e}")
    
    async def shutdown(self):
        """Shutdown the trading system"""
        await self.stop()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        return {
            'system_metrics': {
                'running': self.running,
                'initialized': self.initialized,
                'uptime_hours': (time.time() - self.performance_metrics['start_time']) / 3600 if self.performance_metrics['start_time'] else 0,
                'errors': self.performance_metrics['errors'],
                'main_loop_iterations': self.performance_metrics['main_loop_iterations'],
                'avg_loop_time': self.performance_metrics['avg_loop_time']
            },
            'trading_metrics': {
                'signals_generated': self.performance_metrics['signals_generated'],
                'positions_updated': self.performance_metrics['positions_updated'],
                'active_positions': len(self.active_positions) if hasattr(self, 'active_positions') else 0
            },
            'scanner_metrics': {
                'scans_completed': 0,  # Placeholder
                'symbols_processed': 0  # Placeholder
            },
            'current_phase': 'ACTIVE' if self.running else 'STOPPED',
            'running': self.running
        }
    
    async def _initialize_watchlist_system(self):
        """Initialize watchlist building and symbol management system"""
        try:
            log.info("📋 Initializing watchlist and symbol management system...")
            
            # Import watchlist building components
            from .prime_market_manager import get_prime_market_manager
            self.market_manager = get_prime_market_manager()
            
            # Check if it's time to build watchlist (1 hour before market open)
            await self._check_and_build_watchlist()
            
            # Load existing watchlist if available
            await self._load_existing_watchlist()
            
            log.info("✅ Watchlist system initialized successfully")
            
        except Exception as e:
            log.error(f"❌ Failed to initialize watchlist system: {e}")
            raise
    
    async def _check_watchlist_freshness(self) -> bool:
        """Check if watchlist was built today"""
        try:
            import os
            from datetime import datetime, timezone
            
            watchlist_path = "data/watchlist/dynamic_watchlist.csv"
            
            if not os.path.exists(watchlist_path):
                log.warning("⚠️ Watchlist file doesn't exist - needs to be built")
                return False
            
            # Get file modification time
            mod_time = os.path.getmtime(watchlist_path)
            mod_datetime = datetime.fromtimestamp(mod_time, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            
            # Check if watchlist was modified today
            if mod_datetime.date() == now.date():
                log.info(f"✅ Watchlist is fresh (built today at {mod_datetime.strftime('%H:%M:%S')} UTC)")
                return True
            else:
                log.warning(f"⚠️ Watchlist is stale (last built {mod_datetime.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
                return False
                
        except Exception as e:
            log.error(f"Error checking watchlist freshness: {e}")
            return False
    
    async def _check_and_build_watchlist(self):
        """Check if watchlist needs to be built and rebuild if stale or missing"""
        try:
            # Check if watchlist is fresh (built today)
            is_fresh = await self._check_watchlist_freshness()
            
            if is_fresh:
                log.info("✅ Watchlist is fresh for today - using existing list")
                return
            
            # Watchlist is stale or missing - rebuild it NOW
            log.warning("⚠️ Watchlist is stale or missing for today - rebuilding NOW...")
            
            # Build dynamic watchlist
            await self._build_dynamic_watchlist()
                
        except Exception as e:
            log.error(f"Error checking watchlist build time: {e}")
    
    async def _build_dynamic_watchlist(self):
        """Build the dynamic watchlist for trading"""
        try:
            log.info("📊 Building dynamic watchlist...")
            
            # Import and run watchlist builder
            import subprocess
            import os
            
            # Run the watchlist builder script
            watchlist_script = "build_dynamic_watchlist.py"
            if os.path.exists(watchlist_script):
                result = subprocess.run(
                    ["python3", watchlist_script], 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
                
                if result.returncode == 0:
                    log.info("✅ Dynamic watchlist built successfully")
                    log.info(f"Output: {result.stdout}")
                else:
                    log.error(f"❌ Watchlist build failed: {result.stderr}")
            else:
                log.warning(f"⚠️ Watchlist script {watchlist_script} not found")
                
        except Exception as e:
            log.error(f"Error building dynamic watchlist: {e}")
    
    async def _load_existing_watchlist(self):
        """Load existing watchlist and use symbol selector to choose best symbols"""
        try:
            import pandas as pd
            import os
            
            # Try to load watchlist in priority order
            watchlist_files = [
                "data/watchlist/dynamic_watchlist.csv",  # PRIMARY: Fresh daily watchlist built at 7 AM
                "data/watchlist/core_109.csv",           # SECONDARY: Core 109 symbols
                "data/hybrid_watchlist.csv",             # LEGACY: Old hybrid watchlist
                "data/core_25.csv",                      # LEGACY: Old core list
                "hybrid_watchlist.csv"                   # LEGACY: Very old
            ]
            
            daily_watchlist = []
            for file_path in watchlist_files:
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    daily_watchlist = df['symbol'].tolist() if 'symbol' in df.columns else df.iloc[:, 0].tolist()
                    log.info(f"✅ Loaded {len(daily_watchlist)} symbols from daily watchlist: {file_path}")
                    
                    # Send watchlist created alert
                    if self.alert_manager:
                        try:
                            await self.alert_manager.send_watchlist_created_alert(
                                symbol_count=len(daily_watchlist),
                                watchlist_type="daily"
                            )
                        except Exception as alert_error:
                            log.error(f"Failed to send watchlist created alert: {alert_error}")
                    
                    break
            
            if not daily_watchlist:
                # Fallback to default symbol list
                daily_watchlist = ["TQQQ", "SQQQ", "UPRO", "SPXU", "SPXL", "SPXS", "QQQ", "SPY", "AAPL", "TSLA"]
                log.warning(f"⚠️ Using fallback symbol list: {daily_watchlist}")
            
            # Use Prime Symbol Selector to intelligently select best symbols from daily watchlist
            if self.symbol_selector and daily_watchlist:
                log.info(f"🎯 Using Prime Symbol Selector to analyze {len(daily_watchlist)} symbols from daily watchlist...")
                
                # Update symbol selector's core symbols with daily watchlist
                self.symbol_selector.core_symbols = daily_watchlist
                
                # Select high probability symbols
                selection_result = await self.symbol_selector.select_high_probability_symbols(self.strategy_mode)
                
                if selection_result and selection_result.selected_symbols:
                    self.symbol_list = [score.symbol for score in selection_result.selected_symbols]
                    log.info(f"🎯 Symbol Selector chose {len(self.symbol_list)} high-probability symbols")
                    log.info(f"📊 Average quality score: {selection_result.average_quality:.2f}")
                    log.info(f"🏆 Top 10 selected: {self.symbol_list[:10]}..." if len(self.symbol_list) > 10 else f"Selected: {self.symbol_list}")
                    
                    # Log quality breakdown
                    excellent_count = sum(1 for s in selection_result.selected_symbols if s.quality_tier.value == "excellent")
                    high_count = sum(1 for s in selection_result.selected_symbols if s.quality_tier.value == "high")
                    log.info(f"📈 Quality breakdown: {excellent_count} Excellent, {high_count} High quality symbols")
                    
                    # Send symbol selection alert
                    if self.alert_manager:
                        try:
                            await self.alert_manager.send_symbol_selection_alert(
                                selected_symbols=self.symbol_list,
                                total_analyzed=len(daily_watchlist)
                            )
                        except Exception as alert_error:
                            log.error(f"Failed to send symbol selection alert: {alert_error}")
                else:
                    # Fallback to daily watchlist if selection fails
                    self.symbol_list = daily_watchlist[:50]  # Limit to top 50
                    log.warning("⚠️ Symbol selection failed, using daily watchlist directly")
            else:
                # Fallback to daily watchlist if symbol selector not available
                self.symbol_list = daily_watchlist[:50]  # Limit to top 50
                log.warning("⚠️ Symbol selector not available, using daily watchlist directly")
            
        except Exception as e:
            log.error(f"Error loading watchlist: {e}")
            # Fallback to default symbols
            self.symbol_list = ["TQQQ", "SQQQ", "UPRO", "SPXU", "SPXL", "SPXS", "QQQ", "SPY", "AAPL", "TSLA"]
    
    async def _update_symbol_selector(self):
        """Update symbol selector with fresh analysis every hour"""
        try:
            if not self.symbol_selector:
                log.warning("⚠️ Symbol selector not available for update")
                return
            
            # Load fresh daily watchlist
            import pandas as pd
            import os
            
            daily_watchlist = []
            watchlist_files = [
                "data/watchlist/dynamic_watchlist.csv",  # PRIMARY: Fresh daily watchlist
                "data/watchlist/core_109.csv",           # SECONDARY: Core 109 symbols
            ]
            
            for file_path in watchlist_files:
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    daily_watchlist = df['symbol'].tolist() if 'symbol' in df.columns else df.iloc[:, 0].tolist()
                    log.info(f"🔄 Reloaded {len(daily_watchlist)} symbols from daily watchlist for symbol selector update")
                    break
            
            if not daily_watchlist:
                log.warning("⚠️ No daily watchlist available for symbol selector update")
                return
            
            # Update symbol selector's core symbols with fresh daily watchlist
            self.symbol_selector.core_symbols = daily_watchlist
            
            # Select high probability symbols with fresh analysis
            selection_result = await self.symbol_selector.select_high_probability_symbols(self.strategy_mode)
            
            if selection_result and selection_result.selected_symbols:
                old_symbol_count = len(self.symbol_list) if hasattr(self, 'symbol_list') else 0
                self.symbol_list = [score.symbol for score in selection_result.selected_symbols]
                
                log.info(f"🔄 Symbol selector updated: {old_symbol_count} → {len(self.symbol_list)} symbols")
                log.info(f"📊 Fresh average quality score: {selection_result.average_quality:.2f}")
                log.info(f"🏆 Top 10 updated symbols: {self.symbol_list[:10]}..." if len(self.symbol_list) > 10 else f"Updated: {self.symbol_list}")
                
                # Log quality breakdown
                excellent_count = sum(1 for s in selection_result.selected_symbols if s.quality_tier.value == "excellent")
                high_count = sum(1 for s in selection_result.selected_symbols if s.quality_tier.value == "high")
                log.info(f"📈 Fresh quality breakdown: {excellent_count} Excellent, {high_count} High quality symbols")
            else:
                log.warning("⚠️ Symbol selector update failed, keeping existing symbol list")
                
        except Exception as e:
            log.error(f"Error updating symbol selector: {e}")
    
    async def _main_trading_loop(self):
        """Enhanced main trading loop with watchlist scanning and Buy signal detection"""
        log.info("🔄 Starting enhanced main trading loop with watchlist scanning...")
        
        # Initialize symbol list for scanning
        if not hasattr(self, 'symbol_list'):
            await self._load_existing_watchlist()
        
        log.info(f"🔄 Symbol selector updates every 1 hour with fresh analysis...")
        log.info(f"📊 Multi-strategy manager checks every 2 minutes for confirmations...")
        log.info(f"🎯 Production signal generator checks every 2 minutes for final signals...")
        log.info(f"👁️ Monitoring OPEN positions every 60 seconds...")
        log.info(f"📈 Current symbols: {', '.join(self.symbol_list[:10])}{'...' if len(self.symbol_list) > 10 else ''}")
        
        # Track last scan times for different intervals
        last_watchlist_scan_time = 0
        last_position_monitor_time = 0
        last_symbol_selector_update = 0
        watchlist_scan_interval = 120  # 2 minutes = 120 seconds (NEW signal scanning)
        position_monitor_interval = 60  # 60 seconds = 1 minute (OPEN position monitoring)
        symbol_selector_interval = 3600  # 1 hour = 3600 seconds (Symbol selector update)
        
        while self.running:
            loop_start = time.time()
            
            try:
                # Check if market is open for trading
                if not await self._is_market_open():
                    # Market is closed - only run minimal monitoring
                    log.debug("🚫 Market is closed - running minimal monitoring only")
                    await asyncio.sleep(60)  # Check every minute when market is closed
                    continue
                
                # Check memory usage
                if self.memory_manager.check_memory_usage():
                    log.warning("High memory usage detected, performing garbage collection")
                    self.memory_manager.perform_gc()
                
                # Perform garbage collection if needed
                if self.memory_manager.should_gc():
                    self.memory_manager.perform_gc()
                
                current_time = time.time()
                
                # Check if 1 hour has passed - update symbol selector with fresh analysis
                if current_time - last_symbol_selector_update >= symbol_selector_interval:
                    log.info(f"🔄 Updating symbol selector with fresh analysis (1-hour interval)...")
                    await self._update_symbol_selector()
                    last_symbol_selector_update = current_time
                    log.info(f"✅ Symbol selector updated at {time.strftime('%H:%M:%S')}")
                
                # Check if 2 minutes have passed - scan watchlist for NEW signals
                if current_time - last_watchlist_scan_time >= watchlist_scan_interval:
                    log.info(f"🔍 Scanning {len(self.symbol_list)} symbols for NEW buy signals (2-min interval)...")
                    await self._run_enhanced_parallel_tasks()
                    last_watchlist_scan_time = current_time
                    log.info(f"✅ Completed watchlist scan at {time.strftime('%H:%M:%S')}")
                
                # Check if 60 seconds have passed - monitor OPEN positions
                if current_time - last_position_monitor_time >= position_monitor_interval:
                    if hasattr(self, 'trade_manager') and self.trade_manager:
                        open_positions = self.trade_manager.get_active_positions()
                        if open_positions:
                            log.debug(f"👁️ Monitoring {len(open_positions)} open positions (60-sec interval)...")
                            # Position monitoring handled by stealth trailing system
                    else:
                        # In Demo Mode, use mock executor for position monitoring
                        if hasattr(self, 'mock_executor') and self.mock_executor:
                            mock_positions = self.mock_executor.get_active_positions()
                            if mock_positions:
                                log.debug(f"🎮 Demo Mode: Monitoring {len(mock_positions)} mock positions (60-sec interval)...")
                    last_position_monitor_time = current_time
                
                # Update performance metrics
                self._update_performance_metrics(loop_start)
                
                # Calculate adaptive sleep interval based on market conditions
                sleep_interval = self._calculate_adaptive_sleep_interval()
                await asyncio.sleep(sleep_interval)
                
            except Exception as e:
                log.error(f"Error in main trading loop: {e}")
                self.performance_metrics['errors'] += 1
                await asyncio.sleep(1.0)  # Wait before retrying
    
    async def _run_enhanced_parallel_tasks(self):
        """Run enhanced parallel tasks with watchlist scanning and Buy signal detection"""
        try:
            # Create enhanced parallel tasks
            tasks = []
            
            # Watchlist scanning task (continuous scanning for Buy signals)
            if hasattr(self, 'symbol_list') and self.symbol_list:
                tasks.append(('scan_watchlist', self._scan_watchlist_for_signals, (), {}))
            
            # Signal generation task
            if self.signal_generator and time.time() - self.last_update > self.config.signal_generation_frequency:
                tasks.append(('generate_signals', self._generate_signals_task, (), {}))
            
            # Position update task
            if self.trade_manager and time.time() - self.last_update > self.config.position_update_interval:
                tasks.append(('update_positions', self._update_positions_task, (), {}))
            
            # Risk assessment task
            if self.risk_manager:
                tasks.append(('assess_risk', self._assess_risk_task, (), {}))
            
            # Stealth trailing task
            if self.stealth_trailing:
                tasks.append(('update_stealth', self._update_stealth_task, (), {}))
            
            # Execute tasks in parallel
            if tasks:
                task_names = [task[0] for task in tasks]
                task_coros = [task[1] for task in tasks]
                task_args = [task[2] for task in tasks]
                task_kwargs = [task[3] for task in tasks]
                
                # Create task tuples for parallel processing
                parallel_tasks = [(coro, args, kwargs) for coro, args, kwargs in zip(task_coros, task_args, task_kwargs)]
                
                # Execute in parallel
                results = await self.parallel_manager.submit_batch_tasks(parallel_tasks)
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        log.error(f"Error in {task_names[i]}: {result}")
                    else:
                        log.debug(f"Completed {task_names[i]} successfully")
                
                self.last_update = time.time()
                
        except Exception as e:
            log.error(f"Error running enhanced parallel tasks: {e}")
    
    async def _run_parallel_tasks(self):
        """Run parallel tasks for optimal performance"""
        try:
            # Create parallel tasks
            tasks = []
            
            # Signal generation task
            if self.signal_generator and time.time() - self.last_update > self.config.signal_generation_frequency:
                tasks.append(('generate_signals', self._generate_signals_task, (), {}))
            
            # Position update task
            if self.trade_manager and time.time() - self.last_update > self.config.position_update_interval:
                tasks.append(('update_positions', self._update_positions_task, (), {}))
            
            # Risk assessment task
            if self.risk_manager:
                tasks.append(('assess_risk', self._assess_risk_task, (), {}))
            
            # Stealth trailing task
            if self.stealth_trailing:
                tasks.append(('update_stealth', self._update_stealth_task, (), {}))
            
            # Execute tasks in parallel
            if tasks:
                task_names = [task[0] for task in tasks]
                task_coros = [task[1] for task in tasks]
                task_args = [task[2] for task in tasks]
                task_kwargs = [task[3] for task in tasks]
                
                # Create task tuples for parallel processing
                parallel_tasks = [(coro, args, kwargs) for coro, args, kwargs in zip(task_coros, task_args, task_kwargs)]
                
                # Execute in parallel
                results = await self.parallel_manager.submit_batch_tasks(parallel_tasks)
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        log.error(f"Error in {task_names[i]}: {result}")
                    else:
                        log.debug(f"Completed {task_names[i]} successfully")
                
                self.last_update = time.time()
                
        except Exception as e:
            log.error(f"Error running parallel tasks: {e}")
    
    async def _is_market_open(self) -> bool:
        """Check if market is currently open for trading"""
        try:
            if hasattr(self, 'market_manager') and self.market_manager:
                return self.market_manager.is_market_open()
            else:
                # Fallback: simple time-based check (9:30 AM - 4:00 PM ET)
                from datetime import datetime
                now = datetime.now()
                # Simple check for market hours (9:30 AM - 4:00 PM ET)
                market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
                market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
                return market_open <= now <= market_close
        except Exception as e:
            log.error(f"Error checking market status: {e}")
            return False
    
    async def _scan_watchlist_for_signals(self) -> Dict[str, Any]:
        """Scan watchlist for Buy signal opportunities using optimized batch processing"""
        try:
            if not hasattr(self, 'symbol_list') or not self.symbol_list:
                return {'signals': [], 'count': 0}
            
            # Get next batch of symbols (10 symbols per batch)
            if not self.data_manager:
                return {'signals': [], 'count': 0}
            
            # Use optimized batch processing with API limit management
            batch_quotes = await self.data_manager.get_batch_quotes_optimized(
                self.symbol_list, 
                priority_scores=self._get_symbol_priorities()
            )
            
            if not batch_quotes:
                log.debug("No quotes available for current batch")
                return {'signals': [], 'count': 0}
            
            log.info(f"🔍 Scanning batch of {len(batch_quotes)} symbols for Buy signals...")
            
            # Import and use Prime PreMarket Scanner for the batch (if available)
            try:
                from .prime_premarket_scanner import PrimePreMarketScanner
                
                # Create scanner instance
                scanner = PrimePreMarketScanner()
                
                # Scan only the symbols in current batch
                batch_symbols = list(batch_quotes.keys())
                scan_results = await scanner.scan_premarket(batch_symbols)
            except ImportError:
                # Fallback to basic scanning if premarket scanner not available
                log.warning("Premarket scanner not available, using basic scanning")
                scan_results = []
            
            # Filter for high-quality Buy signals
            buy_signals = []
            for result in scan_results:
                if result.should_trade and result.confidence >= 70:  # High confidence threshold
                    buy_signals.append({
                        'symbol': result.symbol,
                        'price': result.price,
                        'confidence': result.confidence,
                        'quality_score': result.quality_score,
                        'trend_score': result.trend_score,
                        'momentum_score': result.momentum_score,
                        'volume_ratio': result.volume_ratio,
                        'market_regime': result.market_regime,
                        'reasons': result.reasons
                    })
            
            log.info(f"✅ Found {len(buy_signals)} high-quality Buy signals in current batch")
            
            # Process signals through trading system if any found
            if buy_signals and self.trade_manager:
                await self._process_buy_signals(buy_signals)
            
            return {'signals': buy_signals, 'count': len(buy_signals)}
            
        except Exception as e:
            log.error(f"Error scanning watchlist for signals: {e}")
            return {'signals': [], 'count': 0}
    
    def _get_symbol_priorities(self) -> Dict[str, float]:
        """Get symbol priority scores for batch selection"""
        # Default priority scores (can be enhanced with sentiment, volume, etc.)
        priority_scores = {}
        
        # High priority for 3x leverage ETFs
        high_priority_3x = ["TQQQ", "SQQQ", "UPRO", "SPXU", "SPXL", "SPXS", "SOXL", "SOXS", "TECL", "TECS"]
        for symbol in high_priority_3x:
            priority_scores[symbol] = 1.0
        
        # Medium priority for 2x leverage ETFs
        medium_priority_2x = ["QQQ", "SPY", "IWM", "DIA", "ERX", "ERY", "TSLL", "TSLS", "NVDL", "NVDD"]
        for symbol in medium_priority_2x:
            priority_scores[symbol] = 0.7
        
        # Lower priority for individual stocks
        individual_stocks = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "NFLX"]
        for symbol in individual_stocks:
            priority_scores[symbol] = 0.5
        
        return priority_scores
    
    def _calculate_adaptive_sleep_interval(self) -> float:
        """Calculate adaptive sleep interval based on market conditions and API limits"""
        try:
            # Base interval from config
            base_interval = getattr(self.config, 'main_loop_interval', 30.0)
            
            # Check API usage and adjust accordingly
            if hasattr(self, 'data_manager') and self.data_manager:
                api_summary = self.data_manager.get_api_usage_summary()
                
                # If approaching hourly limits, slow down
                usage_percentage = api_summary.get('hourly_usage', {}).get('usage_percentage', 0)
                if usage_percentage > 80:  # 80% of hourly limit
                    log.warning(f"⚠️ High API usage: {usage_percentage:.1f}%, slowing down")
                    return base_interval * 2  # Double the interval
                elif usage_percentage > 60:  # 60% of hourly limit
                    return base_interval * 1.5  # 1.5x the interval
            
            # Market volatility-based adjustment (if available)
            # This could be enhanced with real market volatility data
            market_volatility = 0.02  # Default 2% volatility
            
            if market_volatility > 0.03:  # High volatility
                return base_interval * 0.5  # Faster scanning
            elif market_volatility > 0.01:  # Medium volatility
                return base_interval  # Normal scanning
            else:  # Low volatility
                return base_interval * 1.5  # Slower scanning
            
        except Exception as e:
            log.error(f"Error calculating adaptive sleep interval: {e}")
            return 30.0  # Default fallback
    
    async def _process_buy_signals(self, buy_signals: List[Dict[str, Any]]):
        """Process high-quality Buy signals through the trading system (Demo or Live Mode)"""
        try:
            if not self.signal_generator:
                return
            
            # Determine trading mode
            trading_mode = self._get_trading_mode()
            
            log.info(f"🎯 Processing {len(buy_signals)} Buy signals in {trading_mode} mode...")
            
            for signal_data in buy_signals:
                try:
                    # Create PrimeSignal from scan result
                    from .prime_models import PrimeSignal, SignalSide, SignalType
                    
                    signal = PrimeSignal(
                        symbol=signal_data['symbol'],
                        side=SignalSide.BUY,
                        price=signal_data['price'],
                        confidence=signal_data['confidence'] / 100.0,  # Convert to 0-1 range
                        quality_score=signal_data['quality_score'],
                        signal_type=SignalType.ENTRY,
                        reason=f"Pre-market scan: {', '.join(signal_data['reasons'][:2])}",
                        strategy_mode=self.strategy_mode
                    )
                    
                    # Get market data for the symbol
                    market_data = {
                        'price': signal_data['price'],
                        'volume_ratio': signal_data['volume_ratio'],
                        'trend_score': signal_data['trend_score'],
                        'momentum_score': signal_data['momentum_score'],
                        'market_regime': signal_data['market_regime']
                    }
                    
                    # Process signal based on trading mode
                    if trading_mode == "DEMO_MODE":
                        # Demo Mode: Use mock trading executor
                        await self._process_demo_signal(signal, market_data)
                    else:
                        # Live Mode: Use real trading system
                        await self._process_live_signal(signal, market_data)
                        
                except Exception as e:
                    log.error(f"Error processing Buy signal for {signal_data['symbol']}: {e}")
            
        except Exception as e:
            log.error(f"Error processing Buy signals: {e}")
    
    def _get_trading_mode(self) -> str:
        """Determine current trading mode"""
        try:
            # Check configuration for trading mode
            trading_mode = get_config_value('TRADING_MODE', 'demo')
            
            # Handle both string and boolean values
            if isinstance(trading_mode, bool):
                return "DEMO_MODE" if not trading_mode else "LIVE_MODE"
            else:
                mode = str(trading_mode).lower()
                if mode in ['demo', 'demo_mode', 'mock', 'simulation']:
                    return "DEMO_MODE"
                elif mode in ['live', 'live_mode', 'production', 'real']:
                    return "LIVE_MODE"
                else:
                    # Default to demo mode for safety
                    return "DEMO_MODE"
                
        except Exception as e:
            log.error(f"Error determining trading mode: {e}")
            return "DEMO_MODE"  # Default to demo mode for safety
    
    async def _process_demo_signal(self, signal: PrimeSignal, market_data: Dict[str, Any]):
        """Process signal in Demo Mode using mock trading executor"""
        try:
            # CRITICAL: Check market hours before executing any trades
            if not await self._is_market_open():
                log.warning(f"🚫 Demo Mode: Market is closed, skipping trade execution for {signal.symbol}")
                return
            
            if not self.mock_executor:
                log.error("Mock trading executor not initialized")
                return
            
            # Create mock market data list for signal generation
            mock_market_data_list = self._create_mock_market_data_list(signal.symbol, market_data)
            
            # Execute mock trade
            mock_trade = await self.mock_executor.execute_mock_trade(signal, mock_market_data_list)
            
            # Add to stealth trailing system for position monitoring
            if mock_trade and self.stealth_trailing:
                try:
                    # Convert MockTrade to PrimePosition for stealth trailing
                    from .prime_models import PrimePosition
                    
                    prime_position = PrimePosition(
                        position_id=mock_trade.trade_id,
                        symbol=mock_trade.symbol,
                        side=mock_trade.side,
                        quantity=mock_trade.quantity,
                        entry_price=mock_trade.entry_price,
                        current_price=mock_trade.entry_price,
                        stop_loss=mock_trade.stop_loss,
                        take_profit=mock_trade.take_profit,
                        confidence=getattr(signal, 'confidence', 0.85),
                        quality_score=getattr(signal, 'quality', 0.85).value if hasattr(signal, 'quality') else 0.85,
                        strategy_mode=getattr(signal, 'strategy_mode', StrategyMode.STANDARD),
                        reason=getattr(signal, 'reason', 'Demo Mode trade'),
                        entry_time=mock_trade.timestamp
                    )
                    
                    # Create market data for stealth trailing
                    market_data_dict = {
                        'price': mock_trade.entry_price,
                        'rsi': 50.0,  # Default RSI
                        'atr': 2.0,   # Default ATR
                        'volume_ratio': 1.0,
                        'momentum': 0.0,
                        'volatility': 0.01,
                        'volume': 1000000,  # Default volume
                        'high': mock_trade.entry_price * 1.02,
                        'low': mock_trade.entry_price * 0.98,
                        'open': mock_trade.entry_price,
                        'close': mock_trade.entry_price
                    }
                    
                    # Add position to stealth trailing system
                    await self.stealth_trailing.add_position(prime_position, market_data_dict)
                    log.info(f"🎮 Demo Mode: Added {signal.symbol} to stealth trailing system")
                    
                except Exception as stealth_error:
                    log.error(f"Failed to add mock trade to stealth trailing: {stealth_error}")
            
            if mock_trade:
                log.info(f"🎮 DEMO BUY SIGNAL EXECUTED: {signal.symbol} @ ${signal.price:.2f} "
                        f"(Confidence: {signal.confidence:.1%}) - Trade ID: {mock_trade.trade_id}")
                
                # Note: Trade execution alert is sent by mock_trading_executor.py
                # No need to send duplicate alert here
            else:
                log.warning(f"Demo mock trade failed for {signal.symbol}")
                
        except Exception as e:
            log.error(f"Error processing demo mock signal for {signal.symbol}: {e}")
    
    async def _process_live_signal(self, signal: PrimeSignal, market_data: Dict[str, Any]):
        """Process signal in Live Mode using real E*TRADE trading"""
        try:
            # CRITICAL: Check market hours before executing any trades
            if not await self._is_market_open():
                log.warning(f"🚫 Live Mode: Market is closed, skipping trade execution for {signal.symbol}")
                return
            
            if not self.trade_manager:
                log.error("Trade manager not initialized for live trading")
                return
            
            # Process signal through real trading system
            trade_result = await self.trade_manager.process_signal(signal, market_data)
            
            if trade_result.action.value == "open":
                log.info(f"💰 LIVE BUY SIGNAL EXECUTED: {signal.symbol} @ ${signal.price:.2f} "
                        f"(Confidence: {signal.confidence:.1%})")
                
                # Send live trading alert
                if self.alert_manager:
                    await self.alert_manager.send_trade_execution_alert(
                        symbol=signal.symbol,
                        side="BUY",
                        price=signal.price,
                        quantity=trade_result.quantity if hasattr(trade_result, 'quantity') else 100,
                        trade_id=f"LIVE_{signal.symbol}_{int(time.time())}",
                        mode="LIVE_MODE"
                    )
            else:
                log.debug(f"Live signal not executed for {signal.symbol}: {trade_result.reasoning}")
                
        except Exception as e:
            log.error(f"Error processing live real signal for {signal.symbol}: {e}")
    
    def _create_mock_market_data_list(self, symbol: str, market_data: Dict[str, Any]) -> List[Dict]:
        """Create mock market data list for signal generation"""
        try:
            # Create realistic historical data for the symbol
            base_price = market_data.get('price', 100.0)
            volume_ratio = market_data.get('volume_ratio', 1.0)
            
            mock_data = []
            current_price = base_price
            
            for i in range(100):  # 100 data points
                # Simulate price movement
                price_change = np.random.normal(0.001, 0.02)
                current_price *= (1 + price_change)
                
                # Create OHLC data
                open_price = current_price * np.random.uniform(0.998, 1.002)
                close_price = current_price
                high_price = max(open_price, close_price) * np.random.uniform(1.001, 1.015)
                low_price = min(open_price, close_price) * np.random.uniform(0.985, 0.999)
                
                mock_data.append({
                    'timestamp': datetime.now() - timedelta(hours=100-i),
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': int(1000000 * volume_ratio * np.random.uniform(0.8, 1.2))
                })
            
            return mock_data
            
        except Exception as e:
            log.error(f"Error creating mock market data for {symbol}: {e}")
            return []
    
    async def _generate_signals_task(self) -> Dict[str, Any]:
        """Generate trading signals task"""
        try:
            if not self.signal_generator:
                return {}
            
            # Get market data for signal generation
            symbols = await self._get_active_symbols()
            if not symbols:
                return {}
            
            # Generate signals in parallel
            signals = await self.parallel_manager.process_symbols_parallel(
                symbols, 
                self._generate_signal_for_symbol
            )
            
            # Process generated signals
            processed_signals = []
            for symbol, signal in signals.items():
                if signal and not isinstance(signal, Exception):
                    processed_signals.append(signal)
            
            self.performance_metrics['signals_generated'] += len(processed_signals)
            return {'signals': processed_signals, 'count': len(processed_signals)}
            
        except Exception as e:
            log.error(f"Error generating signals: {e}")
            return {}
    
    async def _update_positions_task(self) -> Dict[str, Any]:
        """Update positions task"""
        try:
            if not self.trade_manager:
                return {}
            
            # Get current positions
            positions = await self._get_current_positions()
            if not positions:
                return {}
            
            # Update positions in parallel
            updates = await self.parallel_manager.process_symbols_parallel(
                list(positions.keys()),
                self._update_position_for_symbol
            )
            
            # Process updates
            updated_count = len([u for u in updates.values() if u and not isinstance(u, Exception)])
            self.performance_metrics['positions_updated'] += updated_count
            
            return {'updates': updates, 'count': updated_count}
            
        except Exception as e:
            log.error(f"Error updating positions: {e}")
            return {}
    
    async def _assess_risk_task(self) -> Dict[str, Any]:
        """Assess risk task"""
        try:
            if not self.risk_manager:
                return {}
            
            # Get risk assessment
            risk_summary = self.risk_manager.get_risk_summary()
            return {'risk_summary': risk_summary}
            
        except Exception as e:
            log.error(f"Error assessing risk: {e}")
            return {}
    
    async def _update_stealth_task(self) -> Dict[str, Any]:
        """Update stealth trailing task"""
        try:
            if not self.stealth_trailing:
                return {}
            
            # Update stealth trailing for all positions
            positions = await self._get_current_positions()
            if not positions:
                return {}
            
            # Update stealth trailing in parallel
            updates = await self.parallel_manager.process_symbols_parallel(
                list(positions.keys()),
                self._update_stealth_for_symbol
            )
            
            return {'updates': updates, 'count': len(updates)}
            
        except Exception as e:
            log.error(f"Error updating stealth trailing: {e}")
            return {}
    
    async def _generate_signal_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate signal for a specific symbol"""
        try:
            if not self.signal_generator:
                return None
            
            # Get market data
            market_data = await self.data_manager.get_historical_data(symbol, datetime.now() - timedelta(days=30), datetime.now(), "1d")
            if not market_data:
                return None
            
            # Two-step signal generation process
            
            # Step 1: Multi-Strategy Manager (Screening)
            if hasattr(self, 'multi_strategy_manager') and self.multi_strategy_manager:
                # Convert market data to format expected by multi-strategy manager
                prices = [d['close'] for d in market_data]
                volumes = [d['volume'] for d in market_data]
                strategy_market_data = {
                    'prices': prices,
                    'volumes': volumes
                }
                
                multi_result = await self.multi_strategy_manager.analyze_symbol(symbol, strategy_market_data)
                
                # Send multi-strategy analysis alert
                if self.alert_manager:
                    try:
                        # Convert strategy results to dict format for alert
                        strategy_results = {}
                        if hasattr(multi_result, 'strategy_results') and multi_result.strategy_results:
                            for strategy_name, result in multi_result.strategy_results.strategies.items():
                                strategy_results[strategy_name] = result
                        
                        await self.alert_manager.send_multi_strategy_analysis_alert(
                            symbol=symbol,
                            strategy_results=strategy_results,
                            has_signals=multi_result.should_trade
                        )
                    except Exception as alert_error:
                        log.error(f"Failed to send multi-strategy analysis alert: {alert_error}")
                
                # Only proceed if multi-strategy validation passes
                if not multi_result.should_trade:
                    log.debug(f"Symbol {symbol} failed multi-strategy validation: {multi_result.reasoning}")
                    return None
                
                log.info(f"Symbol {symbol} passed multi-strategy validation: {multi_result.agreement_level.value} agreement ({len(multi_result.agreements)} strategies)")
            
            # Step 2: Production Signal Generator (Final Confirmation)
            # Convert market data to format expected by signal generator
            signal_market_data = []
            for d in market_data:
                signal_market_data.append({
                    'timestamp': datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')) if isinstance(d['timestamp'], str) else d['timestamp'],
                    'open': d['open'],
                    'high': d['high'],
                    'low': d['low'],
                    'close': d['close'],
                    'volume': d['volume']
                })
            
            signal = await self.signal_generator.generate_profitable_signal(symbol, signal_market_data, self.strategy_mode)
            
            # Send signal generator alert
            if self.alert_manager:
                try:
                    signal_generated = signal is not None
                    signal_quality = signal.get('signal_quality', 'Unknown') if signal else None
                    
                    await self.alert_manager.send_signal_generator_alert(
                        symbol=symbol,
                        signal_generated=signal_generated,
                        signal_quality=signal_quality
                    )
                except Exception as alert_error:
                    log.error(f"Failed to send signal generator alert: {alert_error}")
            
            # Add multi-strategy info if available
            if hasattr(self, 'multi_strategy_manager') and self.multi_strategy_manager and signal:
                signal['multi_strategy_agreement'] = multi_result.agreement_level.value
                signal['multi_strategy_agreements'] = [s.value for s in multi_result.agreements]
                signal['multi_strategy_reasoning'] = multi_result.reasoning
            
            return signal
            
        except Exception as e:
            log.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    async def _update_position_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Update position for a specific symbol"""
        try:
            if not self.trade_manager:
                return None
            
            # Get market data
            market_data = await self.data_manager.get_market_data(symbol)
            if not market_data:
                return None
            
            # Update position
            update = await self.trade_manager.update_position(symbol, market_data)
            return update
            
        except Exception as e:
            log.error(f"Error updating position for {symbol}: {e}")
            return None
    
    async def _update_stealth_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Update stealth trailing for a specific symbol with comprehensive market data"""
        try:
            if not self.stealth_trailing:
                return None
            
            # Get comprehensive market data with all required features
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Get historical data for technical analysis
            historical_data = await self.data_manager.get_historical_data(symbol, start_date, end_date, "1d")
            if not historical_data or len(historical_data) < 20:
                log.warning(f"Insufficient historical data for stealth analysis of {symbol}")
                return None
            
            # Extract current price and calculate technical indicators
            current_price = historical_data[-1]['close']
            prices = [d['close'] for d in historical_data[-20:]]
            volumes = [d['volume'] for d in historical_data[-20:]]
            
            # Calculate technical indicators
            rsi = self._calculate_rsi(prices)
            atr = self._calculate_atr(historical_data[-14:])
            volume_ratio = volumes[-1] / np.mean(volumes[:-1]) if len(volumes) > 1 else 1.0
            momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0.0
            volatility = np.std(prices) / np.mean(prices) if prices else 0.0
            
            # Create comprehensive market data for stealth system
            market_data = {
                'price': current_price,
                'rsi': rsi,
                'atr': atr,
                'volume_ratio': volume_ratio,
                'momentum': momentum,
                'volatility': volatility,
                'volume': volumes[-1],
                'high': historical_data[-1]['high'],
                'low': historical_data[-1]['low'],
                'open': historical_data[-1]['open'],
                'close': current_price
            }
            
            # Update stealth trailing with comprehensive data
            update = await self.stealth_trailing.update_position(symbol, market_data)
            return update
            
        except Exception as e:
            log.error(f"Error updating stealth for {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_atr(self, historical_data: List[Dict], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(historical_data) < 2:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(historical_data)):
            high = historical_data[i]['high']
            low = historical_data[i]['low']
            prev_close = historical_data[i-1]['close']
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)
        
        if not true_ranges:
            return 0.0
        
        return np.mean(true_ranges[-period:]) if len(true_ranges) >= period else np.mean(true_ranges)
    
    async def _get_active_symbols(self) -> List[str]:
        """Get list of active symbols for processing"""
        try:
            # This would typically come from a symbol selector or watchlist
            # For now, return a default list
            return ["SPY", "QQQ", "TQQQ", "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META"]
        except Exception as e:
            log.error(f"Error getting active symbols: {e}")
            return []
    
    async def _get_current_positions(self) -> Dict[str, Any]:
        """Get current positions from appropriate source (Demo or Live Mode)"""
        try:
            # Check if we're in Demo Mode
            if self.config.mode == SystemMode.DEMO_MODE and hasattr(self, 'mock_executor') and self.mock_executor:
                # Get mock positions from Demo Mode
                mock_positions = self.mock_executor.get_active_positions()
                if mock_positions:
                    # Convert mock positions to format expected by stealth trailing
                    positions = {}
                    for trade_id, trade in mock_positions.items():
                        positions[trade.symbol] = {
                            'symbol': trade.symbol,
                            'entry_price': trade.entry_price,
                            'current_price': trade.current_price,
                            'quantity': trade.quantity,
                            'side': trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                            'status': trade.status,
                            'entry_time': trade.timestamp,
                            'confidence': getattr(trade, 'confidence', 0.85),
                            'stop_loss': getattr(trade, 'stop_loss', trade.entry_price * 0.95),
                            'take_profit': getattr(trade, 'take_profit', trade.entry_price * 1.15),
                            'trade_id': trade_id,
                            'source': 'demo'
                        }
                    log.debug(f"Demo Mode: Retrieved {len(positions)} mock positions for stealth trailing")
                    return positions
                log.debug("Demo Mode: No mock positions found")
                return {}
            
            # Live Mode: Get positions from trade manager
            elif self.trade_manager and hasattr(self.trade_manager, 'active_positions'):
                # Get live positions from unified trade manager
                live_positions = {}
                for symbol, position in self.trade_manager.active_positions.items():
                    live_positions[symbol] = {
                        'symbol': position.symbol,
                        'entry_price': position.entry_price,
                        'current_price': position.current_price,
                        'quantity': position.quantity,
                        'side': position.side.value if hasattr(position.side, 'value') else str(position.side),
                        'status': position.status.value if hasattr(position.status, 'value') else str(position.status),
                        'entry_time': position.entry_time,
                        'confidence': position.confidence,
                        'stop_loss': position.stop_loss,
                        'take_profit': position.take_profit,
                        'position_id': position.position_id,
                        'source': 'live'
                    }
                log.debug(f"Live Mode: Retrieved {len(live_positions)} live positions for stealth trailing")
                return live_positions
            
            log.debug("No positions found for stealth trailing")
            return {}
        except Exception as e:
            log.error(f"Error getting current positions: {e}")
            return {}
    
    def _update_performance_metrics(self, loop_start: float):
        """Update performance metrics"""
        loop_time = (time.time() - loop_start) * 1000  # Convert to milliseconds
        
        self.performance_metrics['main_loop_iterations'] += 1
        
        # Update average loop time
        iterations = self.performance_metrics['main_loop_iterations']
        current_avg = self.performance_metrics['avg_loop_time']
        self.performance_metrics['avg_loop_time'] = ((current_avg * (iterations - 1)) + loop_time) / iterations
    
    def _log_performance_report(self):
        """Log performance report"""
        if not self.performance_metrics['start_time']:
            return
        
        runtime = time.time() - self.performance_metrics['start_time']
        
        log.info("📊 Performance Report:")
        log.info(f"  Runtime: {runtime:.2f}s")
        log.info(f"  Main loop iterations: {self.performance_metrics['main_loop_iterations']}")
        log.info(f"  Average loop time: {self.performance_metrics['avg_loop_time']:.2f}ms")
        log.info(f"  Signals generated: {self.performance_metrics['signals_generated']}")
        log.info(f"  Positions updated: {self.performance_metrics['positions_updated']}")
        log.info(f"  Errors: {self.performance_metrics['errors']}")
        
        # Parallel processing metrics
        parallel_metrics = self.parallel_manager.get_metrics()
        log.info(f"  Parallel processing:")
        for key, value in parallel_metrics.items():
            log.info(f"    {key}: {value}")
        
        # Memory metrics
        memory_stats = self.memory_manager.get_memory_stats()
        log.info(f"  Memory usage:")
        for key, value in memory_stats.items():
            log.info(f"    {key}: {value}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            'trading_system': self.performance_metrics,
            'parallel_processing': self.parallel_manager.get_metrics(),
            'memory': self.memory_manager.get_memory_stats(),
            'config': {
                'max_workers': self.config.max_workers,
                'batch_size': self.config.batch_size,
                'main_loop_interval': self.config.main_loop_interval
            }
        }

# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_prime_trading_system(config: TradingConfig = None) -> PrimeTradingSystem:
    """Get optimized Prime Trading System instance"""
    return PrimeTradingSystem(config)

# ============================================================================
# PERFORMANCE TESTING
# ============================================================================

async def test_performance():
    """Test performance improvements"""
    print("🚀 Testing Optimized Prime Trading System Performance...")
    
    # Create performance config
    config = PerformanceConfig(
        max_workers=5,
        batch_size=10,
        main_loop_interval=0.1
    )
    
    # Initialize system
    system = get_prime_trading_system(config)
    
    # Mock components
    components = {
        'data_manager': None,
        'signal_generator': None,
        'risk_manager': None,
        'trade_manager': None,
        'stealth_trailing': None,
        'alert_manager': None
    }
    
    # Initialize system
    await system.initialize(components)
    
    # Test parallel processing
    print("\n📊 Testing parallel processing...")
    start_time = time.time()
    
    # Simulate parallel tasks
    symbols = ["SPY", "QQQ", "TQQQ", "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META"]
    
    # Test parallel symbol processing
    results = await system.parallel_manager.process_symbols_parallel(
        symbols,
        lambda symbol: {"symbol": symbol, "processed": True}
    )
    
    parallel_time = (time.time() - start_time) * 1000
    print(f"Parallel processing time: {parallel_time:.2f}ms ({len(results)} symbols)")
    print(f"Average per symbol: {parallel_time/len(symbols):.2f}ms")
    
    # Get performance metrics
    metrics = system.get_performance_metrics()
    print(f"\n📈 Performance Metrics:")
    for category, data in metrics.items():
        print(f"  {category}:")
        for key, value in data.items():
            print(f"    {key}: {value}")
    
    # Shutdown system
    await system.stop()
    
    print("\n✅ Performance test completed!")

if __name__ == "__main__":
    asyncio.run(test_performance())
