#!/usr/bin/env python3
"""
OAuth Keep-Alive System
=======================

Comprehensive E*TRADE OAuth token keep-alive system that maintains tokens active
throughout the trading day by making lightweight API calls every 1.5 hours.

Features:
- Automatic keep-alive calls every 1.5 hours (safety margin before 2-hour idle timeout)
- Support for both production and sandbox environments
- Background task management with graceful shutdown
- Integration with alert system for monitoring
- CLI interface for manual keep-alive calls
- Comprehensive error handling and recovery
- Real-time status monitoring

Usage:
    # CLI usage (manual keep-alive)
    python3 oauth_keepalive.py sandbox    # Keep sandbox tokens alive
    python3 oauth_keepalive.py prod       # Keep production tokens alive
    python3 oauth_keepalive.py both       # Keep both environments alive
    
    # Programmatic usage (automatic keep-alive)
    from oauth_keepalive import start_oauth_keepalive, stop_oauth_keepalive
    await start_oauth_keepalive()  # Start background keep-alive
    await stop_oauth_keepalive()   # Stop background keep-alive
"""

import os
import sys
import asyncio
import logging
import threading
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add ETradeOAuth to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
etrade_oauth_dir = os.path.dirname(current_dir)
sys.path.insert(0, etrade_oauth_dir)

# Import OAuth modules
try:
    from central_oauth_manager import CentralOAuthManager, Environment
    from simple_oauth_cli import load_tokens, load_config, make_oauth_request
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    logging.warning("OAuth modules not available")

# Import alert manager (if available)
try:
    # Add main project to path
    main_project_dir = os.path.dirname(os.path.dirname(etrade_oauth_dir))
    sys.path.insert(0, main_project_dir)
    from modules.prime_alert_manager import get_prime_alert_manager
    ALERT_MANAGER_AVAILABLE = True
except ImportError:
    ALERT_MANAGER_AVAILABLE = False
    logging.warning("Alert manager not available")

log = logging.getLogger(__name__)

@dataclass
class KeepAliveStatus:
    """Keep-alive status tracking"""
    environment: str
    last_call: Optional[datetime] = None
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    is_running: bool = False
    next_call: Optional[datetime] = None
    total_calls: int = 0
    successful_calls: int = 0

