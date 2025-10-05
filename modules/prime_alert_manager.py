#!/usr/bin/env python3
"""
Prime Alert Manager
==================

Comprehensive alert management system for the V2 ETrade Strategy.
Handles all Telegram notifications for trade signals, performance updates,
and end-of-day summaries.

Key Features:
- Trade signal alerts (entry/exit notifications)
- Performance monitoring alerts
- End-of-day trade summaries
- System status notifications
- Error and warning alerts
- Configurable alert levels and throttling
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import requests
import aiohttp
from collections import defaultdict, deque
import threading

try:
    from .config_loader import get_config_value
except ImportError:
    # Fallback for direct imports
    def get_config_value(key, default=''):
        import os
        return os.getenv(key, default)

log = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert level enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"

class AlertType(Enum):
    """Alert type enumeration"""
    TRADE_SIGNAL = "trade_signal"
    TRADE_ENTRY = "trade_entry"
    TRADE_EXIT = "trade_exit"
    PERFORMANCE_UPDATE = "performance_update"
    END_OF_DAY_SUMMARY = "end_of_day_summary"
    SYSTEM_STATUS = "system_status"
    ERROR = "error"
    WARNING = "warning"
    MARKET_ALERT = "market_alert"
    # OAuth Token Management Alerts
    OAUTH_RENEWAL = "oauth_renewal"
    OAUTH_SUCCESS = "oauth_success"
    OAUTH_EXPIRED = "oauth_expired"
    OAUTH_ERROR = "oauth_error"
    OAUTH_WARNING = "oauth_warning"
    OAUTH_TOKEN_RENEWED_CONFIRMATION = "oauth_token_renewed_confirmation"
    
    # Trading Pipeline Alerts
    WATCHLIST_CREATED = "watchlist_created"
    SYMBOL_SELECTION_COMPLETE = "symbol_selection_complete"
    MULTI_STRATEGY_ANALYSIS = "multi_strategy_analysis"
    SIGNAL_GENERATOR_PROCESSING = "signal_generator_processing"
    MOCK_EXECUTOR_PROCESSING = "mock_executor_processing"

@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    confidence: Optional[float] = None
    expected_return: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TradeAlert:
    """Trade-specific alert data structure"""
    symbol: str
    strategy: str
    action: str  # "BUY" or "SELL"
    price: float
    quantity: int
    confidence: float
    expected_return: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceSummary:
    """End-of-day performance summary"""
    date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    daily_return: float
    active_positions: int
    signals_generated: int
    signals_accepted: int
    acceptance_rate: float
    top_performers: List[Dict[str, Any]] = field(default_factory=list)
    worst_performers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Additional metrics for enhanced reporting
    max_drawdown: float = 0.0
    capital_used_pct: float = 0.0
    consecutive_wins: int = 0
    avg_risk_per_trade: float = 4.2
    total_pnl_dollars: float = 0.0

@dataclass
class OAuthAlert:
    """OAuth-specific alert data structure"""
    environment: str  # "prod" or "sandbox"
    alert_type: str  # "renewal", "success", "error", "warning"
    message: str
    oauth_url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PrimeAlertManager:
    """Prime Alert Manager for comprehensive notification system"""
    
    def __init__(self):
        self.name = "Prime Alert Manager"
        self.version = "1.0"
        
        # Load configuration first
        self._load_configuration()
        
        # Telegram configuration
        self.telegram_bot_token = get_config_value('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = get_config_value('TELEGRAM_CHAT_ID', '')
        telegram_config = get_config_value('TELEGRAM_ALERTS_ENABLED', 'true')
        self.telegram_enabled = str(telegram_config).lower() == 'true' if isinstance(telegram_config, (str, bool)) else True
        
        # Alert configuration
        def safe_bool_config(key: str, default: str = 'true') -> bool:
            config_val = get_config_value(key, default)
            return str(config_val).lower() == 'true' if isinstance(config_val, (str, bool)) else True
        
        self.alert_levels_enabled = {
            AlertLevel.INFO: safe_bool_config('ALERT_LEVEL_INFO', 'true'),
            AlertLevel.WARNING: safe_bool_config('ALERT_LEVEL_WARNING', 'true'),
            AlertLevel.ERROR: safe_bool_config('ALERT_LEVEL_ERROR', 'true'),
            AlertLevel.CRITICAL: safe_bool_config('ALERT_LEVEL_CRITICAL', 'true'),
            AlertLevel.SUCCESS: safe_bool_config('ALERT_LEVEL_SUCCESS', 'true')
        }
        
        # Throttling configuration
        self.max_alerts_per_minute = int(get_config_value('TELEGRAM_MAX_MESSAGES_PER_MINUTE', '20'))
        self.alert_cooldown_seconds = int(get_config_value('ALERT_COOLDOWN_SECONDS', '30'))
        
        # Alert tracking
        self.alert_history = deque(maxlen=1000)
        self.alert_counts = defaultdict(int)
        self.last_alert_time = defaultdict(float)
        
        # Performance tracking
        self.daily_performance = {}
        self.trade_history = []
        
        # End of day scheduling
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # OAuth configuration
        oauth_config = get_config_value('OAUTH_ALERTS_ENABLED', 'true')
        self.oauth_enabled = str(oauth_config).lower() == 'true' if isinstance(oauth_config, (str, bool)) else True
        self.oauth_renewal_url = get_config_value('OAUTH_RENEWAL_URL', 'https://easy-trading-oauth-v2.web.app')
        self.oauth_morning_hour = int(get_config_value('OAUTH_MORNING_HOUR', '21'))
        self.oauth_morning_minute = int(get_config_value('OAUTH_MORNING_MINUTE', '0'))
        self.oauth_market_open_hour = int(get_config_value('OAUTH_MARKET_OPEN_HOUR', '5'))
        self.oauth_market_open_minute = int(get_config_value('OAUTH_MARKET_OPEN_MINUTE', '30'))
        self.oauth_timezone = get_config_value('OAUTH_TIMEZONE', 'America/New_York')
        
        # OAuth tracking
        self.oauth_status = {
            'prod': {'last_renewed': None, 'is_valid': False, 'expires_at': None},
            'sandbox': {'last_renewed': None, 'is_valid': False, 'expires_at': None}
        }
        
        # System status
        self.is_initialized = False
        
        log.info(f"Prime Alert Manager v{self.version} initialized")
    
    def _load_configuration(self):
        """Load configuration from .env files"""
        try:
            from .config_loader import load_configuration
            load_configuration('standard', 'demo', 'development')
            log.info("✅ Configuration loaded successfully")
        except Exception as e:
            log.warning(f"⚠️ Could not load configuration: {e}")
            # Continue without configuration loading
    
    async def initialize(self) -> bool:
        """Initialize the alert manager"""
        try:
            if self.telegram_enabled:
                # Test Telegram connection
                if await self._test_telegram_connection():
                    log.info("✅ Telegram connection successful")
                else:
                    log.warning("⚠️ Telegram connection failed")
                    self.telegram_enabled = False
            
            self.is_initialized = True
            log.info("Prime Alert Manager initialized successfully")
            return True
            
        except Exception as e:
            log.error(f"Failed to initialize alert manager: {e}")
            return False
    
    async def _test_telegram_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                return False
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    log.info(f"Telegram bot connected: @{bot_info['result']['username']}")
                    return True
            
            return False
            
        except Exception as e:
            log.error(f"Telegram connection test failed: {e}")
            return False
    
    # ========================================================================
    # TRADE ALERTS
    # ========================================================================
    
    async def send_trade_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """Send trade signal alert"""
        try:
            alert = Alert(
                alert_id=f"signal_{signal_data.get('symbol', 'unknown')}_{int(time.time())}",
                alert_type=AlertType.TRADE_SIGNAL,
                level=AlertLevel.INFO,
                title="🎯 New Trade Signal",
                message=self._format_trade_signal_message(signal_data),
                symbol=signal_data.get('symbol'),
                strategy=signal_data.get('strategy'),
                confidence=signal_data.get('confidence'),
                expected_return=signal_data.get('expected_return'),
                metadata=signal_data
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send trade signal alert: {e}")
            return False
    
    async def send_trade_entry_alert(self, trade_data: TradeAlert) -> bool:
        """Send trade entry alert"""
        try:
            alert = Alert(
                alert_id=f"entry_{trade_data.symbol}_{int(time.time())}",
                alert_type=AlertType.TRADE_ENTRY,
                level=AlertLevel.SUCCESS,
                title="✅ Trade Executed",
                message=self._format_trade_entry_message(trade_data),
                symbol=trade_data.symbol,
                strategy=trade_data.strategy,
                confidence=trade_data.confidence,
                expected_return=trade_data.expected_return,
                metadata={
                    'action': trade_data.action,
                    'price': trade_data.price,
                    'quantity': trade_data.quantity,
                    'stop_loss': trade_data.stop_loss,
                    'take_profit': trade_data.take_profit
                }
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send trade entry alert: {e}")
            return False
    
    async def send_trade_exit_alert(self, trade_data: TradeAlert) -> bool:
        """Send trade exit alert"""
        try:
            pnl = (trade_data.price - trade_data.metadata.get('entry_price', trade_data.price)) / trade_data.metadata.get('entry_price', trade_data.price)
            pnl_pct = pnl * 100
            
            alert = Alert(
                alert_id=f"exit_{trade_data.symbol}_{int(time.time())}",
                alert_type=AlertType.TRADE_EXIT,
                level=AlertLevel.SUCCESS if pnl > 0 else AlertLevel.WARNING,
                title="🔚 Trade Closed",
                message=self._format_trade_exit_message(trade_data, pnl_pct),
                symbol=trade_data.symbol,
                strategy=trade_data.strategy,
                metadata={
                    'action': trade_data.action,
                    'price': trade_data.price,
                    'quantity': trade_data.quantity,
                    'pnl_pct': pnl_pct,
                    'reason': trade_data.reason
                }
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send trade exit alert: {e}")
            return False
    
    # ========================================================================
    # PERFORMANCE ALERTS
    # ========================================================================
    
    async def send_performance_alert(self, performance_data: Dict[str, Any]) -> bool:
        """Send performance update alert"""
        try:
            alert = Alert(
                alert_id=f"performance_{int(time.time())}",
                alert_type=AlertType.PERFORMANCE_UPDATE,
                level=AlertLevel.INFO,
                title="📊 Performance Update",
                message=self._format_performance_message(performance_data),
                metadata=performance_data
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send performance alert: {e}")
            return False
    
    async def send_end_of_day_summary(self, summary: PerformanceSummary) -> bool:
        """Send end-of-day performance summary"""
        try:
            alert = Alert(
                alert_id=f"eod_summary_{summary.date.strftime('%Y%m%d')}",
                alert_type=AlertType.END_OF_DAY_SUMMARY,
                level=AlertLevel.INFO,
                title="📈 End of Day Summary",
                message=self._format_end_of_day_message(summary),
                metadata={
                    'date': summary.date.isoformat(),
                    'total_trades': summary.total_trades,
                    'win_rate': summary.win_rate,
                    'total_pnl': summary.total_pnl,
                    'daily_return': summary.daily_return
                }
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send end-of-day summary: {e}")
            return False
    
    # ========================================================================
    # SYSTEM ALERTS
    # ========================================================================
    
    async def send_system_alert(self, title: str, message: str, level: AlertLevel = AlertLevel.INFO) -> bool:
        """Send system alert"""
        try:
            alert = Alert(
                alert_id=f"system_{int(time.time())}",
                alert_type=AlertType.SYSTEM_STATUS,
                level=level,
                title=title,
                message=message,
                metadata={'timestamp': datetime.now().isoformat()}
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send system alert: {e}")
            return False
    
    async def send_error_alert(self, error_message: str, error_type: str = "General Error") -> bool:
        """Send error alert"""
        try:
            alert = Alert(
                alert_id=f"error_{int(time.time())}",
                alert_type=AlertType.ERROR,
                level=AlertLevel.ERROR,
                title="🚨 System Error",
                message=f"**{error_type}**\n\n{error_message}",
                metadata={'error_type': error_type, 'timestamp': datetime.now().isoformat()}
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send error alert: {e}")
            return False
    
    async def send_warning_alert(self, warning_message: str, warning_type: str = "General Warning") -> bool:
        """Send warning alert"""
        try:
            alert = Alert(
                alert_id=f"warning_{int(time.time())}",
                alert_type=AlertType.WARNING,
                level=AlertLevel.WARNING,
                title="⚠️ System Warning",
                message=f"**{warning_type}**\n\n{warning_message}",
                metadata={'warning_type': warning_type, 'timestamp': datetime.now().isoformat()}
            )
            
            return await self._send_alert(alert)
            
        except Exception as e:
            log.error(f"Failed to send warning alert: {e}")
            return False
    
    # ========================================================================
    # CORE ALERT SENDING
    # ========================================================================
    
    async def _send_alert(self, alert: Alert) -> bool:
        """Send alert via configured channels"""
        try:
            # Check if alert level is enabled
            if not self.alert_levels_enabled.get(alert.level, False):
                return False
            
            # Check throttling
            if not self._check_alert_throttling(alert):
                return False
            
            # Send via Telegram if enabled
            if self.telegram_enabled:
                success = await self._send_telegram_alert(alert)
                if success:
                    self._track_alert(alert)
                    return True
            
            # Log alert if no other channels available
            log.info(f"Alert: {alert.title} - {alert.message}")
            self._track_alert(alert)
            return True
            
        except Exception as e:
            log.error(f"Failed to send alert: {e}")
            return False
    
    async def _send_telegram_alert(self, alert: Alert) -> bool:
        """Send alert via Telegram"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                return False
            
            # Format message
            message = self._format_telegram_message(alert)
            
            # Send to Telegram
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    log.debug(f"Telegram alert sent: {alert.alert_id}")
                    return True
                else:
                    log.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
            else:
                log.error(f"Telegram HTTP error: {response.status_code}")
            
            return False
            
        except Exception as e:
            log.error(f"Failed to send Telegram alert: {e}")
            return False
    
    async def _send_telegram_message(self, message: str, level: AlertLevel = AlertLevel.INFO) -> bool:
        """Send raw message via Telegram"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                return False
            
            # Send to Telegram
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    log.debug(f"Telegram message sent successfully")
                    return True
                else:
                    log.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
            else:
                log.error(f"Telegram HTTP error: {response.status_code}")
            
            return False
            
        except Exception as e:
            log.error(f"Failed to send Telegram message: {e}")
            return False
    
    # ========================================================================
    # MESSAGE FORMATTING
    # ========================================================================
    
    def _format_telegram_message(self, alert: Alert) -> str:
        """Format alert for Telegram"""
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "🚨",
            AlertLevel.CRITICAL: "🔥",
            AlertLevel.SUCCESS: "✅"
        }
        
        emoji = emoji_map.get(alert.level, "📢")
        timestamp = alert.timestamp.strftime("%H:%M:%S")
        
        message = f"{emoji} **{alert.title}**\n"
        message += f"🕐 {timestamp}\n\n"
        
        if alert.symbol:
            message += f"📈 **Symbol:** {alert.symbol}\n"
        
        if alert.strategy:
            message += f"🎯 **Strategy:** {alert.strategy}\n"
        
        if alert.confidence:
            message += f"🎲 **Confidence:** {alert.confidence:.1%}\n"
        
        if alert.expected_return:
            message += f"💰 **Expected Return:** {alert.expected_return:.2%}\n"
        
        message += f"\n{alert.message}"
        
        return message
    
    def _format_trade_signal_message(self, signal_data: Dict[str, Any]) -> str:
        """Format trade signal message"""
        symbol = signal_data.get('symbol', 'Unknown')
        strategy = signal_data.get('strategy', 'Unknown')
        confidence = signal_data.get('confidence', 0)
        expected_return = signal_data.get('expected_return', 0)
        entry_price = signal_data.get('entry_price', 0)
        
        message = f"**{symbol}** - {strategy} Strategy\n"
        message += f"🎯 **Entry Price:** ${entry_price:.2f}\n"
        message += f"🎲 **Confidence:** {confidence:.1%}\n"
        message += f"💰 **Expected Return:** {expected_return:.2%}\n"
        
        if signal_data.get('stop_loss'):
            message += f"🛑 **Stop Loss:** ${signal_data['stop_loss']:.2f}\n"
        
        if signal_data.get('take_profit'):
            message += f"🎯 **Take Profit:** ${signal_data['take_profit']:.2f}\n"
        
        return message
    
    def _format_trade_entry_message(self, trade_data: TradeAlert) -> str:
        """Format trade entry message"""
        message = f"**{trade_data.symbol}** - {trade_data.strategy}\n"
        message += f"✅ **{trade_data.action}** {trade_data.quantity} shares @ ${trade_data.price:.2f}\n"
        message += f"🎲 **Confidence:** {trade_data.confidence:.1%}\n"
        message += f"💰 **Expected Return:** {trade_data.expected_return:.2%}\n"
        
        if trade_data.stop_loss:
            message += f"🛑 **Stop Loss:** ${trade_data.stop_loss:.2f}\n"
        
        if trade_data.take_profit:
            message += f"🎯 **Take Profit:** ${trade_data.take_profit:.2f}\n"
        
        if trade_data.reason:
            message += f"📝 **Reason:** {trade_data.reason}\n"
        
        return message
    
    def _format_trade_exit_message(self, trade_data: TradeAlert, pnl_pct: float) -> str:
        """Format trade exit message"""
        pnl_emoji = "💰" if pnl_pct > 0 else "📉"
        
        message = f"**{trade_data.symbol}** - {trade_data.strategy}\n"
        message += f"🔚 **{trade_data.action}** {trade_data.quantity} shares @ ${trade_data.price:.2f}\n"
        message += f"{pnl_emoji} **P&L:** {pnl_pct:+.2f}%\n"
        
        if trade_data.reason:
            message += f"📝 **Reason:** {trade_data.reason}\n"
        
        return message
    
    def _format_performance_message(self, performance_data: Dict[str, Any]) -> str:
        """Format performance update message"""
        message = f"📊 **Performance Update**\n\n"
        
        if 'win_rate' in performance_data:
            message += f"🎯 **Win Rate:** {performance_data['win_rate']:.1%}\n"
        
        if 'total_pnl' in performance_data:
            message += f"💰 **Total P&L:** {performance_data['total_pnl']:.2%}\n"
        
        if 'active_positions' in performance_data:
            message += f"📈 **Active Positions:** {performance_data['active_positions']}\n"
        
        if 'daily_return' in performance_data:
            message += f"📅 **Daily Return:** {performance_data['daily_return']:.2%}\n"
        
        return message
    
    def _format_end_of_day_message(self, summary: PerformanceSummary) -> str:
        """Format end-of-day summary message with enhanced reporting"""
        # Determine performance emojis and status
        pnl_emoji = "✅" if summary.total_pnl > 0 else "📉"
        return_emoji = "📈" if summary.daily_return > 0 else "📉"
        
        # Calculate additional metrics
        avg_gain_per_trade = summary.total_pnl / summary.total_trades if summary.total_trades > 0 else 0
        max_drawdown = getattr(summary, 'max_drawdown', 0.0)
        capital_used_pct = getattr(summary, 'capital_used_pct', 0.0)
        consecutive_wins = getattr(summary, 'consecutive_wins', 0)
        
        # Calculate total P&L in dollars (approximate)
        total_pnl_dollars = getattr(summary, 'total_pnl_dollars', summary.total_pnl * 1000)  # Rough estimate
        
        message = f"⚖️ End of Day Trade Report\n"
        message += f"💹🛅 • Date: {summary.date.strftime('%Y-%m-%d')}\n\n"
        
        message += f"{pnl_emoji} {summary.total_pnl:+.2f}% ${total_pnl_dollars:+,.2f}\n"
        message += f"📈 • Total Trades: {summary.total_trades}\n"
        message += f"      • Win Rate: {summary.win_rate:.1%}\n"
        message += f"      • Max Drawdown: {max_drawdown:+.1f}%\n\n"
        
        # Highlights section
        message += f"⚡ Highlights\n"
        if consecutive_wins >= 3:
            message += f"🔰 Win streak: {consecutive_wins} consecutive wins\n"
        if summary.top_performers:
            best_trade = summary.top_performers[0]
            best_symbol = best_trade.get('symbol', 'N/A')
            best_return = best_trade.get('return', 0)
            message += f"👑 Biggest gain: {best_return:+.1f}% on {best_symbol}\n"
        message += "\n"
        
        # Risk metrics
        message += f"🛡 Risk Metrics\n"
        message += f"      • Capital Used: {capital_used_pct:.0f}%\n"
        message += f"      • Avg Gain per Trade: {avg_gain_per_trade:+.1f}%\n"
        message += f"      • Avg Risk per Trade: {getattr(summary, 'avg_risk_per_trade', 4.2):.1f}%\n\n"
        
        # Best and worst trades with detailed breakdown
        if summary.top_performers:
            best_trade = summary.top_performers[0]
            message += f"📈 Best Trade\n"
            message += f"👑 {best_trade.get('symbol', 'N/A')} ({best_trade.get('side', 'LONG')}) — "
            message += f"{best_trade.get('return', 0):+.1f}% ${best_trade.get('pnl_dollars', 0):+.2f} • "
            message += f"Duration: {best_trade.get('duration', 'N/A')}\n"
            message += f"      • Entry: {best_trade.get('entry_price', 'N/A')} @ {best_trade.get('entry_time', 'N/A')}\n"
            message += f"      • Exit: {best_trade.get('exit_price', 'N/A')} @ {best_trade.get('exit_time', 'N/A')}\n"
            message += f"      • Entry Reason: {best_trade.get('entry_reason', 'N/A')}\n"
            message += f"      • Exit Reason: {best_trade.get('exit_reason', 'N/A')}\n\n"
        
        if summary.worst_performers:
            worst_trade = summary.worst_performers[0]
            message += f"💢 Worst Trade\n"
            message += f"📛 {worst_trade.get('symbol', 'N/A')} ({worst_trade.get('side', 'SHORT')}) — "
            message += f"{worst_trade.get('return', 0):+.1f}% ${worst_trade.get('pnl_dollars', 0):+.2f} • "
            message += f"Duration: {worst_trade.get('duration', 'N/A')}\n"
            message += f"      • Entry: {worst_trade.get('entry_price', 'N/A')} @ {worst_trade.get('entry_time', 'N/A')}\n"
            message += f"      • Exit: {worst_trade.get('exit_price', 'N/A')} @ {worst_trade.get('exit_time', 'N/A')}\n"
            message += f"      • Entry Reason: {worst_trade.get('entry_reason', 'N/A')}\n"
            message += f"      • Exit Reason: {worst_trade.get('exit_reason', 'N/A')}\n\n"
        
        # Summary
        message += f"✨ Summary\n"
        if summary.win_rate >= 0.8:
            message += f"📈 Strong execution with disciplined risk. "
        elif summary.win_rate >= 0.6:
            message += f"📊 Solid performance with room for optimization. "
        else:
            message += f"⚠️ Challenging session - reviewing strategy. "
        
        if summary.total_pnl > 2.0:
            message += f"Momentum signals lined up with sentiment confluence."
        elif summary.total_pnl > 0:
            message += f"Positive day with controlled risk management."
        else:
            message += f"Risk management prevented larger losses."
        
        return message
    
    # ========================================================================
    # END OF DAY SCHEDULING
    # ========================================================================
    
    def start_end_of_day_scheduler(self):
        """Start the end-of-day summary scheduler"""
        if self.scheduler_running:
            log.warning("End-of-day scheduler is already running")
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        log.info("End-of-day scheduler started - will send summary at 4:00 PM ET (market close)")
    
    def stop_end_of_day_scheduler(self):
        """Stop the end-of-day summary scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        log.info("End-of-day scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a background thread"""
        while self.scheduler_running:
            # Get current time in Eastern Time (market timezone)
            from zoneinfo import ZoneInfo
            et_tz = ZoneInfo('America/New_York')
            current_time = datetime.now(et_tz)
            
            # Check if it's market close time (4:00 PM ET)
            if current_time.hour == 16 and current_time.minute == 0:
                # Check if we haven't sent today's summary yet
                today = current_time.date()
                last_summary_date = getattr(self, '_last_summary_date', None)
                
                if last_summary_date != today:
                    self._send_scheduled_end_of_day_summary()
                    self._last_summary_date = today
            
            time.sleep(60)  # Check every minute
    
    def _send_scheduled_end_of_day_summary(self):
        """Send the scheduled end-of-day summary"""
        try:
            log.info("Generating scheduled end-of-day summary")
            
            # Check if we're in Demo Mode
            demo_mode = get_config_value('TRADING_MODE', 'demo').lower() in ['demo', 'demo_mode']
            
            if demo_mode and hasattr(self, '_mock_executor') and self._mock_executor:
                # Generate Demo Mode EOD report
                asyncio.run(self._send_demo_eod_summary())
            else:
                # Create performance summary from today's trades
                summary = self._create_daily_performance_summary()
                
                # Send the summary
                asyncio.run(self.send_end_of_day_summary(summary))
            
            log.info("Scheduled end-of-day summary sent successfully")
            
        except Exception as e:
            log.error(f"Failed to send scheduled end-of-day summary: {e}")
    
    async def _send_demo_eod_summary(self):
        """Send Demo Mode end-of-day summary"""
        try:
            if not hasattr(self, '_mock_executor') or not self._mock_executor:
                log.warning("No mock executor available for Demo EOD summary")
                return
            
            # Generate mock executor EOD report
            report = await self._mock_executor.generate_end_of_day_report()
            
            # Send as Telegram alert
            await self._send_telegram_message(report, AlertLevel.INFO)
            
            log.info("Demo Mode EOD summary sent successfully")
            
        except Exception as e:
            log.error(f"Failed to send Demo Mode EOD summary: {e}")
    
    def _create_daily_performance_summary(self) -> PerformanceSummary:
        """Create a performance summary from today's trades"""
        today = datetime.now().date()
        
        # Check if we're in Demo Mode and get mock trades
        demo_mode = get_config_value('TRADING_MODE', 'demo').lower() in ['demo', 'demo_mode']
        mock_trades = []
        
        if demo_mode:
            # Get mock trades from the trading system if available
            try:
                from .prime_trading_system import PrimeTradingSystem
                # This is a bit of a hack - we need a better way to access mock executor
                # For now, we'll check if there are any mock trades in the system
                pass
            except:
                pass
        
        # Filter trades from today (both real and mock)
        today_trades = [trade for trade in self.trade_history 
                       if trade.get('date', datetime.now()).date() == today]
        
        # Add mock trades if in Demo Mode
        if demo_mode and hasattr(self, '_mock_executor') and self._mock_executor:
            mock_closed_trades = getattr(self._mock_executor, 'closed_trades', [])
            for mock_trade in mock_closed_trades:
                if hasattr(mock_trade, 'timestamp') and mock_trade.timestamp.date() == today:
                    today_trades.append({
                        'date': mock_trade.timestamp,
                        'symbol': mock_trade.symbol,
                        'side': mock_trade.side.value,
                        'entry_price': mock_trade.entry_price,
                        'exit_price': mock_trade.exit_price,
                        'quantity': mock_trade.quantity,
                        'pnl': mock_trade.pnl,
                        'exit_reason': mock_trade.exit_reason,
                        'is_mock': True
                    })
        
        if not today_trades:
            # Return empty summary if no trades today
            return PerformanceSummary(
                date=datetime.now(),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                daily_return=0.0,
                active_positions=0,
                signals_generated=0,
                signals_accepted=0,
                acceptance_rate=0.0,
                total_pnl_dollars=0.0
            )
        
        # Calculate metrics
        total_trades = len(today_trades)
        winning_trades = len([t for t in today_trades if t.get('pnl', 0) > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        total_pnl = sum(t.get('pnl', 0) for t in today_trades)
        total_pnl_dollars = sum(t.get('pnl_dollars', 0) for t in today_trades)
        
        # Get top and worst performers
        sorted_trades = sorted(today_trades, key=lambda x: x.get('pnl', 0), reverse=True)
        top_performers = sorted_trades[:3] if sorted_trades else []
        worst_performers = sorted_trades[-2:] if len(sorted_trades) >= 2 else []
        
        # Calculate consecutive wins
        consecutive_wins = 0
        for trade in reversed(sorted_trades):
            if trade.get('pnl', 0) > 0:
                consecutive_wins += 1
            else:
                break
        
        return PerformanceSummary(
            date=datetime.now(),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            daily_return=total_pnl,  # Same as total_pnl for daily
            active_positions=len([t for t in today_trades if t.get('status') == 'open']),
            signals_generated=len(self.alert_history),  # Approximate
            signals_accepted=total_trades,
            acceptance_rate=total_trades / len(self.alert_history) if self.alert_history else 0.0,
            max_drawdown=self._calculate_max_drawdown(today_trades),
            capital_used_pct=self._calculate_capital_used_pct(),
            consecutive_wins=consecutive_wins,
            avg_risk_per_trade=4.2,  # Default value
            total_pnl_dollars=total_pnl_dollars,
            top_performers=top_performers,
            worst_performers=worst_performers
        )
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown from trades"""
        if not trades:
            return 0.0
        
        peak = 0.0
        max_dd = 0.0
        running_pnl = 0.0
        
        for trade in trades:
            running_pnl += trade.get('pnl', 0)
            if running_pnl > peak:
                peak = running_pnl
            dd = peak - running_pnl
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_capital_used_pct(self) -> float:
        """Calculate percentage of capital used"""
        # This would need to be calculated based on account balance and position sizes
        # For now, return a default value
        return 82.0
    
    def add_trade_to_history(self, trade_data: Dict[str, Any]):
        """Add a trade to the daily history for end-of-day summary"""
        trade_data['date'] = datetime.now()
        self.trade_history.append(trade_data)
        
        # Keep only last 30 days of trades
        cutoff_date = datetime.now() - timedelta(days=30)
        self.trade_history = [t for t in self.trade_history 
                            if t.get('date', datetime.now()) > cutoff_date]
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _check_alert_throttling(self, alert: Alert) -> bool:
        """Check if alert should be throttled"""
        current_time = time.time()
        alert_key = f"{alert.alert_type.value}_{alert.level.value}"
        
        # Check cooldown
        if current_time - self.last_alert_time.get(alert_key, 0) < self.alert_cooldown_seconds:
            return False
        
        # Check rate limiting
        minute_key = f"{alert_key}_{current_time // 60}"
        if self.alert_counts[minute_key] >= self.max_alerts_per_minute:
            return False
        
        self.last_alert_time[alert_key] = current_time
        self.alert_counts[minute_key] += 1
        
        return True
    
    def _track_alert(self, alert: Alert):
        """Track alert for analytics"""
        self.alert_history.append(alert)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        if not self.alert_history:
            return {}
        
        stats = {
            'total_alerts': len(self.alert_history),
            'alerts_by_type': defaultdict(int),
            'alerts_by_level': defaultdict(int),
            'recent_alerts': []
        }
        
        for alert in self.alert_history:
            stats['alerts_by_type'][alert.alert_type.value] += 1
            stats['alerts_by_level'][alert.level.value] += 1
        
        # Get recent alerts (last 10)
        stats['recent_alerts'] = [
            {
                'type': alert.alert_type.value,
                'level': alert.level.value,
                'title': alert.title,
                'timestamp': alert.timestamp.isoformat()
            }
            for alert in list(self.alert_history)[-10:]
        ]
        
        return stats
    
    # ============================================================================
    # OAUTH ALERT METHODS
    # ============================================================================
    
    
    async def send_oauth_renewal_success(self, environment: str, token_valid: bool = True) -> bool:
        """
        Send OAuth token renewal success notification
        
        Args:
            environment: Environment (prod or sandbox)
            token_valid: Whether token has been confirmed valid (default: True)
            
        Returns:
            True if alert sent successfully
            
        Note:
            Only sends success alert if token_valid is True.
            If token_valid is False, this method returns False without sending.
        """
        try:
            # Only send success alert if token is confirmed valid
            if not token_valid:
                log.warning(f"Token renewal completed but token is INVALID for {environment} - skipping success alert")
                return False
            
            # Get current time in Pacific Time and Eastern Time
            from zoneinfo import ZoneInfo
            pt_tz = ZoneInfo('America/Los_Angeles')
            et_tz = ZoneInfo('America/New_York')
            now_pt = datetime.now(pt_tz)
            now_et = datetime.now(et_tz)
            
            # Format times properly
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            # Determine system mode based on environment
            if environment.lower() == 'prod':
                system_mode = "Live Trading Enabled"
                env_label = "Production"
            else:
                system_mode = "Sandbox Testing Mode"
                env_label = "Sandbox"
            
            message = f"""===========================================================

✅ OAuth {env_label} Token Renewed — {pt_time} ({et_time})

🎉 Success! E*TRADE {environment.lower()} token successfully renewed for {'Live' if environment.lower() == 'prod' else 'Demo'}

📊 System Mode: {system_mode}
💎 Status: Trading system ready and operational

🌐 Public Dashboard: https://easy-trading-oauth-v2.web.app"""
            
            success = await self._send_telegram_message(message, AlertLevel.SUCCESS)
            
            if success:
                # Update OAuth status
                self.oauth_status[environment]['last_renewed'] = datetime.now()
                self.oauth_status[environment]['is_valid'] = True
                log.info(f"OAuth renewal success alert sent for {environment}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth renewal success alert: {e}")
            return False
    
    async def send_oauth_renewal_error(self, environment: str, error_message: str) -> bool:
        """Send OAuth token renewal error notification"""
        try:
            message = f"""❌ OAuth Token Renewal Failed

🔐 Environment: {environment.upper()}
⏰ Time: {datetime.now().strftime('%I:%M %p ET')}
🚨 Error: {error_message}

🔧 Please check the OAuth web app and try again
🔗 URL: {self.oauth_renewal_url}/oauth/start?env={environment}"""
            
            success = await self._send_telegram_message(message, AlertLevel.ERROR)
            
            if success:
                # Update OAuth status
                self.oauth_status[environment]['is_valid'] = False
                log.info(f"OAuth renewal error alert sent for {environment}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth renewal error alert: {e}")
            return False
    
    async def send_oauth_token_expired_alert(self, environment: str) -> bool:
        """
        Send OAuth token expired alert when token is confirmed expired
        
        Args:
            environment: Environment (prod or sandbox)
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Get current time in Pacific Time
            from zoneinfo import ZoneInfo
            pt_tz = ZoneInfo('America/Los_Angeles')
            now_pt = datetime.now(pt_tz)
            
            # Determine system mode based on environment
            if environment.lower() == 'prod':
                env_label = "Production"
                impact = "Live trading disabled until token renewed"
            else:
                env_label = "Sandbox"
                impact = "Sandbox testing disabled until token renewed"
            
            # Get Eastern Time for comparison
            et_tz = ZoneInfo('America/New_York')
            now_et = datetime.now(et_tz)
            
            # Format the OAuth alert message with proper time formatting
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            message = f"""===========================================================

⚠️ <b>OAuth {env_label} Token Expired —</b> {pt_time} ({et_time})

🚨 <b>Token Status:</b> E*TRADE {environment.lower()} token is EXPIRED ❌
⏰ <b>Detected:</b> {pt_time} ({et_time})

🌐 <b>Public Dashboard:</b> https://easy-trading-oauth-v2.web.app
🦜💼 <b>Management Portal:</b> https://easy-trading-oauth-v2.web.app/manage.html

⚠️ <b>Impact:</b> {impact}

👉 <b>Action Required:</b>
1. Visit the public dashboard
2. Click "Renew {env_label}"
3. Enter access code (easy2025) on management portal
4. Complete OAuth authorization
5. Token will be renewed and stored"""
            
            success = await self._send_telegram_message(message, AlertLevel.ERROR)
            
            if success:
                # Update OAuth status
                self.oauth_status[environment]['is_valid'] = False
                log.info(f"OAuth token expired alert sent for {environment}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth token expired alert: {e}")
            return False
    
    async def send_oauth_warning(self, environment: str, warning_message: str) -> bool:
        """Send OAuth token warning notification"""
        try:
            message = f"""⚠️ OAuth Token Warning

🔐 Environment: {environment.upper()}
⏰ Time: {datetime.now().strftime('%I:%M %p ET')}
⚠️ Warning: {warning_message}

🔧 Please check token status
🔗 URL: {self.oauth_renewal_url}"""
            
            success = await self.send_alert(
                AlertType.OAUTH_WARNING,
                AlertLevel.WARNING,
                "OAuth Token Warning",
                message
            )
            
            if success:
                log.info(f"OAuth warning alert sent for {environment}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth warning alert: {e}")
            return False
    
    def update_oauth_status(self, environment: str, is_valid: bool, last_renewed: datetime = None):
        """Update OAuth token status"""
        try:
            self.oauth_status[environment]['is_valid'] = is_valid
            if last_renewed:
                self.oauth_status[environment]['last_renewed'] = last_renewed
            else:
                self.oauth_status[environment]['last_renewed'] = datetime.now()
            
            log.info(f"OAuth status updated for {environment}: valid={is_valid}")
            
        except Exception as e:
            log.error(f"Error updating OAuth status: {e}")
    
    def get_oauth_status(self, environment: str) -> Dict[str, Any]:
        """Get current OAuth status for environment"""
        return self.oauth_status.get(environment, {
            'last_renewed': None,
            'is_valid': False,
            'expires_at': None
        })
    
    async def check_oauth_token_health(self) -> Dict[str, bool]:
        """Check OAuth token health for all environments"""
        try:
            health_status = {}
            
            for env in ['prod', 'sandbox']:
                status = self.get_oauth_status(env)
                
                # Check if token is valid and recently renewed
                is_healthy = (
                    status['is_valid'] and 
                    status['last_renewed'] and 
                    (datetime.now() - status['last_renewed']).total_seconds() < 86400  # 24 hours
                )
                
                health_status[env] = is_healthy
                
                # Send warning if token is unhealthy
                if not is_healthy and status['last_renewed']:
                    await self.send_oauth_warning(
                        env, 
                        f"Token may be expired or invalid. Last renewed: {status['last_renewed']}"
                    )
            
            return health_status
            
        except Exception as e:
            log.error(f"Error checking OAuth token health: {e}")
            return {'prod': False, 'sandbox': False}
    
    async def schedule_oauth_morning_alert(self) -> bool:
        """Schedule OAuth morning alert (called by Cloud Scheduler)"""
        try:
            if not self.oauth_enabled:
                log.info("OAuth alerts disabled, skipping morning alert scheduling")
                return False
            
            # This method is called by Cloud Scheduler at 8:30 AM ET
            success = await self.send_oauth_morning_alert()
            
            if success:
                log.info("OAuth morning alert scheduled and sent")
            else:
                log.error("Failed to send scheduled OAuth morning alert")
            
            return success
            
        except Exception as e:
            log.error(f"Error in scheduled OAuth morning alert: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the alert manager"""
        log.info("Prime Alert Manager shutting down...")
        
        # Send shutdown notification
        await self.send_system_alert(
            "🔌 System Shutdown",
            "ETrade Strategy system is shutting down gracefully.",
            AlertLevel.INFO
        )
    
    async def send_oauth_alert(self, title: str, message: str, level: AlertLevel = AlertLevel.INFO) -> bool:
        """
        Send OAuth-related alert
        
        Args:
            title: Alert title
            message: Alert message
            level: Alert level
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Format OAuth alert
            formatted_message = f"🔐 **OAuth Alert**\n\n**{title}**\n\n{message}"
            
            # Send alert
            success = await self._send_telegram_message(formatted_message, level)
            
            if success:
                log.info(f"OAuth alert sent: {title}")
            else:
                log.warning(f"Failed to send OAuth alert: {title}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth alert: {e}")
            return False
    
    async def send_oauth_morning_alert(self) -> bool:
        """
        Send OAuth renewal alert at 9:01pm PT (12:01am ET)
        
        Returns:
            True if alert sent successfully
        """
        try:
            # Get current time in Pacific Time
            from zoneinfo import ZoneInfo
            pt_tz = ZoneInfo('America/Los_Angeles')
            now_pt = datetime.now(pt_tz)
            
            # Check if it's 9:00pm PT (exactly when tokens expire at midnight ET)
            if now_pt.hour == 21 and now_pt.minute == 0:
                log.info("Sending OAuth renewal alert - tokens just expired")
            else:
                log.info(f"OAuth alert time check: {now_pt.strftime('%I:%M %p PT')} (waiting for 9:00 PM PT)")
                return False
            
            # Get Eastern Time for comparison
            et_tz = ZoneInfo('America/New_York')
            now_et = datetime.now(et_tz)
            
            # Format the OAuth alert message with proper time formatting
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            # Create OAuth alert message
            message = f"""===========================================================

🌙 OAuth Token Renewal Alert — {pt_time} ({et_time})

⚠️ E*TRADE tokens just expired at midnight ET (just now)

🌐 Public Dashboard: https://easy-trading-oauth-v2.web.app

🪙 Renewal required ♻️"""

            success = await self._send_telegram_message(message, AlertLevel.WARNING)
            
            if success:
                log.info("Morning OAuth alert sent successfully")
            else:
                log.warning("Failed to send morning OAuth alert")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending morning OAuth alert: {e}")
            return False
    
    async def send_oauth_warning(self, environment: str, message: str) -> bool:
        """
        Send OAuth warning alert
        
        Args:
            environment: Environment (sandbox/prod)
            message: Warning message
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Format warning message
            formatted_message = f"""⚠️ **OAuth Warning** - {environment.upper()}

{message}

**Environment**: {environment}
**Time**: {datetime.now().strftime('%I:%M %p ET')}
**Action**: Check OAuth status and renew if needed"""

            success = await self._send_telegram_message(formatted_message, AlertLevel.WARNING)
            
            if success:
                log.info(f"OAuth warning sent for {environment}")
            else:
                log.warning(f"Failed to send OAuth warning for {environment}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth warning: {e}")
            return False
    
    async def send_oauth_token_renewed_confirmation(self, environment: str) -> bool:
        """
        Send OAuth token renewal confirmation alert when tokens are successfully renewed
        
        Args:
            environment: Environment (sandbox/prod)
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Get current time in Pacific Time and Eastern Time
            from zoneinfo import ZoneInfo
            pt_tz = ZoneInfo('America/Los_Angeles')
            et_tz = ZoneInfo('America/New_York')
            now_pt = datetime.now(pt_tz)
            now_et = datetime.now(et_tz)
            
            # Format times properly
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            # Determine environment labels
            if environment.lower() == 'prod':
                env_label = "Production"
                system_mode = "Live Trading Enabled"
            else:
                env_label = "Sandbox"
                system_mode = "Demo Mode Available"
            
            # Determine environment-specific details
            if environment.lower() == 'prod':
                token_type = "production token successfully renewed for Live"
            else:
                token_type = "sandbox token successfully renewed for Demo"
            
            message = f"""===========================================================

✅ OAuth {env_label} Token Renewed — {pt_time} ({et_time})

🎉 Success! E*TRADE {token_type}

📊 System Mode: {system_mode}
💎 Status: Trading system ready and operational

🌐 Public Dashboard: https://easy-trading-oauth-v2.web.app"""
            
            success = await self._send_telegram_message(message, AlertLevel.SUCCESS)
            
            if success:
                log.info(f"OAuth {environment} token renewal confirmation sent")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth token renewal confirmation: {e}")
            return False

    async def send_oauth_success(self, environment: str, message: str) -> bool:
        """
        Send OAuth success alert
        
        Args:
            environment: Environment (sandbox/prod)
            message: Success message
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Format success message
            formatted_message = f"""✅ **OAuth Success** - {environment.upper()}

{message}

**Environment**: {environment}
**Time**: {datetime.now().strftime('%I:%M %p ET')}
**Status**: Active and ready for trading"""

            success = await self._send_telegram_message(formatted_message, AlertLevel.SUCCESS)
            
            if success:
                log.info(f"OAuth success alert sent for {environment}")
            else:
                log.warning(f"Failed to send OAuth success alert for {environment}")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth success alert: {e}")
            return False
    
    async def send_buy_signal_alert(self, symbol: str, company_name: str, shares: int,
                                   entry_price: float, total_value: float, confidence: float,
                                   expected_return: float, quality_score: float,
                                   strategies_agreeing: str, stop_loss: float,
                                   take_profit: float, note: str = "") -> bool:
        """Send buy signal alert with comprehensive details"""
        try:
            # Determine confidence emoji
            if confidence >= 0.98:
                emoji = "🔰🔰🔰"
            elif confidence >= 0.85:
                emoji = "🔰🔰"
            elif confidence >= 0.70:
                emoji = "🔰"
            elif confidence >= 0.60:
                emoji = "📟"
            else:
                emoji = "🟡"
            
            message = f"""📈 <b>BUY SIGNAL - {symbol}</b> {emoji}

📊 <b>BUY</b> - {shares} shares - {company_name}
• Entry: ${entry_price:.2f}
• Total Value: ${total_value:.2f}

💼 <b>POSITION DETAILS:</b>
Symbol: {symbol}
Confidence: {confidence:.0%}
Expected Return: {expected_return:.1%}
Quality Score: {quality_score:.0%}

📊 <b>RISK MANAGEMENT:</b>
Stop Loss: ${stop_loss:.2f} ({((stop_loss - entry_price) / entry_price * 100):.1f}%)
Take Profit: ${take_profit:.2f} ({((take_profit - entry_price) / entry_price * 100):.1f}%)

⏰ <b>Entry Time:</b> {datetime.utcnow().strftime('%H:%M:%S')} UTC"""
            
            if note:
                message += f"\n\n{note}"
            
            return await self._send_telegram_message(message, AlertLevel.SUCCESS)
            
        except Exception as e:
            log.error(f"Failed to send buy signal alert: {e}")
            return False
    
    async def send_sell_signal_alert(self, symbol: str, company_name: str, shares: int,
                                     entry_price: float, exit_price: float, total_pnl: float,
                                     pnl_pct: float, duration_minutes: float, exit_reason: str,
                                     note: str = "") -> bool:
        """Send sell signal alert with P&L details"""
        try:
            pnl_emoji = "💰" if total_pnl > 0 else "📉"
            
            message = f"""📉 <b>SELL SIGNAL - {symbol}</b>

📊 <b>SELL</b> - {shares} shares - {company_name}
• Exit: ${exit_price:.2f}

💼 <b>POSITION CLOSED:</b>
Entry: ${entry_price:.2f}
Exit: ${exit_price:.2f}
P&L: {pnl_emoji} ${total_pnl:+.2f} ({pnl_pct:+.2f}%)
Duration: {duration_minutes:.0f} minutes

🎯 <b>EXIT REASON:</b>
{exit_reason}

⏰ <b>Exit Time:</b> {datetime.utcnow().strftime('%H:%M:%S')} UTC"""
            
            if note:
                message += f"\n\n{note}"
            
            return await self._send_telegram_message(message, AlertLevel.SUCCESS)
            
        except Exception as e:
            log.error(f"Failed to send sell signal alert: {e}")
            return False
    
    async def send_telegram_alert(self, message: str, level: AlertLevel = AlertLevel.INFO) -> bool:
        """Public method to send raw Telegram message"""
        return await self._send_telegram_message(message, level)
    
    async def send_oauth_market_open_alert(self) -> bool:
        """
        Send OAuth market open alert at 5:30 AM PT (8:30 AM ET) - 1 hour before market open
        Only sends if tokens are actually invalid at that time
        
        Returns:
            True if alert sent successfully
        """
        try:
            if not self.oauth_enabled:
                log.info("OAuth alerts disabled, skipping market open alert")
                return False
            
            # Get current time in Pacific Time and Eastern Time
            from zoneinfo import ZoneInfo
            pt_tz = ZoneInfo('America/Los_Angeles')
            et_tz = ZoneInfo('America/New_York')
            now_pt = datetime.now(pt_tz)
            now_et = datetime.now(et_tz)
            
            # Format times properly
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            # Check if it's 5:30 AM PT (8:30 AM ET) - 1 hour before market open
            if now_pt.hour == 5 and now_pt.minute == 30:
                log.info("Checking token status before market open")
            else:
                log.info(f"Market open alert time check: {pt_time} (waiting for 5:30 AM PT)")
                return False
            
            # Check token status via Secret Manager directly
            # Since we're in Demo Mode, we only need sandbox tokens to be valid
            prod_valid = False
            sandbox_valid = False
            
            try:
                # Import Secret Manager OAuth integration
                from modules.etrade_oauth_integration import get_etrade_oauth_integration
                
                # Check sandbox token (required for Demo Mode)
                sandbox_oauth = get_etrade_oauth_integration('sandbox')
                if sandbox_oauth and sandbox_oauth.is_authenticated():
                    sandbox_valid = True
                    log.info("Sandbox tokens are valid - Demo Mode can proceed")
                else:
                    log.info("Sandbox tokens are invalid - Demo Mode cannot proceed")
                
                # Check production token (optional for Demo Mode)
                prod_oauth = get_etrade_oauth_integration('prod')
                if prod_oauth and prod_oauth.is_authenticated():
                    prod_valid = True
                    log.info("Production tokens are valid - Live Mode available")
                else:
                    log.info("Production tokens are invalid - Live Mode not available")
                
                # For Demo Mode, we only need sandbox tokens
                if sandbox_valid:
                    log.info("Demo Mode can proceed with sandbox tokens - skipping market open alert")
                    return False
                else:
                    log.info("Demo Mode cannot proceed - sandbox tokens invalid")
                    
            except Exception as oauth_error:
                log.error(f"Failed to check token status via OAuth integration: {oauth_error}")
                # If we can't check status, err on the side of caution and send alert
                log.info("Unable to verify token status - sending market open alert as precaution")
            
            # Only reach here if production tokens are invalid or we can't verify status
            if sandbox_valid:
                # Sandbox is valid - system will run in demo mode
                message = f"""===========================================================

🌅 <b>OAuth Market Open Alert —</b> {now_pt.strftime('%I:%M %p PT')}

📝 <b>REMINDER:</b> Market opens in <b>1 hour</b> - OAuth Sandbox token is INVALID

🌐 <b>Public Dashboard:</b> https://easy-trading-oauth-v2.web.app

⚠️ <b>Status:</b> Pre-Market Check → Production Token INVALID
🛡️ <b>Status:</b> Demo Token VALID
🛠 <b>Trading Mode:</b> Demo Sandbox (Testing Mode)

📝 <b>Reminder:</b> Market opens in <b>1 hour</b>
📈 <b>Market Opens:</b> 9:30 AM ET (6:30 AM PT)
🕒 <b>Current Time:</b> {now_pt.strftime('%I:%M %p PT')} (8:30 AM ET)

✅ <b>System Status:</b> Trading system active in Sandbox
🔎 <b>Scanning & Signals:</b> Running (sandbox token valid)
📊 <b>Data & Analysis:</b> Fully functional"""
            else:
                # Neither token is valid - system cannot function
                message = f"""===========================================================

🌅 OAuth Market Open Alert — {pt_time} ({et_time})

🚨 URGENT: Market opens in 1 hour - OAuth Production token is INVALID

🌐 Public Dashboard: https://easy-trading-oauth-v2.web.app

🚫 Trading System: Cannot start until tokens are valid

🚨 System Status: Trading system BLOCKED
❌ All Operations: Suspended (no valid tokens)
⚠️ Risk Level: HIGH - No trading capability"""

            success = await self._send_telegram_message(message, AlertLevel.ERROR)
            
            if success:
                log.info("OAuth market open alert sent successfully")
            else:
                log.warning("Failed to send OAuth market open alert")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending OAuth market open alert: {e}")
            return False
    
    # ============================================================================
    # TRADING PIPELINE ALERT METHODS
    # ============================================================================
    
    async def send_watchlist_created_alert(self, symbol_count: int, watchlist_type: str = "daily") -> bool:
        """
        Send alert when daily watchlist is created
        
        Args:
            symbol_count: Number of symbols in the watchlist
            watchlist_type: Type of watchlist (daily, dynamic, etc.)
            
        Returns:
            True if alert sent successfully
        """
        try:
            from zoneinfo import ZoneInfo
            
            # Get current time
            pt_tz = ZoneInfo('America/Los_Angeles')
            et_tz = ZoneInfo('America/New_York')
            now_pt = datetime.now(pt_tz)
            now_et = datetime.now(et_tz)
            
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            message = f"""===========================================================

📋 Daily Watchlist Created — {pt_time} ({et_time})

🎯 Watchlist Status: {symbol_count} symbols loaded
📊 Watchlist Type: {watchlist_type.title()}
⏰ Created at: {pt_time} ({et_time})

✅ System Status: Watchlist building complete
🔍 Next Step: Symbol selection and analysis"""
            
            success = await self._send_telegram_message(message, AlertLevel.INFO)
            
            if success:
                log.info(f"Watchlist created alert sent - {symbol_count} symbols")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending watchlist created alert: {e}")
            return False
    
    async def send_symbol_selection_alert(self, selected_symbols: list, total_analyzed: int) -> bool:
        """
        Send alert when symbol selection is completed
        
        Args:
            selected_symbols: List of selected symbols for trading
            total_analyzed: Total number of symbols analyzed
            
        Returns:
            True if alert sent successfully
        """
        try:
            from zoneinfo import ZoneInfo
            
            # Get current time
            pt_tz = ZoneInfo('America/Los_Angeles')
            et_tz = ZoneInfo('America/New_York')
            now_pt = datetime.now(pt_tz)
            now_et = datetime.now(et_tz)
            
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            selected_count = len(selected_symbols)
            symbols_text = ", ".join(selected_symbols[:5])  # Show first 5 symbols
            if len(selected_symbols) > 5:
                symbols_text += f" (+{len(selected_symbols) - 5} more)"
            
            message = f"""===========================================================

🎯 Symbol Selection Complete — {pt_time} ({et_time})

📊 Analysis Results: {selected_count}/{total_analyzed} symbols selected
🔍 Selected Symbols: {symbols_text}
⏰ Selection Time: {pt_time} ({et_time})

✅ System Status: Symbol analysis complete
🔍 Next Step: Multi-strategy analysis"""
            
            success = await self._send_telegram_message(message, AlertLevel.INFO)
            
            if success:
                log.info(f"Symbol selection alert sent - {selected_count}/{total_analyzed} symbols selected")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending symbol selection alert: {e}")
            return False
    
    async def send_multi_strategy_analysis_alert(self, symbol: str, strategy_results: dict, has_signals: bool) -> bool:
        """
        Send alert when multi-strategy analysis is completed for a symbol
        ONLY sends alert if signals are approved (has_signals=True)
        
        Args:
            symbol: Symbol being analyzed
            strategy_results: Results from multi-strategy analysis
            has_signals: Whether any strategies generated signals
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Only send alert if signals are approved
            if not has_signals:
                log.debug(f"Multi-strategy analysis for {symbol} - no signals approved, skipping alert")
                return True  # Return True to indicate "handled" but don't send alert
            
            from zoneinfo import ZoneInfo
            
            # Get current time
            pt_tz = ZoneInfo('America/Los_Angeles')
            et_tz = ZoneInfo('America/New_York')
            now_pt = datetime.now(pt_tz)
            now_et = datetime.now(et_tz)
            
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            # Count strategies that recommend trading
            trading_strategies = []
            for strategy_name, result in strategy_results.items():
                if hasattr(result, 'should_trade') and result.should_trade:
                    trading_strategies.append(strategy_name)
            
            trading_count = len(trading_strategies)
            
            message = f"""===========================================================

🧠 Multi-Strategy Analysis — {pt_time} ({et_time})

📊 Symbol: {symbol}
🎯 Strategy Results: {trading_count} strategies recommend trading
✅ Signals Generated
⏰ Analysis Time: {pt_time} ({et_time})

✅ System Status: Multi-strategy analysis complete
🔍 Next Step: Signal generation"""
            
            success = await self._send_telegram_message(message, AlertLevel.INFO)
            
            if success:
                log.info(f"Multi-strategy analysis alert sent for {symbol} - {trading_count} trading strategies approved")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending multi-strategy analysis alert: {e}")
            return False
    
    async def send_signal_generator_alert(self, symbol: str, signal_generated: bool, signal_quality: str = None) -> bool:
        """
        Send alert when signal generator processes a symbol
        ONLY sends alert if a signal is actually generated
        
        Args:
            symbol: Symbol being processed
            signal_generated: Whether a signal was generated
            signal_quality: Quality of the generated signal
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Only send alert if signal is generated
            if not signal_generated:
                log.debug(f"Signal generator for {symbol} - no signal generated, skipping alert")
                return True  # Return True to indicate "handled" but don't send alert
            
            from zoneinfo import ZoneInfo
            
            # Get current time
            pt_tz = ZoneInfo('America/Los_Angeles')
            et_tz = ZoneInfo('America/New_York')
            now_pt = datetime.now(pt_tz)
            now_et = datetime.now(et_tz)
            
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            quality_text = f" (Quality: {signal_quality})" if signal_quality else ""
            
            message = f"""===========================================================

📡 Signal Generator Processing — {pt_time} ({et_time})

📊 Symbol: {symbol}
🎯 Signal Status: ✅ BUY Signal Generated{quality_text}
⏰ Processing Time: {pt_time} ({et_time})

✅ System Status: Signal generation complete
🔍 Next Step: Trade execution"""
            
            success = await self._send_telegram_message(message, AlertLevel.INFO)
            
            if success:
                log.info(f"Signal generator alert sent for {symbol} - BUY Signal Generated")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending signal generator alert: {e}")
            return False
    
    async def send_mock_executor_alert(self, symbol: str, trade_executed: bool, trade_id: str = None) -> bool:
        """
        Send alert when mock trading executor processes a trade
        ONLY sends alert if a trade is actually executed
        
        Args:
            symbol: Symbol being traded
            trade_executed: Whether a trade was executed
            trade_id: ID of the executed trade
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Only send alert if trade is executed
            if not trade_executed:
                log.debug(f"Mock executor for {symbol} - no trade executed, skipping alert")
                return True  # Return True to indicate "handled" but don't send alert
            
            from zoneinfo import ZoneInfo
            
            # Get current time
            pt_tz = ZoneInfo('America/Los_Angeles')
            et_tz = ZoneInfo('America/New_York')
            now_pt = datetime.now(pt_tz)
            now_et = datetime.now(et_tz)
            
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            trade_id_text = f" (ID: {trade_id})" if trade_id else ""
            
            message = f"""===========================================================

🎮 Mock Trading Executor — {pt_time} ({et_time})

📊 Symbol: {symbol}
🎯 Trade Status: ✅ Trade Executed{trade_id_text}
⏰ Execution Time: {pt_time} ({et_time})

✅ System Status: Mock trade execution complete
🔍 Next Step: Position monitoring"""
            
            success = await self._send_telegram_message(message, AlertLevel.INFO)
            
            if success:
                log.info(f"Mock executor alert sent for {symbol} - Trade Executed")
            
            return success
            
        except Exception as e:
            log.error(f"Error sending mock executor alert: {e}")
            return False
    
    async def send_trade_execution_alert(self, symbol: str, side: str, price: float, 
                                        quantity: int, trade_id: str, mode: str = "LIVE") -> bool:
        """Send trade execution alert for demo or live trading"""
        try:
            from zoneinfo import ZoneInfo
            
            # Determine mode emoji and text
            if mode == "DEMO_MODE":
                mode_emoji = "🎮"
                mode_text = "Demo Trade Executed"
                mode_title = "Demo Mode Trade Execution Alert"
            else:
                mode_emoji = "🎮"
                mode_text = "Live Trade Executed"
                mode_title = "Live Mode Trade Execution Alert"
            
            # Get current time in Pacific Time and Eastern Time
            pt_tz = ZoneInfo('America/Los_Angeles')
            et_tz = ZoneInfo('America/New_York')
            now_pt = datetime.now(pt_tz)
            now_et = datetime.now(et_tz)
            
            # Format times properly
            pt_time = now_pt.strftime('%I:%M %p PT')
            et_time = now_et.strftime('%I:%M %p ET')
            
            # Normalize side to consistent format
            normalized_side = side.upper()
            if normalized_side in ["LONG", "BUY"]:
                normalized_side = "BUY"
                side_emoji = "🟢"  # Green for BUY orders
            elif normalized_side in ["SHORT", "SELL"]:
                normalized_side = "SELL"
                side_emoji = "🔴"  # Red for SELL orders
            else:
                side_emoji = "⚪"  # Default for other actions
            
            # Format quantity for display (remove unnecessary decimal places)
            if isinstance(quantity, float) and quantity.is_integer():
                display_quantity = int(quantity)
            else:
                display_quantity = f"{quantity:.2f}".rstrip('0').rstrip('.')
            
            # Format the message
            message = f"""{mode_emoji} {mode_text}

{side_emoji} • {normalized_side} {display_quantity} {symbol} @ ${price:.2f} • ${price * quantity:.2f}

📊 Trade ID: {trade_id}
⏰ Execution Time: {pt_time} ({et_time})"""
            
            return await self._send_telegram_message(message, AlertLevel.SUCCESS)
            
        except Exception as e:
            log.error(f"Failed to send trade execution alert: {e}")
            return False

# Global instance
_prime_alert_manager = None

def get_prime_alert_manager() -> PrimeAlertManager:
    """Get the prime alert manager instance"""
    global _prime_alert_manager
    if _prime_alert_manager is None:
        _prime_alert_manager = PrimeAlertManager()
    return _prime_alert_manager

log.info("Prime Alert Manager loaded successfully")
