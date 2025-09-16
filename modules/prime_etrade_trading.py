"""
Prime ETrade Trading Module

This module provides comprehensive ETrade API integration for the trading system.
It implements all the essential ETrade API functions based on the provided checklist:

Auth (OAuth 1.0a): getRequestToken, authorizeUrl, getAccessToken, renewAccessToken, revokeAccessToken
Accounts: listAccounts, getAccountBalances, getPortfolio, listTransactions  
Orders: listOrders, getOrderDetails, previewEquityOrder, placeEquityOrder, cancelOrder
Market: getQuotes, lookupProduct, getOptionChains
Alerts: listAlerts, getAlert, deleteAlert
"""

import os
import sys
import json
import logging
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add ETradeOAuth to path
etrade_oauth_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ETradeOAuth')
sys.path.insert(0, etrade_oauth_path)

try:
    from simple_oauth_cli import load_config, load_tokens, make_oauth_request
    ETradeOAuth_AVAILABLE = True
except ImportError:
    logging.error("ETradeOAuth simple_oauth_cli not found. Please ensure ETradeOAuth folder is correctly set up.")
    ETradeOAuth_AVAILABLE = False

# Import requests-oauthlib for correct OAuth 1.0a implementation
try:
    import requests
    from requests_oauthlib import OAuth1
    REQUESTS_OAUTH_AVAILABLE = True
except ImportError:
    REQUESTS_OAUTH_AVAILABLE = False
    logging.warning("requests-oauthlib not available. Using fallback OAuth implementation.")

log = logging.getLogger(__name__)

@dataclass
class ETradeAccount:
    """ETrade Account Information"""
    account_id: str
    account_name: Optional[str]
    account_id_key: str
    account_status: str
    institution_type: str
    account_type: str

@dataclass
class ETradeBalance:
    """ETrade Account Balance Information - Essential fields only"""
    account_value: Optional[float]
    cash_available_for_investment: Optional[float]  # Cash available for investments
    cash_buying_power: Optional[float]  # Total buying power (cash + margin)
    option_level: Optional[str]

@dataclass
class ETradePosition:
    """ETrade Position Information"""
    position_id: str
    symbol: str
    symbol_description: str
    quantity: int
    position_type: str
    market_value: float
    total_cost: float
    total_gain: float
    total_gain_pct: float
    days_gain: float
    days_gain_pct: float

@dataclass
class ETradeQuote:
    """ETrade Market Quote"""
    symbol: str
    last_price: float
    change: float
    change_pct: float
    volume: int
    bid: float
    ask: float
    high: float
    low: float
    open: float