class OAuthKeepAlive:
    """
    OAuth Keep-Alive System
    
    Maintains E*TRADE OAuth tokens active by making lightweight API calls
    every 1.5 hours to prevent idle timeout (2 hours).
    """
    
    def __init__(self):
        self.keepalive_interval = 1.5 * 3600  # 1.5 hours in seconds
        self.environments = ['prod', 'sandbox']
        self.status: Dict[str, KeepAliveStatus] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.running = False
        
        # Initialize OAuth manager
        self.oauth_manager = None
        if OAUTH_AVAILABLE:
            try:
                self.oauth_manager = CentralOAuthManager()
                log.info("✅ OAuth manager initialized for keep-alive")
            except Exception as e:
                log.error(f"Failed to initialize OAuth manager: {e}")
        
        # Initialize alert manager
        self.alert_manager = None
        if ALERT_MANAGER_AVAILABLE:
            try:
                self.alert_manager = get_prime_alert_manager()
                log.info("✅ Alert manager initialized for keep-alive")
            except Exception as e:
                log.error(f"Failed to initialize alert manager: {e}")
        
        # Initialize status for each environment
        for env in self.environments:
            self.status[env] = KeepAliveStatus(environment=env)
    
    async def start_keepalive(self) -> bool:
        """
        Start keep-alive system for all environments
        
        Returns:
            True if started successfully
        """
        try:
            if not OAUTH_AVAILABLE:
                log.error("OAuth modules not available for keep-alive")
                return False
            
            self.running = True
            log.info("🔄 Starting OAuth keep-alive system...")
            
            # Start keep-alive tasks for each environment
            for env in self.environments:
                task = asyncio.create_task(self._keepalive_loop(env))
                self.tasks[env] = task
                self.status[env].is_running = True
                self.status[env].next_call = datetime.now(timezone.utc) + timedelta(seconds=self.keepalive_interval)
                
                log.info(f"✅ Keep-alive started for {env} environment")
            
            # Send startup alert
            if self.alert_manager:
                await self.alert_manager.send_oauth_warning(
                    "system", 
                    "OAuth keep-alive system started - tokens will be maintained active"
                )
            
            return True
            
        except Exception as e:
            log.error(f"Failed to start keep-alive system: {e}")
            return False
    
    async def stop_keepalive(self) -> bool:
        """
        Stop keep-alive system
        
        Returns:
            True if stopped successfully
        """
        try:
            self.running = False
            log.info("🛑 Stopping OAuth keep-alive system...")
            
            # Cancel all tasks
            for env, task in self.tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                self.status[env].is_running = False
                self.status[env].next_call = None
                
                log.info(f"✅ Keep-alive stopped for {env} environment")
            
            self.tasks.clear()
            
            # Send shutdown alert
            if self.alert_manager:
                await self.alert_manager.send_oauth_warning(
                    "system", 
                    "OAuth keep-alive system stopped"
                )
            
            return True
            
        except Exception as e:
            log.error(f"Failed to stop keep-alive system: {e}")
            return False
    
    async def _keepalive_loop(self, env: str):
        """Keep-alive loop for specific environment"""
        log.info(f"🔄 Starting keep-alive loop for {env}")
        
        while self.running:
            try:
                # Wait for keep-alive interval
                await asyncio.sleep(self.keepalive_interval)
                
                if not self.running:
                    break
                
                # Make keep-alive call
                await self._make_keepalive_call(env)
                
                # Update next call time
                self.status[env].next_call = datetime.now(timezone.utc) + timedelta(seconds=self.keepalive_interval)
                
            except asyncio.CancelledError:
                log.info(f"Keep-alive loop cancelled for {env}")
                break
            except Exception as e:
                log.error(f"Error in keep-alive loop for {env}: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _make_keepalive_call(self, env: str) -> bool:
        """
        Make lightweight API call to keep tokens alive
        
        Args:
            env: Environment ('prod' or 'sandbox')
            
        Returns:
            True if call successful
        """
        try:
            log.info(f"🔄 Making keep-alive call for {env}...")
            
            # Update call count
            self.status[env].total_calls += 1
            self.status[env].last_call = datetime.now(timezone.utc)
            
            # Use simple OAuth CLI approach for reliability
            success = await self._call_account_list_simple(env)
            
            if success:
                self.status[env].last_success = datetime.now(timezone.utc)
                self.status[env].consecutive_failures = 0
                self.status[env].successful_calls += 1
                
                log.info(f"✅ Keep-alive call successful for {env}")
                
                # Send success alert if this was a recovery
                if self.status[env].consecutive_failures > 0 and self.alert_manager:
                    await self.alert_manager.send_oauth_renewal_success(env)
                
                return True
            else:
                self.status[env].consecutive_failures += 1
                log.warning(f"⚠️ Keep-alive call failed for {env} (attempt {self.status[env].consecutive_failures})")
                
                # Send error alert if too many failures
                if self.status[env].consecutive_failures >= 3 and self.alert_manager:
                    await self.alert_manager.send_oauth_renewal_error(
                        env, 
                        f"Keep-alive failed {self.status[env].consecutive_failures} times"
                    )
                
                return False
                
        except Exception as e:
            log.error(f"Keep-alive call error for {env}: {e}")
            self.status[env].consecutive_failures += 1
            return False
    
    async def _call_account_list_simple(self, env: str) -> bool:
        """
        Make lightweight account list API call using simple OAuth CLI
        
        Args:
            env: Environment ('prod' or 'sandbox')
            
        Returns:
            True if call successful
        """
        try:
            # Load credentials and tokens
            config = load_config(env)
            tokens = load_tokens(env)
            
            if not tokens or not config.get('consumer_key'):
                log.error(f"No credentials or tokens found for {env}")
                return False
            
            # Make API call to keep tokens alive
            accounts_url = f"{config['base_url']}/v1/accounts/list"
            
            # Use simple OAuth request
            response = make_oauth_request(
                'GET', 
                accounts_url, 
                {}, 
                config['consumer_key'], 
                config['consumer_secret'],
                tokens['oauth_token'], 
                tokens['oauth_token_secret']
            )
            
            # Check if response indicates success
            if isinstance(response, dict) and 'AccountListResponse' in response:
                # Update last used timestamp
                tokens['last_used'] = datetime.now().isoformat()
                
                # Save updated tokens
                token_file = f'tokens_{env}.json'
                with open(token_file, 'w') as f:
                    json.dump(tokens, f, indent=2)
                
                log.info(f"✅ {env} tokens updated: {tokens['last_used']}")
                return True
            else:
                log.warning(f"Unexpected response for {env}: {response}")
                return False
                
        except Exception as e:
            log.error(f"Account list call error for {env}: {e}")
            return False
    
    def get_status(self, env: str) -> Dict[str, Any]:
        """
        Get keep-alive status for environment
        
        Args:
            env: Environment ('prod' or 'sandbox')
            
        Returns:
            Status dictionary
        """
        if env not in self.status:
            return {"error": "Environment not found"}
        
        status = self.status[env]
        now = datetime.now(timezone.utc)
        
        return {
            "environment": env,
            "is_running": status.is_running,
            "last_call": status.last_call.isoformat() if status.last_call else None,
            "last_success": status.last_success.isoformat() if status.last_success else None,
            "consecutive_failures": status.consecutive_failures,
            "next_call": status.next_call.isoformat() if status.next_call else None,
            "time_until_next": (status.next_call - now).total_seconds() if status.next_call else None,
            "total_calls": status.total_calls,
            "successful_calls": status.successful_calls,
            "success_rate": (status.successful_calls / status.total_calls * 100) if status.total_calls > 0 else 0,
            "status": "healthy" if status.consecutive_failures == 0 else "degraded" if status.consecutive_failures < 3 else "unhealthy"
        }
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get keep-alive status for all environments"""
        return {
            env: self.get_status(env) 
            for env in self.environments
        }
    
    async def force_keepalive_call(self, env: str) -> bool:
        """
        Force an immediate keep-alive call
        
        Args:
            env: Environment ('prod' or 'sandbox')
            
        Returns:
            True if call successful
        """
        log.info(f"🔄 Forcing keep-alive call for {env}...")
        return await self._make_keepalive_call(env)

# Global instance
_keepalive_instance: Optional[OAuthKeepAlive] = None

def get_oauth_keepalive() -> OAuthKeepAlive:
    """Get or create OAuth keep-alive instance"""
    global _keepalive_instance
    
    if _keepalive_instance is None:
        _keepalive_instance = OAuthKeepAlive()
    
    return _keepalive_instance

async def start_oauth_keepalive() -> bool:
    """Start OAuth keep-alive system"""
    keepalive = get_oauth_keepalive()
    return await keepalive.start_keepalive()

async def stop_oauth_keepalive() -> bool:
    """Stop OAuth keep-alive system"""
    keepalive = get_oauth_keepalive()
    return await keepalive.stop_keepalive()

def get_keepalive_status(env: str = None) -> Dict[str, Any]:
    """Get keep-alive status"""
    keepalive = get_oauth_keepalive()
    
    if env:
        return keepalive.get_status(env)
    else:
        return keepalive.get_all_status()

# --- CLI INTERFACE ---
async def keep_alive_environment(env: str) -> bool:
    """Keep tokens alive for a specific environment (CLI)"""
    print(f"🔐 Keeping {env.upper()} tokens alive...")
    print("=" * 40)
    
    if not OAUTH_AVAILABLE:
        print("❌ OAuth modules not available")
        return False
    
    # Load credentials and tokens
    config = load_config(env)
    tokens = load_tokens(env)
    
    if not tokens or not config.get('consumer_key'):
        print(f"❌ {env.upper()} not properly configured")
        return False
    
    print(f"Consumer Key: {config['consumer_key'][:8]}...")
    print(f"Token: {tokens['oauth_token'][:20]}...")
    print(f"Last Used: {tokens.get('last_used', 'Unknown')}")
    print()
    
    # Make API call to keep tokens alive
    accounts_url = f"{config['base_url']}/v1/accounts/list"
    
    try:
        print(f"📋 Making API call to keep {env} tokens alive...")
        accounts_response = make_oauth_request('GET', accounts_url, {}, 
                                            config['consumer_key'], config['consumer_secret'],
                                            tokens['oauth_token'], tokens['oauth_token_secret'])
        
        print(f"✅ {env.upper()} API call successful")
        
        # Update last used timestamp
        tokens['last_used'] = datetime.now().isoformat()
        
        # Save updated tokens
        token_file = f'tokens_{env}.json'
        with open(token_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print(f"✅ {env.upper()} tokens updated: {tokens['last_used']}")
        print(f"✅ {env.upper()} tokens will remain valid for 2+ hours")
        
        return True
        
    except Exception as e:
        print(f"❌ {env.upper()} API call failed: {e}")
        print(f"⚠️  {env.upper()} tokens may need renewal")
        return False

async def main():
    """Main CLI function"""
    if len(sys.argv) != 2:
        print("Usage: python3 oauth_keepalive.py {sandbox|prod|both}")
        sys.exit(1)
    
    env = sys.argv[1].lower()
    
    print("🔐 ETrade OAuth Keep-Alive System")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if env == 'sandbox':
        success = await keep_alive_environment('sandbox')
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    elif env == 'prod':
        success = await keep_alive_environment('prod')
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    elif env == 'both':
        print("🔄 Keeping both environments alive...")
        print()
        sandbox_ok = await keep_alive_environment('sandbox')
        print()
        prod_ok = await keep_alive_environment('prod')
        
        print()
        print("📊 SUMMARY:")
        print("=" * 20)
        print(f"Sandbox: {'✅ Active' if sandbox_ok else '❌ Failed'}")
        print(f"Production: {'✅ Active' if prod_ok else '❌ Failed'}")
    else:
        print("❌ Invalid environment. Use: sandbox, prod, or both")
        sys.exit(1)
    
    print()
    print("🎯 Keep-alive complete!")

async def test_keepalive():
    """Test keep-alive functionality"""
    print("🔄 Testing OAuth Keep-Alive System")
    print("-" * 40)
    
    keepalive = get_oauth_keepalive()
    
    # Test status
    status = keepalive.get_all_status()
    print(f"Status: {status}")
    
    # Test force call
    for env in ['prod', 'sandbox']:
        print(f"\nTesting {env} environment...")
        success = await keepalive.force_keepalive_call(env)
        print(f"Force call result: {success}")
    
    print("\n✅ Keep-alive test completed")

if __name__ == "__main__":
    asyncio.run(main())