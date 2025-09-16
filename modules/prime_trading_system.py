#!/usr/bin/env python3
"""
Prime Trading System
===================

Main trading system coordinator that integrates all components:
- Market Manager for holiday/weekend checking
- Unified Trade Manager for position management
- Signal Generator for signal processing
- Risk Manager for risk controls
- Alert Manager for notifications

This is the main entry point that coordinates all trading operations
and ensures proper market hour and holiday compliance.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .prime_models import StrategyMode, SignalType, SignalSide, TradeStatus
    from .prime_market_manager import get_prime_market_manager, PrimeMarketManager
    from .prime_unified_trade_manager import PrimeUnifiedTradeManager, TradeResult, TradeAction
    from .production_signal_generator import get_production_signal_generator, ProductionSignalGenerator
    from .prime_risk_manager import get_prime_risk_manager, PrimeRiskManager
    from .prime_alert_manager import get_prime_alert_manager, PrimeAlertManager
    from .config_loader import get_config_value
except ImportError:
    from prime_models import StrategyMode, SignalType, SignalSide, TradeStatus
    from prime_market_manager import get_prime_market_manager, PrimeMarketManager
    from prime_unified_trade_manager import PrimeUnifiedTradeManager, TradeResult, TradeAction
    from production_signal_generator import get_production_signal_generator, ProductionSignalGenerator
    from prime_risk_manager import get_prime_risk_manager, PrimeRiskManager
    from prime_alert_manager import get_prime_alert_manager, PrimeAlertManager
    from config_loader import get_config_value

log = logging.getLogger(__name__)

class SystemMode(Enum):
    """System operation modes"""
    SIGNAL_ONLY = "signal_only"
    SCANNER_ONLY = "scanner_only"
    FULL_TRADING = "full_trading"
    ALERT_ONLY = "alert_only"

@dataclass
class TradingConfig:
    """Trading system configuration"""
    mode: SystemMode = SystemMode.FULL_TRADING
    strategy_mode: StrategyMode = StrategyMode.STANDARD
    enable_premarket_analysis: bool = True
    enable_confluence_trading: bool = True
    enable_multi_strategy: bool = True
    enable_news_sentiment: bool = True
    enable_enhanced_signals: bool = True
    max_positions: int = 20  # Max concurrent open positions
    max_daily_trades: int = 40  # Daily trade limit (can close and reopen)
    scan_frequency: int = 60  # Changed from 30 to 60 seconds for API efficiency
    position_refresh_frequency: int = 60  # NEW: Separate position refresh frequency
    signal_generation_frequency: int = 120  # NEW: Signal generation every 2 minutes
    api_calls_per_hour_limit: int = 200  # NEW: API call rate limiting

class PrimeTradingSystem:
    """
    Prime Trading System
    
    Main coordinator that integrates all trading components and ensures
    proper market hour and holiday compliance.
    """
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.running = False
        self.start_time = None
        
        # Initialize core components
        self.market_manager = get_prime_market_manager()
        self.trade_manager = PrimeUnifiedTradeManager(config.strategy_mode)
        self.signal_generator = get_production_signal_generator()
        self.risk_manager = get_prime_risk_manager()
        self.alert_manager = get_prime_alert_manager()
        
        # Initialize news manager for sentiment analysis
        from .prime_news_manager import get_prime_news_manager
        self.news_manager = get_prime_news_manager(market_manager=self.market_manager)
        
        # Initialize E*TRADE trading system
        self.etrade_trading = None
        self._initialize_etrade_trading()
        
        # System metrics
        self.metrics = {
            'signals_processed': 0,
            'trades_executed': 0,
            'positions_opened': 0,
            'positions_closed': 0,
            'daily_trades_today': 0,  # NEW: Track daily trades
            'last_reset_date': None,  # NEW: Track when daily counter was reset
            'errors': 0,
            'uptime_hours': 0.0,
            'last_signal_time': None,
            'last_trade_time': None
        }
        
        # API call tracking
        self.api_calls_today = 0
        self.api_calls_hour = 0
        self.last_api_reset_hour = datetime.now().hour
        
        # Market status tracking
        self.current_phase = "DARK"
        self.is_trading_allowed = False
        
        log.info("Prime Trading System initialized")
    
    def _initialize_etrade_trading(self):
        """Initialize E*TRADE trading system"""
        try:
            from .prime_etrade_trading import PrimeETradeTrading
            from .config_loader import get_config_value
            
            # Determine environment
            etrade_mode = get_config_value('ETRADE_MODE', 'prod')
            
            # Initialize E*TRADE trading
            self.etrade_trading = PrimeETradeTrading(environment=etrade_mode)
            
            # Initialize the trading system
            if self.etrade_trading.initialize():
                log.info("✅ E*TRADE trading system initialized successfully")
                
                # Get account summary for verification
                account_summary = self.etrade_trading.get_account_summary()
                if 'error' not in account_summary:
                    log.info(f"✅ E*TRADE account ready: {account_summary['account']['name']}")
                    log.info(f"   Cash available for investment: ${account_summary['balance']['cash_available_for_investment']}")
                    log.info(f"   Cash buying power: ${account_summary['balance']['cash_buying_power']}")
                else:
                    log.warning(f"⚠️ E*TRADE account issue: {account_summary['error']}")
            else:
                log.error("❌ Failed to initialize E*TRADE trading system")
                self.etrade_trading = None
                
        except Exception as e:
            log.error(f"❌ Error initializing E*TRADE trading: {e}")
            self.etrade_trading = None

    async def initialize(self) -> bool:
        """Initialize the trading system"""
        try:
            log.info("Initializing Prime Trading System...")
            
            # Initialize market manager
            await self.market_manager.initialize()
            log.info("✅ Market Manager initialized")
            
            # Initialize signal generator
            await self.signal_generator.initialize()
            log.info("✅ Signal Generator initialized")
            
            # Initialize risk manager
            await self.risk_manager.initialize()
            log.info("✅ Risk Manager initialized")
            
            # Initialize alert manager
            await self.alert_manager.initialize()
            log.info("✅ Alert Manager initialized")
            
            # Check initial market status
            await self._update_market_status()
            
            log.info("✅ Prime Trading System initialized successfully")
            return True
            
        except Exception as e:
            log.error(f"❌ Failed to initialize Prime Trading System: {e}")
            return False

    async def start(self) -> None:
        """Start the trading system"""
        try:
            log.info("🚀 Starting Prime Trading System...")
            
            # Initialize system
            if not await self.initialize():
                log.error("❌ Failed to initialize system")
                return
            
            self.running = True
            self.start_time = datetime.now()
            
            # Send startup alert
            await self.alert_manager.send_system_alert(
                "system_startup",
                "Prime Trading System started",
                {"mode": self.config.mode.value, "strategy": self.config.strategy_mode.value}
            )
            
            # Main trading loop
            await self._main_trading_loop()
            
        except Exception as e:
            log.error(f"❌ Error in trading system: {e}")
            await self.alert_manager.send_system_alert(
                "system_error",
                f"Trading system error: {e}",
                {"error": str(e)}
            )
        finally:
            await self.shutdown()

    async def _main_trading_loop(self) -> None:
        """Main trading loop"""
        log.info("🔄 Starting main trading loop...")
        
        while self.running:
            try:
                # Update market status
                await self._update_market_status()
                
                # Check if trading is allowed
                if not self.is_trading_allowed:
                    log.debug("⏸️ Trading not allowed - market closed or holiday")
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # Process signals based on system mode (only if we can open new positions)
                if self.config.mode in [SystemMode.FULL_TRADING, SystemMode.SIGNAL_ONLY]:
                    if self._can_open_new_position():
                        await self._process_signals()
                    else:
                        log.debug("🚫 Signal processing skipped - position limits reached")
                
                # Update positions (always runs regardless of limits)
                if self.config.mode in [SystemMode.FULL_TRADING]:
                    await self._update_positions()
                
                # Update metrics
                self._update_metrics()
                
                # Wait for next cycle based on system activity
                if self.config.mode in [SystemMode.FULL_TRADING]:
                    await asyncio.sleep(self.config.position_refresh_frequency)
                else:
                    await asyncio.sleep(self.config.scan_frequency)
                
            except Exception as e:
                log.error(f"❌ Error in main trading loop: {e}")
                self.metrics['errors'] += 1
                await asyncio.sleep(30)  # Wait before retry

    async def _update_market_status(self) -> None:
        """Update market status and trading permissions"""
        try:
            # Check if it's a trading day
            is_trading_day = self.market_manager.is_trading_day()
            
            # Check if market is open
            is_market_open = self.market_manager.is_market_open()
            
            # Get current market phase
            current_phase = self.market_manager.get_market_phase()
            self.current_phase = current_phase.value
            
            # Determine if trading is allowed
            self.is_trading_allowed = is_trading_day and is_market_open
            
            # Log status changes
            if not is_trading_day:
                log.info("📅 Not a trading day (weekend or holiday)")
            elif not is_market_open:
                log.info("⏰ Market is closed")
            else:
                log.debug(f"✅ Trading allowed - Phase: {self.current_phase}")
                
        except Exception as e:
            log.error(f"❌ Error updating market status: {e}")

    async def _process_signals(self) -> None:
        """Process trading signals"""
        try:
            # Check daily trade limit
            if not self._can_open_new_position():
                log.debug("🚫 Daily trade limit reached - skipping signal processing")
                return
            
            # Generate signals
            signals = await self.signal_generator.generate_signals()
            
            if not signals:
                return
            
            log.info(f"📊 Generated {len(signals)} signals")
            
            # Process each signal
            for signal in signals:
                try:
                    # Check daily trade limit again
                    if not self._can_open_new_position():
                        log.debug("🚫 Daily trade limit reached during signal processing")
                        break
                    
                    # Check risk limits
                    if not await self.risk_manager.can_open_position(signal.symbol):
                        log.debug(f"🚫 Risk limit reached for {signal.symbol}")
                        continue
                    
                    # Get comprehensive market data for signal analysis
                    market_data = await self.data_manager.get_strategy_market_data(signal.symbol)
                    
                    # Log data quality for monitoring
                    data_quality = market_data.get('data_quality', 'unknown')
                    historical_points = market_data.get('historical_points', 0)
                    log.debug(f"📊 {signal.symbol} data quality: {data_quality} ({historical_points} historical points)")
                    
                    # Process signal through trade manager
                    result = await self.trade_manager.process_signal(signal, market_data)
                    
                    # Update metrics
                    self.metrics['signals_processed'] += 1
                    self.metrics['last_signal_time'] = datetime.now().isoformat()
                    
                    # Log result
                    if result.action == TradeAction.OPEN:
                        log.info(f"✅ Position opened: {result.symbol} - {result.reasoning}")
                        self.metrics['positions_opened'] += 1
                        self.metrics['trades_executed'] += 1
                        self.metrics['last_trade_time'] = datetime.now().isoformat()
                    elif result.action == TradeAction.HOLD:
                        log.debug(f"⏸️ Signal held: {result.symbol} - {result.reasoning}")
                    
                except Exception as e:
                    log.error(f"❌ Error processing signal for {signal.symbol}: {e}")
                    self.metrics['errors'] += 1
                    
        except Exception as e:
            log.error(f"❌ Error in signal processing: {e}")
            self.metrics['errors'] += 1

    async def _update_positions(self) -> None:
        """Update active positions - always runs regardless of daily trade limit"""
        try:
            # Get market data for all active positions
            active_symbols = list(self.trade_manager.active_positions.keys())
            if not active_symbols:
                return
            
            log.info(f"📊 Updating positions for {len(active_symbols)} symbols...")
            market_data = {}
            for symbol in active_symbols:
                market_data[symbol] = await self.data_manager.get_strategy_market_data(symbol)
            
            # Update positions through trade manager
            results = await self.trade_manager.update_positions(market_data)
            
            # Log results and track metrics
            for result in results:
                if result.action == TradeAction.CLOSE:
                    log.info(f"✅ Position closed: {result.symbol} - {result.reasoning}")
                    self.metrics['positions_closed'] += 1
                    self.metrics['trades_executed'] += 1
                    self.metrics['last_trade_time'] = datetime.now().isoformat()
                elif result.action == TradeAction.OPEN:
                    # Only increment daily trades if we're not at the limit
                    if self.metrics['daily_trades_today'] < self.config.max_daily_trades:
                        log.info(f"✅ Position opened: {result.symbol}")
                        self.metrics['positions_opened'] += 1
                        self._increment_daily_trades()
                        self.metrics['last_trade_time'] = datetime.now().isoformat()
                    else:
                        log.warning(f"🚫 Position opening blocked: {result.symbol} - daily trade limit reached")
            
            # Track API calls for position updates
            self._increment_api_calls(len(active_symbols))
                    
        except Exception as e:
            log.error(f"❌ Error updating positions: {e}")
            self.metrics['errors'] += 1

    async def _get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for a symbol including news sentiment"""
        try:
            # Basic market data structure
            market_data = {
                'symbol': symbol,
                'price': 100.0,  # Placeholder - would integrate with data provider
                'volume': 1000000,  # Placeholder
                'timestamp': datetime.now().isoformat()
            }
            
            # Add news sentiment analysis if news manager is available
            if self.news_manager and self.config.enable_news_sentiment:
                try:
                    sentiment_result = await self.news_manager.analyze_news_sentiment(symbol, lookback_hours=24)
                    
                    # Add sentiment data to market data
                    market_data['news_sentiment'] = {
                        'sentiment_score': sentiment_result.overall_sentiment,
                        'direction': 'positive' if sentiment_result.overall_sentiment > 0.1 else 'negative' if sentiment_result.overall_sentiment < -0.1 else 'neutral',
                        'confidence': sentiment_result.sentiment_confidence,
                        'news_count': sentiment_result.news_count,
                        'trading_implications': sentiment_result.trading_implications,
                        'breaking_news': sentiment_result.breaking_news,
                        'earnings_related': sentiment_result.earnings_related,
                        'market_impact': sentiment_result.market_impact,
                        'sentiment_trend': sentiment_result.sentiment_trend
                    }
                    
                    log.debug(f"📰 News sentiment for {symbol}: {sentiment_result.overall_sentiment:.2f} ({sentiment_result.news_count} items)")
                    
                except Exception as e:
                    log.warning(f"⚠️ News sentiment analysis failed for {symbol}: {e}")
                    # Add neutral sentiment as fallback
                    market_data['news_sentiment'] = {
                        'sentiment_score': 0.0,
                        'direction': 'neutral',
                        'confidence': 0.0,
                        'news_count': 0,
                        'trading_implications': 'neutral',
                        'breaking_news': False,
                        'earnings_related': False,
                        'market_impact': 0.0,
                        'sentiment_trend': 'stable'
                    }
            
            return market_data
            
        except Exception as e:
            log.error(f"❌ Error getting market data for {symbol}: {e}")
            return {}

    def _update_metrics(self) -> None:
        """Update system metrics"""
        if self.start_time:
            self.metrics['uptime_hours'] = (datetime.now() - self.start_time).total_seconds() / 3600
        
        # Reset daily counters if new day
        current_date = datetime.now().date()
        if self.metrics['last_reset_date'] != current_date:
            self.metrics['daily_trades_today'] = 0
            self.metrics['last_reset_date'] = current_date
            self.api_calls_today = 0
            log.info("🔄 Daily counters reset for new trading day")
        
        # Reset hourly API counter
        current_hour = datetime.now().hour
        if current_hour != self.last_api_reset_hour:
            self.api_calls_hour = 0
            self.last_api_reset_hour = current_hour
    
    def _can_open_new_position(self) -> bool:
        """Check if we can open a new position based on daily and concurrent limits"""
        # Check daily trade limit
        if self.metrics['daily_trades_today'] >= self.config.max_daily_trades:
            log.debug("🚫 Daily trade limit reached - no new positions allowed")
            return False
        
        # Check concurrent position limit
        current_positions = len(self.trade_manager.get_active_positions())
        if current_positions >= self.config.max_positions:
            log.debug(f"🚫 Concurrent position limit reached ({current_positions}/{self.config.max_positions})")
            return False
        
        # Check API call limits
        if self.api_calls_hour >= self.config.api_calls_per_hour_limit:
            log.debug("🚫 API call limit reached - throttling new positions")
            return False
        
        return True
    
    def _increment_daily_trades(self) -> None:
        """Increment daily trade counter"""
        self.metrics['daily_trades_today'] += 1
        log.info(f"📊 Daily trades: {self.metrics['daily_trades_today']}/{self.config.max_daily_trades}")
    
    def _increment_api_calls(self, count: int = 1) -> None:
        """Increment API call counters"""
        self.api_calls_today += count
        self.api_calls_hour += count

    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            'system_metrics': self.metrics.copy(),
            'trading_metrics': self.trade_manager.get_unified_metrics(),
            'scanner_metrics': self.signal_generator.get_metrics(),
            'current_phase': self.current_phase,
            'is_trading_allowed': self.is_trading_allowed,
            'running': self.running
        }

    async def shutdown(self) -> None:
        """Shutdown the trading system"""
        try:
            log.info("🛑 Shutting down Prime Trading System...")
            
            self.running = False
            
            # Send shutdown alert
            await self.alert_manager.send_system_alert(
                "system_shutdown",
                "Prime Trading System shutting down",
                {"uptime_hours": self.metrics['uptime_hours']}
            )
            
            # Shutdown components
            if hasattr(self.market_manager, 'shutdown'):
                await self.market_manager.shutdown()
            
            if hasattr(self.signal_generator, 'shutdown'):
                await self.signal_generator.shutdown()
            
            if hasattr(self.risk_manager, 'shutdown'):
                await self.risk_manager.shutdown()
            
            if hasattr(self.alert_manager, 'shutdown'):
                await self.alert_manager.shutdown()
            
            log.info("✅ Prime Trading System shutdown completed")
            
        except Exception as e:
            log.error(f"❌ Error during shutdown: {e}")

# Global instance
_prime_trading_system = None

def get_prime_trading_system(config: TradingConfig) -> PrimeTradingSystem:
    """Get the prime trading system instance"""
    global _prime_trading_system
    if _prime_trading_system is None:
        _prime_trading_system = PrimeTradingSystem(config)
    return _prime_trading_system

# For backward compatibility
def get_integrated_system() -> PrimeTradingSystem:
    """Get integrated system (backward compatibility)"""
    config = TradingConfig()  # Default configuration
    return get_prime_trading_system(config)