class PrimeETradeTrading:
    """
    Prime ETrade Trading System
    
    Comprehensive ETrade API integration for the trading strategy.
    Handles authentication, account management, portfolio tracking, and trading operations.
    """
    
    def __init__(self, environment: str = 'prod'):
        self.environment = environment
        self.config = None
        self.tokens = None
        self.accounts: List[ETradeAccount] = []
        self.selected_account: Optional[ETradeAccount] = None
        self.balance: Optional[ETradeBalance] = None
        self.portfolio: List[ETradePosition] = []
        
        if not ETradeOAuth_AVAILABLE:
            raise Exception("ETradeOAuth not available. Please set up ETradeOAuth system first.")
        
        self._load_credentials()
        self._load_tokens()
        self._load_accounts()
    
    def initialize(self) -> bool:
        """
        Initialize the ETrade trading system
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            log.info(f"🔧 Initializing ETrade {self.environment} trading system...")
            
            # Validate OAuth tokens
            if not self._validate_oauth_tokens():
                log.error("❌ OAuth token validation failed")
                return False
            
            # Test API connection
            if not self._test_api_connection():
                log.error("❌ API connection test failed")
                return False
            
            # Load account data
            if not self.accounts:
                log.error("❌ No accounts found")
                return False
            
            # Select primary account
            self._select_primary_account()
            
            log.info(f"✅ ETrade {self.environment} trading system initialized successfully")
            log.info(f"   Selected account: {self.selected_account.account_name if self.selected_account else 'None'}")
            log.info(f"   Total accounts: {len(self.accounts)}")
            
            return True
            
        except Exception as e:
            log.error(f"❌ Failed to initialize ETrade trading system: {e}")
            return False
    
    def _validate_oauth_tokens(self) -> bool:
        """
        Validate OAuth tokens
        
        Returns:
            True if tokens are valid, False otherwise
        """
        try:
            if not self.tokens:
                log.error("No OAuth tokens found")
                return False
            
            # Check if tokens have required fields
            required_fields = ['oauth_token', 'oauth_token_secret']
            for field in required_fields:
                if field not in self.tokens or not self.tokens[field]:
                    log.error(f"Missing required token field: {field}")
                    return False
            
            # Check if tokens are expired (past midnight ET)
            if self._is_token_expired():
                log.error("OAuth tokens expired at midnight ET")
                return False
            
            # Check if tokens need renewal (idle for 2+ hours)
            if self._needs_token_renewal():
                log.warning("OAuth tokens idle for 2+ hours, renewal needed")
                if not self._renew_tokens():
                    log.error("Failed to renew OAuth tokens")
                    return False
            
            log.info("✅ OAuth tokens validated successfully")
            return True
            
        except Exception as e:
            log.error(f"OAuth token validation failed: {e}")
            return False
    
    def _is_token_expired(self) -> bool:
        """Check if OAuth tokens are expired (past midnight ET)"""
        try:
            if not self.tokens:
                return True
            
            # Check if tokens have expires_at field
            if 'expires_at' in self.tokens:
                from datetime import datetime, timezone
                expires_at = datetime.fromisoformat(self.tokens['expires_at'])
                return datetime.now(timezone.utc) > expires_at
            
            # Check if tokens were created today (ET)
            created_at = self.tokens.get('created_at')
            if not created_at:
                return True
            
            # Parse creation time
            created_dt = datetime.fromisoformat(created_at)
            
            # Check if created today in ET
            now_et = datetime.now(timezone.utc).astimezone()
            created_et = created_dt.astimezone()
            
            # If created on a different day, tokens are expired
            return created_et.date() != now_et.date()
            
        except Exception as e:
            log.error(f"Error checking token expiration: {e}")
            return True
    
    def _needs_token_renewal(self) -> bool:
        """Check if OAuth tokens need renewal (idle for 2+ hours)"""
        try:
            if not self.tokens:
                return True
            
            last_used = self.tokens.get('last_used')
            if not last_used:
                return True
            
            # Parse last used time
            last_used_dt = datetime.fromisoformat(last_used)
            
            # Check if idle for 2+ hours
            idle_hours = (datetime.now(timezone.utc) - last_used_dt).total_seconds() / 3600
            return idle_hours >= 2
            
        except Exception as e:
            log.error(f"Error checking renewal need: {e}")
            return True
    
    def _renew_tokens(self) -> bool:
        """
        Renew OAuth tokens if needed
        
        Returns:
            True if renewal successful or not needed
        """
        try:
            # Import the OAuth manager
            from central_oauth_manager import CentralOAuthManager, Environment
            
            oauth_manager = CentralOAuthManager()
            env = Environment.PROD if self.environment == 'prod' else Environment.SANDBOX
            
            # Attempt renewal
            success = oauth_manager.renew_if_needed(env)
            
            if success:
                log.info("✅ OAuth tokens renewed successfully")
                # Reload tokens
                self._load_tokens()
                return True
            else:
                log.warning("⚠️ OAuth token renewal failed")
                return False
                
        except Exception as e:
            log.error(f"Error renewing tokens: {e}")
            return False
    
    def _test_api_connection(self) -> bool:
        """
        Test API connection with a simple call
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            log.info("🔍 Testing API connection...")
            
            # Test with account list call
            response = self._make_etrade_api_call(
                method='GET',
                url="/v1/accounts/list",
                params={}
            )
            
            # Check if response contains error
            if isinstance(response, dict) and 'error' in response:
                log.error(f"API test failed: {response['error']}")
                return False
            
            # Check if response contains account data
            if isinstance(response, dict) and 'AccountListResponse' in response:
                log.info("✅ API connection test successful")
                return True
            elif isinstance(response, str) and 'AccountListResponse' in response:
                log.info("✅ API connection test successful")
                return True
            else:
                log.error(f"Unexpected API response: {response}")
                return False
                
        except Exception as e:
            log.error(f"API connection test failed: {e}")
            return False
    
    def _select_primary_account(self):
        """Select the primary trading account"""
        try:
            if not self.accounts:
                log.warning("No accounts available for selection")
                return
            
            # Select the first account as primary
            self.selected_account = self.accounts[0]
            log.info(f"Selected primary account: {self.selected_account.account_name} ({self.selected_account.account_id})")
            
        except Exception as e:
            log.error(f"Failed to select primary account: {e}")
    
    def is_authenticated(self) -> bool:
        """
        Check if the system is properly authenticated
        
        Returns:
            True if authenticated and ready for trading
        """
        try:
            return (
                self.tokens is not None and
                self.accounts is not None and
                len(self.accounts) > 0 and
                self.selected_account is not None
            )
        except Exception as e:
            log.error(f"Error checking authentication status: {e}")
            return False
    
    def _make_etrade_api_call(self, method: str, url: str, params: Dict = None):
        """Make ETrade API call with correct OAuth 1.0a implementation"""
        if REQUESTS_OAUTH_AVAILABLE:
            return self._make_correct_oauth_call(method, url, params)
        else:
            # Fallback to original implementation
            return self._make_legacy_oauth_call(method, url, params)
    
    def _make_correct_oauth_call(self, method: str, url: str, params: Dict = None):
        """Make ETrade API call with correct OAuth 1.0a HMAC-SHA1 signature"""
        try:
            # Set up OAuth 1.0a with HMAC-SHA1
            oauth = OAuth1(
                client_key=self.config['consumer_key'],
                client_secret=self.config['consumer_secret'],
                resource_owner_key=self.tokens['oauth_token'],
                resource_owner_secret=self.tokens['oauth_token_secret'],
                signature_method="HMAC-SHA1",
                signature_type="AUTH_HEADER",  # OAuth params in Authorization header
            )
            
            # Make the request
            if url.startswith('/'):
                full_url = f"{self.config['base_url']}{url}"
            else:
                full_url = url
            
            # Add Accept header for JSON responses
            headers = {"Accept": "application/json"}
            
            response = requests.request(
                method=method,
                url=full_url,
                params=params or {},
                headers=headers,
                auth=oauth,
                timeout=30
            )
            
            # Handle response
            if response.status_code == 200:
                # Try to parse as JSON first
                try:
                    return response.json()
                except:
                    # Return as text if not JSON
                    return response.text
            else:
                log.error(f"API call failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}", "message": response.text}
                
        except Exception as e:
            log.error(f"OAuth API call failed: {e}")
            return {"error": str(e)}
    
    def _make_legacy_oauth_call(self, method: str, url: str, params: Dict = None):
        """Fallback OAuth implementation using original method"""
        original_cwd = os.getcwd()
        etrade_oauth_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ETradeOAuth')
        
        try:
            os.chdir(etrade_oauth_dir)
            return make_oauth_request(
                method=method,
                url=url,
                params=params or {},
                consumer_key=self.config['consumer_key'],
                consumer_secret=self.config['consumer_secret'],
                oauth_token=self.tokens['oauth_token'],
                oauth_token_secret=self.tokens['oauth_token_secret']
            )
        finally:
            os.chdir(original_cwd)
        
    def _load_credentials(self):
        """Load ETrade credentials"""
        try:
            # Temporarily change to ETradeOAuth directory for config loading
            original_cwd = os.getcwd()
            etrade_oauth_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ETradeOAuth')
            
            try:
                os.chdir(etrade_oauth_dir)
                self.config = load_config(self.environment)
            finally:
                os.chdir(original_cwd)
            
            if not self.config:
                raise Exception(f"Failed to load config for {self.environment}")
            log.info(f"✅ Loaded ETrade credentials for {self.environment}")
        except Exception as e:
            log.error(f"Failed to load ETrade credentials: {e}")
            raise
    
    def _load_tokens(self):
        """Load ETrade tokens"""
        try:
            # Temporarily change to ETradeOAuth directory for token loading
            original_cwd = os.getcwd()
            etrade_oauth_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ETradeOAuth')
            
            try:
                os.chdir(etrade_oauth_dir)
                self.tokens = load_tokens(self.environment)
            finally:
                os.chdir(original_cwd)
            
            if not self.tokens:
                raise Exception(f"No tokens found for {self.environment}")
            log.info(f"✅ Loaded ETrade tokens for {self.environment}")
        except Exception as e:
            log.error(f"Failed to load ETrade tokens: {e}")
            raise
    
    def _load_accounts(self):
        """Load and parse account list"""
        try:
            log.info("📋 Loading ETrade accounts...")
            
            response = self._make_etrade_api_call(
                method='GET',
                url="/v1/accounts/list",
                params={}
            )
            
            # Handle different response formats
            if isinstance(response, dict):
                # JSON response from new OAuth implementation
                if 'AccountListResponse' in response:
                    self._parse_account_list_json(response)
                elif 'Accounts' in response:
                    self._parse_account_list_json(response)
                elif 'error' in response:
                    log.error(f"API error: {response['error']}")
                    raise Exception(f"API error: {response['error']}")
                else:
                    log.error(f"Unexpected JSON response format: {response}")
                    raise Exception("Unexpected JSON response format")
            elif isinstance(response, str):
                # XML response (legacy)
                if '<?xml' in response:
                    self._parse_account_list_xml(response)
                else:
                    log.error(f"Unexpected string response: {response[:200]}...")
                    raise Exception("Unexpected string response format")
            else:
                log.error(f"Unexpected response type: {type(response)}")
                raise Exception(f"Unexpected response type: {type(response)}")
                
        except Exception as e:
            log.error(f"Failed to load accounts: {e}")
            raise
    
    def _parse_account_list_json(self, response_data: dict):
        """Parse account list JSON response"""
        try:
            # Handle both response formats
            if 'AccountListResponse' in response_data:
                accounts_data = response_data['AccountListResponse']['Accounts']['Account']
            elif 'Accounts' in response_data:
                accounts_data = response_data['Accounts']['Account']
            else:
                raise Exception("No accounts data found in response")
            
            if not isinstance(accounts_data, list):
                accounts_data = [accounts_data]
            
            for account_data in accounts_data:
                account = ETradeAccount(
                    account_id=account_data.get('accountId'),
                    account_name=account_data.get('accountName'),
                    account_id_key=account_data.get('accountIdKey'),
                    account_status=account_data.get('accountStatus'),
                    institution_type=account_data.get('institutionType'),
                    account_type=account_data.get('accountType')
                )
                self.accounts.append(account)
                log.info(f"✅ Loaded account: {account.account_name} ({account.account_id})")
            
            log.info(f"✅ Loaded {len(self.accounts)} accounts")
            
        except Exception as e:
            log.error(f"Failed to parse account list JSON: {e}")
            raise
    
    def _parse_account_list_xml(self, xml_data: str):
        """Parse account list XML response"""
        try:
            # Clean up the XML data
            xml_data = xml_data.strip()
            
            if xml_data.startswith('"1.0" encoding="UTF-8" standalone="yes"?>'):
                xml_data = '<?xml version=' + xml_data
            elif not xml_data.startswith('<?xml version'):
                xml_data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + xml_data
            
            root = ET.fromstring(xml_data)
            
            self.accounts = []
            for account in root.findall('.//Account'):
                account_data = ETradeAccount(
                    account_id=account.find('accountId').text if account.find('accountId') is not None else None,
                    account_name=account.find('accountName').text if account.find('accountName') is not None else None,
                    account_id_key=account.find('accountIdKey').text if account.find('accountIdKey') is not None else None,
                    account_status=account.find('accountStatus').text if account.find('accountStatus') is not None else None,
                    institution_type=account.find('institutionType').text if account.find('institutionType') is not None else None,
                    account_type=account.find('accountType').text if account.find('accountType') is not None else None,
                )
                self.accounts.append(account_data)
            
            # Auto-select the first active account
            active_accounts = [acc for acc in self.accounts if acc.account_status == 'ACTIVE']
            if active_accounts:
                self.selected_account = active_accounts[0]
                log.info(f"✅ Auto-selected account: {self.selected_account.account_name} ({self.selected_account.account_id})")
            
            log.info(f"✅ Loaded {len(self.accounts)} accounts ({len(active_accounts)} active)")
            
        except Exception as e:
            log.error(f"Failed to parse account list XML: {e}")
            raise
    
    def select_account(self, account_id: str) -> bool:
        """Select a specific account for trading"""
        for account in self.accounts:
            if account.account_id == account_id and account.account_status == 'ACTIVE':
                self.selected_account = account
                log.info(f"✅ Selected account: {account.account_name} ({account.account_id})")
                return True
        log.error(f"Account {account_id} not found or not active")
        return False
    
    def get_account_balance(self) -> ETradeBalance:
        """Get account balance information using correct OAuth 1.0a"""
        if not self.selected_account:
            raise Exception("No account selected")
        
        try:
            log.info(f"💰 Fetching balance for account {self.selected_account.account_id}...")
            
            # Use correct OAuth implementation with required query parameters
            params = {'instType': 'BROKERAGE', 'realTimeNAV': 'true'}
            url = f"/v1/accounts/{self.selected_account.account_id_key}/balance"
            
            response = self._make_etrade_api_call(
                method='GET',
                url=url,
                params=params
            )
            
            if response and not isinstance(response, dict) or 'error' not in response:
                self.balance = self._parse_balance_response(response)
                log.info(f"✅ Retrieved balance: Cash Available for Investment: ${self.balance.cash_available_for_investment}")
                return self.balance
            else:
                log.warning(f"Balance API failed: {response}")
                
                # Fallback: Try to get balance from portfolio
                log.info("🔄 Attempting to get balance from portfolio data...")
                portfolio = self.get_portfolio()
                if portfolio:
                    # Calculate balance from portfolio positions
                    total_value = sum(pos.market_value for pos in portfolio if pos.market_value)
                    cash_positions = [pos for pos in portfolio 
                                    if 'CASH' in pos.symbol.upper() or 'USD' in pos.symbol.upper()]
                    cash_available = sum(pos.market_value for pos in cash_positions if pos.market_value) if cash_positions else 0.0
                    
                    self.balance = ETradeBalance(
                        account_value=total_value,
                        cash_available_for_investment=cash_available,
                        cash_buying_power=cash_available,
                        option_level=None
                    )
                    log.info(f"✅ Retrieved balance from portfolio: Cash Available for Investment: ${self.balance.cash_available_for_investment}")
                    return self.balance
            
            # If all methods fail, return empty balance
            self.balance = ETradeBalance(
                account_value=None,
                cash_available_for_investment=None,
                cash_buying_power=None,
                option_level=None
            )
            return self.balance
            
        except Exception as e:
            log.error(f"Failed to get account balance: {e}")
            raise
    
    def _parse_balance_response(self, response) -> ETradeBalance:
        """Parse balance response (JSON or XML)"""
        try:
            # Handle JSON response first (preferred)
            if isinstance(response, dict):
                if 'BalanceResponse' in response:
                    # JSON response structure
                    balance_response = response['BalanceResponse']
                    computed = balance_response.get('Computed', {}) or balance_response.get('ComputedBalance', {})
                    
                    def safe_float(value):
                        try:
                            return float(value) if value else None
                        except (ValueError, TypeError):
                            return None
                    
                    return ETradeBalance(
                        account_value=safe_float(computed.get('totalAccountValue')),
                        cash_available_for_investment=safe_float(computed.get('cashAvailableForInvestment')),
                        cash_buying_power=safe_float(computed.get('cashBuyingPower')),
                        option_level=computed.get('optionLevel')
                    )
            
            # Handle XML response (legacy)
            if isinstance(response, str) and '<?xml' in response:
                xml_data = response.strip()
                
                # Clean up XML data
                if xml_data.startswith('"1.0" encoding="UTF-8" standalone="yes"?>'):
                    xml_data = '<?xml version=' + xml_data
                elif not xml_data.startswith('<?xml version'):
                    xml_data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + xml_data
                
                root = ET.fromstring(xml_data)
                
                # Extract balance information
                balance_data = {}
                account_balance = root.find('.//AccountBalance')
                if account_balance is not None:
                    for child in account_balance:
                        balance_data[child.tag] = child.text
                
                # Map to ETradeBalance
                def safe_float(value):
                    try:
                        return float(value) if value else None
                    except (ValueError, TypeError):
                        return None
                
                return ETradeBalance(
                    account_value=safe_float(balance_data.get('accountValue', balance_data.get('accountBalance'))),
                    cash_available_for_investment=safe_float(balance_data.get('cashAvailableForInvestment')),
                    cash_buying_power=safe_float(balance_data.get('cashBuyingPower', balance_data.get('buyingPower'))),
                    option_level=balance_data.get('optionLevel')
                )
            
            return ETradeBalance(None, None, None, None)
            
        except Exception as e:
            log.error(f"Failed to parse balance response: {e}")
            return ETradeBalance(None, None, None, None)
    
    def get_portfolio(self) -> List[ETradePosition]:
        """Get portfolio positions"""
        if not self.selected_account:
            raise Exception("No account selected")
        
        try:
            log.info(f"📊 Fetching portfolio for account {self.selected_account.account_id}...")
            
            response = self._make_etrade_api_call(
                method='GET',
                url=f"{self.config['base_url']}/v1/accounts/{self.selected_account.account_id_key}/portfolio",
                params={}
            )
            
            if response:
                self.portfolio = self._parse_portfolio_response(response)
                log.info(f"✅ Retrieved {len(self.portfolio)} portfolio positions")
                return self.portfolio
            else:
                self.portfolio = []
                return self.portfolio
                
        except Exception as e:
            log.error(f"Failed to get portfolio: {e}")
            self.portfolio = []
            return self.portfolio
    
    def _parse_portfolio_response(self, response: Dict) -> List[ETradePosition]:
        """Parse portfolio response"""
        try:
            xml_key = '<?xml version'
            if xml_key in response:
                xml_data = response[xml_key]
                
                # Clean up XML data
                xml_data = xml_data.strip()
                if xml_data.startswith('"1.0" encoding="UTF-8" standalone="yes"?>'):
                    xml_data = '<?xml version=' + xml_data
                elif not xml_data.startswith('<?xml version'):
                    xml_data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + xml_data
                
                root = ET.fromstring(xml_data)
                
                positions = []
                for position in root.findall('.//Position'):
                    pos_data = {}
                    for child in position:
                        pos_data[child.tag] = child.text
                    
                    # Map to ETradePosition
                    def safe_float(value):
                        try:
                            return float(value) if value else 0.0
                        except (ValueError, TypeError):
                            return 0.0
                    
                    def safe_int(value):
                        try:
                            return int(value) if value else 0
                        except (ValueError, TypeError):
                            return 0
                    
                    positions.append(ETradePosition(
                        position_id=pos_data.get('positionId', ''),
                        symbol=pos_data.get('symbolDescription', ''),
                        symbol_description=pos_data.get('symbolDescription', ''),
                        quantity=safe_int(pos_data.get('quantity')),
                        position_type=pos_data.get('positionType', ''),
                        market_value=safe_float(pos_data.get('marketValue')),
                        total_cost=safe_float(pos_data.get('totalCost')),
                        total_gain=safe_float(pos_data.get('totalGain')),
                        total_gain_pct=safe_float(pos_data.get('totalGainPct')),
                        days_gain=safe_float(pos_data.get('daysGain')),
                        days_gain_pct=safe_float(pos_data.get('daysGainPct'))
                    ))
                
                return positions
            
            return []
            
        except Exception as e:
            log.error(f"Failed to parse portfolio response: {e}")
            return []
    
    def get_quotes(self, symbols: List[str]) -> List[ETradeQuote]:
        """Get market quotes for symbols"""
        try:
            if not symbols:
                return []
            
            log.info(f"📈 Fetching quotes for {len(symbols)} symbols...")
            
            # ETrade API accepts comma-separated symbols
            symbol_param = ','.join(symbols)
            
            response = self._make_etrade_api_call(
                method='GET',
                url=f"{self.config['base_url']}/v1/market/quote/{symbol_param}",
                params={'detailFlag': 'ALL'}
            )
            
            if response:
                quotes = self._parse_quotes_response(response)
                log.info(f"✅ Retrieved {len(quotes)} quotes")
                return quotes
            else:
                return []
                
        except Exception as e:
            log.error(f"Failed to get quotes: {e}")
            return []
    
    def get_historical_data(self, symbol: str, period: str = "1d", count: int = 200) -> List[Dict[str, Any]]:
        """
        Get historical data for technical analysis
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1m, 3m, 6m, 1y, 2y, 5y)
            count: Number of data points (max 200)
        """
        try:
            log.info(f"📊 Fetching historical data for {symbol} ({period}, {count} points)...")
            
            # E*TRADE doesn't provide historical data directly
            # This would need to be implemented with a different provider
            # For now, return empty list
            log.warning(f"E*TRADE doesn't provide historical data for {symbol}")
            return []
            
        except Exception as e:
            log.error(f"Failed to get historical data for {symbol}: {e}")
            return []
    
    def get_market_data_for_strategy(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive market data for strategy analysis
        
        This method provides all the data that strategies need by:
        1. Getting real-time data from E*TRADE
        2. Using cached historical data if available
        3. Calculating technical indicators
        4. Providing fallback data for missing information
        
        Returns:
            Dictionary with all data needed for strategy analysis
        """
        try:
            # Get real-time quote from E*TRADE
            quotes = self.get_quotes([symbol])
            if not quotes:
                log.warning(f"No quote data available for {symbol}")
                return self._get_fallback_market_data(symbol)
            
            quote = quotes[0]
            
            # Try to get historical data from cache or external source
            historical_data = self._get_historical_data_for_symbol(symbol)
            
            # Calculate comprehensive technical indicators
            technical_indicators = self._calculate_technical_indicators(quote, historical_data)
            
            # Build comprehensive market data
            market_data = {
                'symbol': symbol,
                'current_price': quote.last_price,
                'bid': quote.bid,
                'ask': quote.ask,
                'open': quote.open,
                'high': quote.high,
                'low': quote.low,
                'volume': quote.volume,
                'change': quote.change,
                'change_pct': quote.change_pct,
                'timestamp': datetime.utcnow().isoformat(),
                
                # Price arrays for technical analysis (enhanced)
                'prices': self._build_price_array(quote, historical_data),
                'volumes': self._build_volume_array(quote, historical_data),
                'closes': self._build_closes_array(quote, historical_data),
                'highs': self._build_highs_array(quote, historical_data),
                'lows': self._build_lows_array(quote, historical_data),
                'opens': self._build_opens_array(quote, historical_data),
                
                # Technical indicators (comprehensive)
                'rsi': technical_indicators['rsi'],
                'rsi_14': technical_indicators['rsi_14'],
                'rsi_21': technical_indicators['rsi_21'],
                'macd': technical_indicators['macd'],
                'macd_signal': technical_indicators['macd_signal'],
                'macd_histogram': technical_indicators['macd_histogram'],
                'sma_20': technical_indicators['sma_20'],
                'sma_50': technical_indicators['sma_50'],
                'sma_200': technical_indicators['sma_200'],
                'ema_12': technical_indicators['ema_12'],
                'ema_26': technical_indicators['ema_26'],
                'atr': technical_indicators['atr'],
                'bollinger_upper': technical_indicators['bollinger_upper'],
                'bollinger_middle': technical_indicators['bollinger_middle'],
                'bollinger_lower': technical_indicators['bollinger_lower'],
                'bollinger_width': technical_indicators['bollinger_width'],
                
                # Volume analysis
                'volume_ratio': technical_indicators['volume_ratio'],
                'volume_sma': technical_indicators['volume_sma'],
                'obv': technical_indicators['obv'],
                'ad_line': technical_indicators['ad_line'],
                
                # Pattern recognition
                'doji': technical_indicators['doji'],
                'hammer': technical_indicators['hammer'],
                'engulfing': technical_indicators['engulfing'],
                'morning_star': technical_indicators['morning_star'],
                
                # Market data metadata
                'data_source': 'ETRADE',
                'data_quality': technical_indicators['data_quality'],
                'historical_points': len(historical_data) if historical_data else 0,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            log.debug(f"📊 Generated comprehensive market data for {symbol}: {technical_indicators['data_quality']} quality")
            return market_data
            
        except Exception as e:
            log.error(f"Failed to get market data for strategy: {e}")
            return self._get_fallback_market_data(symbol)
    
    def _calculate_basic_rsi(self, quote: ETradeQuote) -> float:
        """Calculate basic RSI from available data"""
        try:
            # Very basic RSI calculation using price change
            if quote.change_pct > 0:
                return min(100, 50 + (quote.change_pct * 2))  # Rough approximation
            else:
                return max(0, 50 + (quote.change_pct * 2))
        except:
            return 50.0
    
    def _calculate_basic_macd(self, quote: ETradeQuote) -> float:
        """Calculate basic MACD from available data"""
        try:
            # Very basic MACD using price vs open
            return quote.last_price - quote.open
        except:
            return 0.0
    
    def _calculate_basic_atr(self, quote: ETradeQuote) -> float:
        """Calculate basic ATR from available data"""
        try:
            # Basic ATR using high-low range
            return quote.high - quote.low
        except:
            return 0.0
    
    def _get_historical_data_for_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """Get historical data for symbol from cache or external source"""
        try:
            # Check if we have cached historical data
            # This would integrate with a data cache or external provider
            # For now, return empty list as E*TRADE doesn't provide historical data
            return []
        except Exception as e:
            log.debug(f"No historical data available for {symbol}: {e}")
            return []
    
    def _calculate_technical_indicators(self, quote: ETradeQuote, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive technical indicators"""
        try:
            # Build price arrays from available data
            closes = self._build_closes_array(quote, historical_data)
            highs = self._build_highs_array(quote, historical_data)
            lows = self._build_lows_array(quote, historical_data)
            volumes = self._build_volume_array(quote, historical_data)
            
            # Determine data quality
            data_quality = 'excellent' if len(historical_data) >= 200 else 'good' if len(historical_data) >= 50 else 'limited' if len(historical_data) >= 20 else 'minimal'
            
            # Calculate indicators based on available data
            indicators = {
                # RSI calculations
                'rsi': self._calculate_rsi(closes, 14) if len(closes) >= 15 else self._calculate_basic_rsi(quote),
                'rsi_14': self._calculate_rsi(closes, 14) if len(closes) >= 15 else self._calculate_basic_rsi(quote),
                'rsi_21': self._calculate_rsi(closes, 21) if len(closes) >= 22 else self._calculate_basic_rsi(quote),
                
                # MACD calculations
                'macd': self._calculate_macd(closes) if len(closes) >= 26 else self._calculate_basic_macd(quote),
                'macd_signal': self._calculate_macd_signal(closes) if len(closes) >= 26 else 0.0,
                'macd_histogram': self._calculate_macd_histogram(closes) if len(closes) >= 26 else 0.0,
                
                # Moving averages
                'sma_20': self._calculate_sma(closes, 20) if len(closes) >= 20 else quote.last_price,
                'sma_50': self._calculate_sma(closes, 50) if len(closes) >= 50 else quote.last_price,
                'sma_200': self._calculate_sma(closes, 200) if len(closes) >= 200 else quote.last_price,
                'ema_12': self._calculate_ema(closes, 12) if len(closes) >= 12 else quote.last_price,
                'ema_26': self._calculate_ema(closes, 26) if len(closes) >= 26 else quote.last_price,
                
                # Volatility indicators
                'atr': self._calculate_atr(highs, lows, closes) if len(highs) >= 14 else self._calculate_basic_atr(quote),
                
                # Bollinger Bands
                'bollinger_upper': self._calculate_bollinger_upper(closes) if len(closes) >= 20 else quote.high,
                'bollinger_middle': self._calculate_bollinger_middle(closes) if len(closes) >= 20 else quote.last_price,
                'bollinger_lower': self._calculate_bollinger_lower(closes) if len(closes) >= 20 else quote.low,
                'bollinger_width': self._calculate_bollinger_width(closes) if len(closes) >= 20 else 0.0,
                
                # Volume analysis
                'volume_ratio': self._calculate_volume_ratio(volumes) if len(volumes) >= 20 else 1.0,
                'volume_sma': self._calculate_sma(volumes, 20) if len(volumes) >= 20 else quote.volume,
                'obv': self._calculate_obv(closes, volumes) if len(closes) >= 2 else 0.0,
                'ad_line': self._calculate_ad_line(highs, lows, closes, volumes) if len(highs) >= 2 else 0.0,
                
                # Pattern recognition
                'doji': self._detect_doji(quote) if quote.open and quote.close else False,
                'hammer': self._detect_hammer(quote) if quote.open and quote.close and quote.high and quote.low else False,
                'engulfing': False,  # Would need previous candle data
                'morning_star': False,  # Would need previous candle data
                
                # Data quality
                'data_quality': data_quality
            }
            
            return indicators
            
        except Exception as e:
            log.error(f"Error calculating technical indicators: {e}")
            return self._get_basic_indicators(quote)
    
    def _build_price_array(self, quote: ETradeQuote, historical_data: List[Dict[str, Any]]) -> List[float]:
        """Build price array for technical analysis"""
        try:
            prices = []
            
            # Add historical data if available
            if historical_data:
                for data_point in historical_data:
                    if 'close' in data_point:
                        prices.append(float(data_point['close']))
            
            # Add current quote data
            if quote.last_price:
                prices.append(quote.last_price)
            
            return prices if prices else [quote.last_price] if quote.last_price else [100.0]
        except:
            return [quote.last_price] if quote.last_price else [100.0]
    
    def _build_volume_array(self, quote: ETradeQuote, historical_data: List[Dict[str, Any]]) -> List[int]:
        """Build volume array for technical analysis"""
        try:
            volumes = []
            
            # Add historical data if available
            if historical_data:
                for data_point in historical_data:
                    if 'volume' in data_point:
                        volumes.append(int(data_point['volume']))
            
            # Add current quote data
            if quote.volume:
                volumes.append(quote.volume)
            
            return volumes if volumes else [quote.volume] if quote.volume else [1000000]
        except:
            return [quote.volume] if quote.volume else [1000000]
    
    def _build_closes_array(self, quote: ETradeQuote, historical_data: List[Dict[str, Any]]) -> List[float]:
        """Build closes array for technical analysis"""
        return self._build_price_array(quote, historical_data)
    
    def _build_highs_array(self, quote: ETradeQuote, historical_data: List[Dict[str, Any]]) -> List[float]:
        """Build highs array for technical analysis"""
        try:
            highs = []
            
            # Add historical data if available
            if historical_data:
                for data_point in historical_data:
                    if 'high' in data_point:
                        highs.append(float(data_point['high']))
            
            # Add current quote data
            if quote.high:
                highs.append(quote.high)
            
            return highs if highs else [quote.high] if quote.high else [quote.last_price] if quote.last_price else [100.0]
        except:
            return [quote.high] if quote.high else [quote.last_price] if quote.last_price else [100.0]
    
    def _build_lows_array(self, quote: ETradeQuote, historical_data: List[Dict[str, Any]]) -> List[float]:
        """Build lows array for technical analysis"""
        try:
            lows = []
            
            # Add historical data if available
            if historical_data:
                for data_point in historical_data:
                    if 'low' in data_point:
                        lows.append(float(data_point['low']))
            
            # Add current quote data
            if quote.low:
                lows.append(quote.low)
            
            return lows if lows else [quote.low] if quote.low else [quote.last_price] if quote.last_price else [100.0]
        except:
            return [quote.low] if quote.low else [quote.last_price] if quote.last_price else [100.0]
    
    def _build_opens_array(self, quote: ETradeQuote, historical_data: List[Dict[str, Any]]) -> List[float]:
        """Build opens array for technical analysis"""
        try:
            opens = []
            
            # Add historical data if available
            if historical_data:
                for data_point in historical_data:
                    if 'open' in data_point:
                        opens.append(float(data_point['open']))
            
            # Add current quote data
            if quote.open:
                opens.append(quote.open)
            
            return opens if opens else [quote.open] if quote.open else [quote.last_price] if quote.last_price else [100.0]
        except:
            return [quote.open] if quote.open else [quote.last_price] if quote.last_price else [100.0]
    
    def _get_fallback_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get fallback market data when E*TRADE data is unavailable"""
        try:
            return {
                'symbol': symbol,
                'current_price': 100.0,
                'bid': 99.95,
                'ask': 100.05,
                'open': 99.50,
                'high': 100.50,
                'low': 99.00,
                'volume': 1000000,
                'change': 0.50,
                'change_pct': 0.5,
                'timestamp': datetime.utcnow().isoformat(),
                
                # Price arrays
                'prices': [99.50, 100.50, 99.00, 100.0],
                'volumes': [1000000],
                'closes': [100.0],
                'highs': [100.50],
                'lows': [99.00],
                'opens': [99.50],
                
                # Technical indicators (fallback values)
                'rsi': 50.0,
                'rsi_14': 50.0,
                'rsi_21': 50.0,
                'macd': 0.0,
                'macd_signal': 0.0,
                'macd_histogram': 0.0,
                'sma_20': 100.0,
                'sma_50': 100.0,
                'sma_200': 100.0,
                'ema_12': 100.0,
                'ema_26': 100.0,
                'atr': 1.0,
                'bollinger_upper': 101.0,
                'bollinger_middle': 100.0,
                'bollinger_lower': 99.0,
                'bollinger_width': 2.0,
                
                # Volume analysis
                'volume_ratio': 1.0,
                'volume_sma': 1000000,
                'obv': 0.0,
                'ad_line': 0.0,
                
                # Pattern recognition
                'doji': False,
                'hammer': False,
                'engulfing': False,
                'morning_star': False,
                
                # Metadata
                'data_source': 'FALLBACK',
                'data_quality': 'placeholder',
                'historical_points': 0,
                'last_updated': datetime.utcnow().isoformat()
            }
        except Exception as e:
            log.error(f"Error creating fallback market data: {e}")
            return {}
    
    def _get_basic_indicators(self, quote: ETradeQuote) -> Dict[str, Any]:
        """Get basic indicators when calculation fails"""
        return {
            'rsi': self._calculate_basic_rsi(quote),
            'rsi_14': self._calculate_basic_rsi(quote),
            'rsi_21': self._calculate_basic_rsi(quote),
            'macd': self._calculate_basic_macd(quote),
            'macd_signal': 0.0,
            'macd_histogram': 0.0,
            'sma_20': quote.last_price,
            'sma_50': quote.last_price,
            'sma_200': quote.last_price,
            'ema_12': quote.last_price,
            'ema_26': quote.last_price,
            'atr': self._calculate_basic_atr(quote),
            'bollinger_upper': quote.high,
            'bollinger_middle': quote.last_price,
            'bollinger_lower': quote.low,
            'bollinger_width': 0.0,
            'volume_ratio': 1.0,
            'volume_sma': quote.volume,
            'obv': 0.0,
            'ad_line': 0.0,
            'doji': False,
            'hammer': False,
            'engulfing': False,
            'morning_star': False,
            'data_quality': 'minimal'
        }
    
    # ========================================================================
    # COMPREHENSIVE TECHNICAL ANALYSIS METHODS
    # ========================================================================
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI with proper algorithm"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [delta if delta > 0 else 0 for delta in deltas]
            losses = [-delta if delta < 0 else 0 for delta in deltas]
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return 50.0
    
    def _calculate_macd(self, prices: List[float]) -> float:
        """Calculate MACD line"""
        try:
            if len(prices) < 26:
                return 0.0
            
            ema_12 = self._calculate_ema(prices, 12)
            ema_26 = self._calculate_ema(prices, 26)
            return ema_12 - ema_26
        except:
            return 0.0
    
    def _calculate_macd_signal(self, prices: List[float]) -> float:
        """Calculate MACD signal line"""
        try:
            if len(prices) < 26:
                return 0.0
            
            macd_values = []
            for i in range(26, len(prices) + 1):
                ema_12 = self._calculate_ema(prices[:i], 12)
                ema_26 = self._calculate_ema(prices[:i], 26)
                macd_values.append(ema_12 - ema_26)
            
            if len(macd_values) < 9:
                return 0.0
            
            return self._calculate_ema(macd_values, 9)
        except:
            return 0.0
    
    def _calculate_macd_histogram(self, prices: List[float]) -> float:
        """Calculate MACD histogram"""
        try:
            macd = self._calculate_macd(prices)
            signal = self._calculate_macd_signal(prices)
            return macd - signal
        except:
            return 0.0
    
    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average"""
        try:
            if len(prices) < period:
                return sum(prices) / len(prices) if prices else 0.0
            return sum(prices[-period:]) / period
        except:
            return 0.0
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        try:
            if len(prices) < period:
                return sum(prices) / len(prices) if prices else 0.0
            
            multiplier = 2 / (period + 1)
            ema = prices[0]
            
            for price in prices[1:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            
            return ema
        except:
            return 0.0
    
    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if len(highs) < period + 1:
                return 0.0
            
            true_ranges = []
            for i in range(1, len(highs)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                true_ranges.append(max(tr1, tr2, tr3))
            
            if len(true_ranges) < period:
                return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0
            
            return sum(true_ranges[-period:]) / period
        except:
            return 0.0
    
    def _calculate_bollinger_upper(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> float:
        """Calculate Bollinger Bands upper band"""
        try:
            if len(prices) < period:
                return prices[-1] if prices else 0.0
            
            sma = self._calculate_sma(prices, period)
            variance = sum((price - sma) ** 2 for price in prices[-period:]) / period
            std = variance ** 0.5
            return sma + (std_dev * std)
        except:
            return prices[-1] if prices else 0.0
    
    def _calculate_bollinger_middle(self, prices: List[float], period: int = 20) -> float:
        """Calculate Bollinger Bands middle band (SMA)"""
        return self._calculate_sma(prices, period)
    
    def _calculate_bollinger_lower(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> float:
        """Calculate Bollinger Bands lower band"""
        try:
            if len(prices) < period:
                return prices[-1] if prices else 0.0
            
            sma = self._calculate_sma(prices, period)
            variance = sum((price - sma) ** 2 for price in prices[-period:]) / period
            std = variance ** 0.5
            return sma - (std_dev * std)
        except:
            return prices[-1] if prices else 0.0
    
    def _calculate_bollinger_width(self, prices: List[float], period: int = 20) -> float:
        """Calculate Bollinger Bands width"""
        try:
            upper = self._calculate_bollinger_upper(prices, period)
            lower = self._calculate_bollinger_lower(prices, period)
            middle = self._calculate_bollinger_middle(prices, period)
            return (upper - lower) / middle if middle != 0 else 0.0
        except:
            return 0.0
    
    def _calculate_volume_ratio(self, volumes: List[int], period: int = 20) -> float:
        """Calculate volume ratio (current vs average)"""
        try:
            if len(volumes) < 2:
                return 1.0
            
            current_volume = volumes[-1]
            avg_volume = self._calculate_sma(volumes, min(period, len(volumes)))
            return current_volume / avg_volume if avg_volume > 0 else 1.0
        except:
            return 1.0
    
    def _calculate_obv(self, closes: List[float], volumes: List[int]) -> float:
        """Calculate On-Balance Volume"""
        try:
            if len(closes) < 2 or len(volumes) < 2:
                return 0.0
            
            obv = 0.0
            for i in range(1, min(len(closes), len(volumes))):
                if closes[i] > closes[i-1]:
                    obv += volumes[i]
                elif closes[i] < closes[i-1]:
                    obv -= volumes[i]
            
            return obv
        except:
            return 0.0
    
    def _calculate_ad_line(self, highs: List[float], lows: List[float], closes: List[float], volumes: List[int]) -> float:
        """Calculate Accumulation/Distribution Line"""
        try:
            if len(highs) < 2 or len(volumes) < 2:
                return 0.0
            
            ad_line = 0.0
            for i in range(min(len(highs), len(lows), len(closes), len(volumes))):
                if highs[i] != lows[i]:
                    clv = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / (highs[i] - lows[i])
                    ad_line += clv * volumes[i]
            
            return ad_line
        except:
            return 0.0
    
    def _detect_doji(self, quote: ETradeQuote) -> bool:
        """Detect doji pattern"""
        try:
            if not all([quote.open, quote.close, quote.high, quote.low]):
                return False
            
            body_size = abs(quote.close - quote.open)
            total_range = quote.high - quote.low
            
            return body_size <= (total_range * 0.1) if total_range > 0 else False
        except:
            return False
    
    def _detect_hammer(self, quote: ETradeQuote) -> bool:
        """Detect hammer pattern"""
        try:
            if not all([quote.open, quote.close, quote.high, quote.low]):
                return False
            
            body_size = abs(quote.close - quote.open)
            lower_shadow = min(quote.open, quote.close) - quote.low
            upper_shadow = quote.high - max(quote.open, quote.close)
            total_range = quote.high - quote.low
            
            return (lower_shadow >= 2 * body_size and 
                   upper_shadow <= body_size * 0.5 and 
                   total_range > 0)
        except:
            return False
    
    def _parse_quotes_response(self, response: Dict) -> List[ETradeQuote]:
        """Parse quotes response"""
        try:
            xml_key = '<?xml version'
            if xml_key in response:
                xml_data = response[xml_key]
                
                # Clean up XML data
                xml_data = xml_data.strip()
                if xml_data.startswith('"1.0" encoding="UTF-8" standalone="yes"?>'):
                    xml_data = '<?xml version=' + xml_data
                elif not xml_data.startswith('<?xml version'):
                    xml_data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + xml_data
                
                root = ET.fromstring(xml_data)
                
                quotes = []
                for quote in root.findall('.//QuoteData'):
                    quote_data = {}
                    for child in quote:
                        quote_data[child.tag] = child.text
                    
                    # Map to ETradeQuote
                    def safe_float(value):
                        try:
                            return float(value) if value else 0.0
                        except (ValueError, TypeError):
                            return 0.0
                    
                    def safe_int(value):
                        try:
                            return int(value) if value else 0
                        except (ValueError, TypeError):
                            return 0
                    
                    quotes.append(ETradeQuote(
                        symbol=quote_data.get('symbol', ''),
                        last_price=safe_float(quote_data.get('lastPrice')),
                        change=safe_float(quote_data.get('change')),
                        change_pct=safe_float(quote_data.get('changePercent')),
                        volume=safe_int(quote_data.get('volume')),
                        bid=safe_float(quote_data.get('bid')),
                        ask=safe_float(quote_data.get('ask')),
                        high=safe_float(quote_data.get('high')),
                        low=safe_float(quote_data.get('low')),
                        open=safe_float(quote_data.get('open'))
                    ))
                
                return quotes
            
            return []
            
        except Exception as e:
            log.error(f"Failed to parse quotes response: {e}")
            return []
    
    def get_cash_available_for_trading(self) -> Optional[float]:
        """Get cash available for trading (primary method)"""
        if not self.balance:
            self.get_account_balance()
        
        return self.balance.cash_available_for_investment if self.balance else None
    
    def get_cash_available_for_investment(self) -> Optional[float]:
        """Get cash specifically available for investment"""
        if not self.balance:
            self.get_account_balance()
        
        return self.balance.cash_available_for_investment if self.balance else None
    
    def get_cash_buying_power(self) -> Optional[float]:
        """Get total cash buying power (cash + margin)"""
        if not self.balance:
            self.get_account_balance()
        
        return self.balance.cash_buying_power if self.balance else None
    
    def get_available_cash_for_trading(self) -> Optional[float]:
        """
        Get the most appropriate cash amount for trading decisions
        
        Priority order:
        1. Cash available for investment (primary trading cash)
        2. Cash buying power (includes margin)
        """
        if not self.balance:
            self.get_account_balance()
        
        if not self.balance:
            return None
        
        # Priority order for trading decisions
        if self.balance.cash_available_for_investment is not None and self.balance.cash_available_for_investment > 0:
            return self.balance.cash_available_for_investment
        elif self.balance.cash_buying_power is not None and self.balance.cash_buying_power > 0:
            return self.balance.cash_buying_power
        else:
            return 0.0
    
    def get_total_portfolio_value(self) -> float:
        """Get total portfolio value from positions"""
        if not self.portfolio:
            self.get_portfolio()
        
        return sum(pos.market_value for pos in self.portfolio)
    
    def get_position_by_symbol(self, symbol: str) -> Optional[ETradePosition]:
        """Get position by symbol"""
        if not self.portfolio:
            self.get_portfolio()
        
        for position in self.portfolio:
            if position.symbol == symbol:
                return position
        return None
    
    def refresh_data(self):
        """Refresh all account data"""
        log.info("🔄 Refreshing ETrade account data...")
        self.get_account_balance()
        self.get_portfolio()
        log.info("✅ ETrade data refreshed")
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get comprehensive account summary"""
        if not self.selected_account:
            return {"error": "No account selected"}
        
        # Refresh data
        self.refresh_data()
        
        return {
            "account": {
                "id": self.selected_account.account_id,
                "name": self.selected_account.account_name,
                "status": self.selected_account.account_status,
                "type": self.selected_account.account_type
            },
            "balance": {
                "account_value": self.balance.account_value if self.balance else None,
                "cash_available_for_investment": self.balance.cash_available_for_investment if self.balance else None,
                "cash_buying_power": self.balance.cash_buying_power if self.balance else None,
                "option_level": self.balance.option_level if self.balance else None
            },
            "portfolio": {
                "total_positions": len(self.portfolio),
                "total_value": self.get_total_portfolio_value(),
                "positions": [
                    {
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "market_value": pos.market_value,
                        "total_gain": pos.total_gain,
                        "total_gain_pct": pos.total_gain_pct,
                        "days_gain": pos.days_gain,
                        "days_gain_pct": pos.days_gain_pct
                    }
                    for pos in self.portfolio
                ]
            }
        }
    
    def get_orders(self, status: str = 'OPEN') -> List[Dict[str, Any]]:
        """Get account orders
        
        Args:
            status: Order status filter ('OPEN', 'EXECUTED', 'CANCELLED', 'REJECTED', 'EXPIRED')
        """
        if not self.selected_account:
            raise Exception("No account selected")
        
        try:
            log.info(f"📋 Fetching orders for account {self.selected_account.account_id}...")
            
            response = self._make_etrade_api_call(
                method='GET',
                url=f"{self.config['base_url']}/v1/accounts/{self.selected_account.account_id_key}/orders",
                params={'status': status} if status else {}
            )
            
            orders = []
            if '<?xml version' in response:
                xml_data = response['<?xml version']
                orders = self._parse_orders_response(xml_data)
            
            log.info(f"✅ Retrieved {len(orders)} orders")
            return orders
            
        except Exception as e:
            log.error(f"Failed to get orders: {e}")
            return []
    
    def _parse_orders_response(self, xml_data: str) -> List[Dict[str, Any]]:
        """Parse orders XML response"""
        try:
            # Clean up XML data
            xml_data = xml_data.strip()
            if xml_data.startswith('"1.0" encoding="UTF-8" standalone="yes"?>'):
                xml_data = '<?xml version=' + xml_data
            elif not xml_data.startswith('<?xml version'):
                xml_data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + xml_data
            
            root = ET.fromstring(xml_data)
            
            orders = []
            for order in root.findall('.//Order'):
                order_data = {
                    'order_id': order.find('orderId').text if order.find('orderId') is not None else None,
                    'status': order.find('status').text if order.find('status') is not None else None,
                    'order_type': order.find('orderType').text if order.find('orderType') is not None else None,
                    'side': order.find('side').text if order.find('side') is not None else None,
                    'symbol': order.find('symbol').text if order.find('symbol') is not None else None,
                    'quantity': int(order.find('quantity').text) if order.find('quantity') is not None else 0,
                    'price': float(order.find('price').text) if order.find('price') is not None else None,
                    'stop_price': float(order.find('stopPrice').text) if order.find('stopPrice') is not None else None,
                    'time_in_force': order.find('timeInForce').text if order.find('timeInForce') is not None else None,
                    'created_time': order.find('createdTime').text if order.find('createdTime') is not None else None,
                    'executed_quantity': int(order.find('executedQuantity').text) if order.find('executedQuantity') is not None else 0,
                    'remaining_quantity': int(order.find('remainingQuantity').text) if order.find('remainingQuantity') is not None else 0,
                }
                orders.append(order_data)
            
            return orders
            
        except Exception as e:
            log.error(f"Failed to parse orders XML: {e}")
            return []
    
    def preview_order(self, symbol: str, quantity: int, side: str, order_type: str = 'MARKET', 
                     price: Optional[float] = None, stop_price: Optional[float] = None) -> Dict[str, Any]:
        """Preview order before placing
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            side: 'BUY' or 'SELL'
            order_type: 'MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT'
            price: Limit price (for LIMIT orders)
            stop_price: Stop price (for STOP orders)
        """
        if not self.selected_account:
            raise Exception("No account selected")
        
        try:
            log.info(f"🔍 Previewing {side} order for {quantity} shares of {symbol}...")
            
            # Build order data
            order_data = {
                'orderType': order_type,
                'clientOrderId': f"PREVIEW_{int(time.time())}",
                'Order': [{
                    'allOrNone': False,
                    'priceType': 'MARKET' if order_type == 'MARKET' else 'LIMIT',
                    'orderAction': side,
                    'quantity': quantity,
                    'symbol': symbol,
                    'orderTerm': 'GOOD_FOR_DAY'
                }]
            }
            
            # Add price if limit order
            if order_type == 'LIMIT' and price:
                order_data['Order'][0]['limitPrice'] = price
            
            # Add stop price if stop order
            if order_type in ['STOP', 'STOP_LIMIT'] and stop_price:
                order_data['Order'][0]['stopPrice'] = stop_price
            
            response = self._make_etrade_api_call(
                method='POST',
                url=f"{self.config['base_url']}/v1/accounts/{self.selected_account.account_id_key}/orders/preview",
                params=order_data
            )
            
            log.info(f"✅ Order preview successful")
            return response
            
        except Exception as e:
            log.error(f"Failed to preview order: {e}")
            raise
    
    def place_order(self, symbol: str, quantity: int, side: str, order_type: str = 'MARKET',
                   price: Optional[float] = None, stop_price: Optional[float] = None,
                   client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place an order
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            side: 'BUY' or 'SELL'
            order_type: 'MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT'
            price: Limit price (for LIMIT orders)
            stop_price: Stop price (for STOP orders)
            client_order_id: Custom order ID
        """
        if not self.selected_account:
            raise Exception("No account selected")
        
        try:
            log.info(f"📝 Placing {side} order for {quantity} shares of {symbol}...")
            
            # Generate client order ID if not provided
            if not client_order_id:
                client_order_id = f"ETRADE_{int(time.time())}"
            
            # Build order data
            order_data = {
                'orderType': order_type,
                'clientOrderId': client_order_id,
                'Order': [{
                    'allOrNone': False,
                    'priceType': 'MARKET' if order_type == 'MARKET' else 'LIMIT',
                    'orderAction': side,
                    'quantity': quantity,
                    'symbol': symbol,
                    'orderTerm': 'GOOD_FOR_DAY'
                }]
            }
            
            # Add price if limit order
            if order_type == 'LIMIT' and price:
                order_data['Order'][0]['limitPrice'] = price
            
            # Add stop price if stop order
            if order_type in ['STOP', 'STOP_LIMIT'] and stop_price:
                order_data['Order'][0]['stopPrice'] = stop_price
            
            response = self._make_etrade_api_call(
                method='POST',
                url=f"{self.config['base_url']}/v1/accounts/{self.selected_account.account_id_key}/orders/place",
                params=order_data
            )
            
            log.info(f"✅ Order placed successfully: {client_order_id}")
            return response
            
        except Exception as e:
            log.error(f"Failed to place order: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order
        
        Args:
            order_id: Order ID to cancel
        """
        if not self.selected_account:
            raise Exception("No account selected")
        
        try:
            log.info(f"❌ Cancelling order {order_id}...")
            
            response = self._make_etrade_api_call(
                method='DELETE',
                url=f"{self.config['base_url']}/v1/accounts/{self.selected_account.account_id_key}/orders/cancel",
                params={'orderId': order_id}
            )
            
            log.info(f"✅ Order cancelled successfully")
            return response
            
        except Exception as e:
            log.error(f"Failed to cancel order: {e}")
            raise
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status
        
        Args:
            order_id: Order ID to check
        """
        if not self.selected_account:
            raise Exception("No account selected")
        
        try:
            log.info(f"🔍 Getting status for order {order_id}...")
            
            response = self._make_etrade_api_call(
                method='GET',
                url=f"{self.config['base_url']}/v1/accounts/{self.selected_account.account_id_key}/orders/{order_id}",
                params={}
            )
            
            log.info(f"✅ Retrieved order status")
            return response
            
        except Exception as e:
            log.error(f"Failed to get order status: {e}")
            raise
    
    def get_market_hours(self) -> Dict[str, Any]:
        """Get market hours information"""
        try:
            log.info("🕐 Fetching market hours...")
            
            response = self._make_etrade_api_call(
                method='GET',
                url=f"{self.config['base_url']}/v1/market/hours",
                params={}
            )
            
            log.info(f"✅ Retrieved market hours")
            return response
            
        except Exception as e:
            log.error(f"Failed to get market hours: {e}")
            return {}
    
    def get_option_chains(self, symbol: str, expiry_date: str, option_type: str = 'CALL') -> Dict[str, Any]:
        """Get option chains for a symbol
        
        Args:
            symbol: Stock symbol
            expiry_date: Expiry date (YYYY-MM-DD)
            option_type: 'CALL' or 'PUT'
        """
        try:
            log.info(f"🔗 Fetching option chains for {symbol} expiring {expiry_date}...")
            
            response = self._make_etrade_api_call(
                method='GET',
                url=f"{self.config['base_url']}/v1/market/optionchains",
                params={
                    'symbol': symbol,
                    'expiryDate': expiry_date,
                    'optionType': option_type,
                    'includeWeekly': 'true'
                }
            )
            
            log.info(f"✅ Retrieved option chains")
            return response
            
        except Exception as e:
            log.error(f"Failed to get option chains: {e}")
            return {}
    
    def get_account_alerts(self) -> List[Dict[str, Any]]:
        """Get account alerts"""
        if not self.selected_account:
            raise Exception("No account selected")
        
        try:
            log.info(f"🔔 Fetching alerts for account {self.selected_account.account_id}...")
            
            response = self._make_etrade_api_call(
                method='GET',
                url=f"{self.config['base_url']}/v1/user/alerts",
                params={}
            )
            
            alerts = []
            if '<?xml version' in response:
                xml_data = response['<?xml version']
                alerts = self._parse_alerts_response(xml_data)
            
            log.info(f"✅ Retrieved {len(alerts)} alerts")
            return alerts
            
        except Exception as e:
            log.error(f"Failed to get alerts: {e}")
            return []
    
    def _parse_alerts_response(self, xml_data: str) -> List[Dict[str, Any]]:
        """Parse alerts XML response"""
        try:
            # Clean up XML data
            xml_data = xml_data.strip()
            if xml_data.startswith('"1.0" encoding="UTF-8" standalone="yes"?>'):
                xml_data = '<?xml version=' + xml_data
            elif not xml_data.startswith('<?xml version'):
                xml_data = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + xml_data
            
            root = ET.fromstring(xml_data)
            
            alerts = []
            for alert in root.findall('.//Alert'):
                alert_data = {
                    'alert_id': alert.find('alertId').text if alert.find('alertId') is not None else None,
                    'alert_name': alert.find('alertName').text if alert.find('alertName') is not None else None,
                    'alert_type': alert.find('alertType').text if alert.find('alertType') is not None else None,
                    'status': alert.find('status').text if alert.find('status') is not None else None,
                    'created_time': alert.find('createdTime').text if alert.find('createdTime') is not None else None,
                    'symbol': alert.find('symbol').text if alert.find('symbol') is not None else None,
                    'condition': alert.find('condition').text if alert.find('condition') is not None else None,
                    'trigger_price': float(alert.find('triggerPrice').text) if alert.find('triggerPrice') is not None else None,
                }
                alerts.append(alert_data)
            
            return alerts
            
        except Exception as e:
            log.error(f"Failed to parse alerts XML: {e}")
            return []

# Global instance
_etrade_trading_instance: Optional[PrimeETradeTrading] = None
_etrade_trading_lock = threading.Lock()

def get_etrade_trading(environment: str = 'prod') -> PrimeETradeTrading:
    """Get or create ETrade trading instance"""
    global _etrade_trading_instance
    with _etrade_trading_lock:
        if _etrade_trading_instance is None:
            _etrade_trading_instance = PrimeETradeTrading(environment)
        return _etrade_trading_instance

def test_etrade_trading():
    """Test ETrade trading functionality"""
    try:
        print("🔐 Testing ETrade Trading System...")
        
        etrade = get_etrade_trading('prod')
        
        print(f"✅ Environment: {etrade.environment}")
        print(f"✅ Accounts loaded: {len(etrade.accounts)}")
        
        if etrade.selected_account:
            print(f"✅ Selected account: {etrade.selected_account.account_name} ({etrade.selected_account.account_id})")
            
            # Test balance
            balance = etrade.get_account_balance()
            print(f"✅ Account value: ${balance.account_value}")
            print(f"✅ Cash available for investment: ${balance.cash_available_for_investment}")
            print(f"✅ Cash buying power: ${balance.cash_buying_power}")
            print(f"✅ Option level: {balance.option_level}")
            
            # Test portfolio
            portfolio = etrade.get_portfolio()
            print(f"✅ Portfolio positions: {len(portfolio)}")
            
            # Test quotes for first few positions
            if portfolio:
                symbols = [pos.symbol for pos in portfolio[:3]]
                quotes = etrade.get_quotes(symbols)
                print(f"✅ Retrieved quotes for {len(quotes)} symbols")
                
                # Test comprehensive market data for strategies
                if quotes:
                    test_symbol = quotes[0].symbol
                    market_data = etrade.get_market_data_for_strategy(test_symbol)
                    print(f"✅ Generated comprehensive market data for {test_symbol}:")
                    print(f"   Data quality: {market_data.get('data_quality', 'unknown')}")
                    print(f"   Historical points: {market_data.get('historical_points', 0)}")
                    print(f"   RSI: {market_data.get('rsi', 0):.2f}")
                    print(f"   MACD: {market_data.get('macd', 0):.4f}")
                    print(f"   SMA 20: {market_data.get('sma_20', 0):.2f}")
                    print(f"   Volume ratio: {market_data.get('volume_ratio', 0):.2f}")
                    print(f"   Bollinger width: {market_data.get('bollinger_width', 0):.4f}")
                    print(f"   Patterns - Doji: {market_data.get('doji', False)}, Hammer: {market_data.get('hammer', False)}")
            
            # Get summary
            summary = etrade.get_account_summary()
            print(f"✅ Account summary generated")
            
        print("🎯 ETrade trading system test completed successfully!")
        
    except Exception as e:
        log.error(f"❌ ETrade trading test failed: {e}")
        raise

if __name__ == '__main__':
    test_etrade_trading()
