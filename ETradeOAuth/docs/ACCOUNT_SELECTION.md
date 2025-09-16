# Account Selection Guide

## 🎯 Current Configuration

Your trading system is currently configured to trade on:

**✅ Steinwealth Account (775690861)**
- **Account ID**: 775690861
- **ID Key**: Hel9RqZ9D4gisYP9uzKt1A
- **Status**: ACTIVE
- **Type**: INDIVIDUAL, CASH

## 📊 Available Accounts

### Active Accounts (Available for Trading):

1. **Account 1: (No Name)**
   - **Account ID**: 215107721
   - **ID Key**: euyhpVVT8Z5f9k-tBDnzQg
   - **Status**: ACTIVE
   - **Type**: INDIVIDUAL, CASH

2. **Steinwealth (Current)**
   - **Account ID**: 775690861
   - **ID Key**: Hel9RqZ9D4gisYP9uzKt1A
   - **Status**: ACTIVE
   - **Type**: INDIVIDUAL, CASH

### Closed Accounts (Not Available):

3. **Account 2: (No Name)**
   - **Account ID**: 215530841
   - **Status**: CLOSED

4. **Account 3: (No Name)**
   - **Account ID**: 326580731
   - **Status**: CLOSED

## 🔧 How to Change Trading Account

To change which account the trading system uses, update these configuration files:

### 1. Update ETrade OAuth Configuration

**File**: `configs/etrade-oauth.env`

```bash
# Change this line:
ETRADE_LIVE_ACCOUNT_ID=775690861

# To your desired account ID:
ETRADE_LIVE_ACCOUNT_ID=215107721  # For Account 1
# OR
ETRADE_LIVE_ACCOUNT_ID=775690861  # For Steinwealth (current)
```

### 2. Update Deployment Configuration

**File**: `configs/deployment.env`

```bash
# Change this line:
LIVE_ACCOUNT_ID=775690861

# To your desired account ID:
LIVE_ACCOUNT_ID=215107721  # For Account 1
# OR
LIVE_ACCOUNT_ID=775690861  # For Steinwealth (current)
```

### 3. Update Trading System Configuration

**File**: `modules/etrade_oauth_integration.py`

The trading system will automatically use the account ID specified in the configuration files.

## 🚀 Quick Account Switch Commands

### Switch to Account 1 (215107721):

```bash
# Update configuration files
cd configs
sed -i '' 's/ETRADE_LIVE_ACCOUNT_ID=775690861/ETRADE_LIVE_ACCOUNT_ID=215107721/' etrade-oauth.env
sed -i '' 's/LIVE_ACCOUNT_ID=775690861/LIVE_ACCOUNT_ID=215107721/' deployment.env

# Test the new configuration
cd ../ETradeOAuth
python3 simple_oauth_cli.py test prod
```

### Switch back to Steinwealth (775690861):

```bash
# Update configuration files
cd configs
sed -i '' 's/ETRADE_LIVE_ACCOUNT_ID=215107721/ETRADE_LIVE_ACCOUNT_ID=775690861/' etrade-oauth.env
sed -i '' 's/LIVE_ACCOUNT_ID=215107721/LIVE_ACCOUNT_ID=775690861/' deployment.env

# Test the configuration
cd ../ETradeOAuth
python3 simple_oauth_cli.py test prod
```

## ✅ Verification

After changing the account, verify the configuration:

```bash
cd ETradeOAuth
python3 -c "
import sys
sys.path.insert(0, '..')
from modules.config_loader import get_config_value

print('Current Trading Account Configuration:')
print(f'Live Account ID: {get_config_value(\"ETRADE_LIVE_ACCOUNT_ID\", \"Not set\")}')
print(f'Deployment Account ID: {get_config_value(\"LIVE_ACCOUNT_ID\", \"Not set\")}')
"
```

## 🎯 Recommendation

**Steinwealth (775690861)** appears to be your main trading account and is currently configured. This is likely the best choice for trading unless you have a specific reason to use Account 1 (215107721).

## 🔒 Security Note

Always verify you're trading on the correct account before placing any live orders. The account ID is critical for ensuring trades are placed in the intended account.
