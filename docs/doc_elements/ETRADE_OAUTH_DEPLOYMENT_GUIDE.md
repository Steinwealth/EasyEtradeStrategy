# ETrade OAuth Deployment Guide

## Overview
This guide provides step-by-step instructions for setting up ETrade OAuth integration for both Demo Sandbox and Live trading in the V2 Easy ETrade Strategy.

## Prerequisites

### 1. ETrade Developer Account
- Visit [ETrade Developer Portal](https://developer.etrade.com)
- Create a developer account
- Complete identity verification

### 2. ETrade Trading Account
- **Demo Sandbox**: Free testing account (no real money)
- **Live Account**: Real trading account with funds

### 3. Required Credentials
- Consumer Key
- Consumer Secret
- Account ID
- Trading permissions enabled

## Setup Process

### Step 1: Get ETrade Credentials

#### For Demo Sandbox:
1. Log into [ETrade Developer Portal](https://developer.etrade.com)
2. Navigate to "My Apps"
3. Click "Create New App"
4. Select "Sandbox" environment
5. Fill in application details:
   - App Name: "V2 Easy ETrade Strategy"
   - Description: "Automated trading system"
   - Callback URL: `oob` (out-of-band)
6. Submit application
7. Copy the Consumer Key and Consumer Secret
8. Note your Account ID from the sandbox account

#### For Live Trading:
1. Log into [ETrade Developer Portal](https://developer.etrade.com)
2. Navigate to "My Apps"
3. Click "Create New App"
4. Select "Production" environment
5. Fill in application details:
   - App Name: "V2 Easy ETrade Strategy Live"
   - Description: "Live automated trading system"
   - Callback URL: `oob` (out-of-band)
6. Submit application for review
7. Wait for approval (can take 1-3 business days)
8. Copy the Consumer Key and Consumer Secret
9. Note your Account ID from your live account

### Step 2: Configure OAuth Credentials

#### Option A: Interactive Setup
```bash
python3 scripts/setup_etrade_oauth.py
```

This will prompt you to enter:
- Demo Consumer Key
- Demo Consumer Secret
- Demo Account ID
- Live Consumer Key
- Live Consumer Secret
- Live Account ID

#### Option B: Manual Configuration
Edit `configs/etrade-oauth.env`:

```env
# Demo Sandbox Credentials
ETRADE_DEMO_CONSUMER_KEY=your_demo_consumer_key_here
ETRADE_DEMO_CONSUMER_SECRET=your_demo_consumer_secret_here
ETRADE_DEMO_ACCOUNT_ID=your_demo_account_id_here

# Live Account Credentials
ETRADE_LIVE_CONSUMER_KEY=your_live_consumer_key_here
ETRADE_LIVE_CONSUMER_SECRET=your_live_consumer_secret_here
ETRADE_LIVE_ACCOUNT_ID=your_live_account_id_here
```

### Step 3: Test OAuth Integration

```bash
python3 scripts/test_etrade_integration.py
```

This will test:
- Credential loading
- Demo Sandbox authentication
- Live account authentication
- Trading permissions validation
- Portfolio access
- Market data retrieval

### Step 4: Initialize Trading System

#### Demo Mode (Recommended First):
```bash
python3 improved_main.py --etrade-mode demo --system-mode full_trading
```

#### Live Mode (After Demo Testing):
```bash
python3 improved_main.py --etrade-mode live --system-mode full_trading
```

## Security Considerations

### 1. Credential Protection
- Never commit `configs/etrade-oauth.env` to version control
- Use environment variables in production
- Rotate credentials regularly
- Use secure storage for production

### 2. Access Control
- Limit API access to necessary IP addresses
- Use read-only permissions when possible
- Monitor API usage
- Set up alerts for unusual activity

### 3. Risk Management
- Start with Demo Sandbox
- Test thoroughly before Live trading
- Set position size limits
- Use stop-loss orders
- Monitor account balance

## Google Cloud Deployment

### 1. Environment Variables
Set these in Google Cloud Secret Manager:

```bash
ETRADE_DEMO_CONSUMER_KEY=your_demo_key
ETRADE_DEMO_CONSUMER_SECRET=your_demo_secret
ETRADE_DEMO_ACCOUNT_ID=your_demo_account
ETRADE_LIVE_CONSUMER_KEY=your_live_key
ETRADE_LIVE_CONSUMER_SECRET=your_live_secret
ETRADE_LIVE_ACCOUNT_ID=your_live_account
ETRADE_MODE=demo  # or 'live' for production
```

### 2. Deployment Script
```bash
python3 scripts/deploy_to_google_cloud.py --etrade-mode demo
```

### 3. Monitoring
- Set up Cloud Logging
- Monitor API calls
- Track trading performance
- Set up alerts for errors

## Testing Checklist

### Demo Sandbox Testing
- [ ] OAuth authentication works
- [ ] Account information retrieved
- [ ] Trading permissions validated
- [ ] Market data accessible
- [ ] Order placement works (test orders)
- [ ] Position tracking works
- [ ] Portfolio summary accurate

### Live Account Testing
- [ ] OAuth authentication works
- [ ] Account information retrieved
- [ ] Trading permissions validated
- [ ] Market data accessible
- [ ] Small test order placed successfully
- [ ] Position tracking works
- [ ] Portfolio summary accurate

## Troubleshooting

### Common Issues

#### 1. Authentication Failed
- Check Consumer Key and Secret
- Verify Account ID
- Ensure trading permissions enabled
- Check network connectivity

#### 2. Trading Permissions Denied
- Contact ETrade support
- Verify account status
- Check for account restrictions
- Ensure sufficient funds

#### 3. API Rate Limits
- Implement rate limiting
- Use exponential backoff
- Monitor API usage
- Consider upgrading API plan

#### 4. Order Placement Failed
- Check account balance
- Verify symbol validity
- Check market hours
- Review order parameters

### Debug Commands

```bash
# Test OAuth only
python3 modules/prime_etrade_oauth.py

# Test trader only
python3 modules/prime_etrade_trader.py

# Full integration test
python3 scripts/test_etrade_integration.py

# Check configuration
python3 -c "from modules.prime_etrade_oauth import PrimeETradeOAuth; print(PrimeETradeOAuth().credentials)"
```

## Production Deployment

### 1. Pre-deployment Checklist
- [ ] Demo Sandbox fully tested
- [ ] Live account OAuth working
- [ ] Trading permissions validated
- [ ] Risk management configured
- [ ] Monitoring set up
- [ ] Alerts configured
- [ ] Backup procedures in place

### 2. Go-Live Process
1. Deploy to Google Cloud with Demo mode
2. Run for 24-48 hours in Demo mode
3. Verify all systems working
4. Switch to Live mode
5. Start with small position sizes
6. Monitor closely for first week
7. Gradually increase position sizes

### 3. Post-deployment Monitoring
- Monitor trading performance
- Track API usage and costs
- Watch for errors or issues
- Review daily performance reports
- Adjust parameters as needed

## Support and Resources

### ETrade Resources
- [ETrade Developer Portal](https://developer.etrade.com)
- [API Documentation](https://developer.etrade.com/api-documentation)
- [Support Center](https://us.etrade.com/etrade/support)

### System Resources
- [Prime ETrade OAuth Module](modules/prime_etrade_oauth.py)
- [Prime ETrade Trader Module](modules/prime_etrade_trader.py)
- [Integration Test Script](scripts/test_etrade_integration.py)
- [Setup Script](scripts/setup_etrade_oauth.py)

## Conclusion

The ETrade OAuth integration provides secure, reliable access to both Demo Sandbox and Live trading accounts. Follow this guide carefully to ensure proper setup and deployment.

**Remember**: Always test thoroughly in Demo mode before switching to Live trading!

---

*Generated on: 2024-12-19*  
*Version: 1.0*  
*Status: Ready for Deployment*
