# ETrade Credentials Setup Guide

## Quick Setup Instructions

### Step 1: Get Your ETrade Credentials

1. **Visit ETrade Developer Portal**
   - Go to: https://developer.etrade.com
   - Log in with your ETrade account

2. **Create New Application**
   - Click "Create New App"
   - Choose "Sandbox" for Demo testing
   - Choose "Production" for Live trading
   - Fill in application details:
     - App Name: "V2 Easy ETrade Strategy"
     - Description: "Automated trading system"
     - Callback URL: `oob`

3. **Get Your Credentials**
   - Copy the **Consumer Key**
   - Copy the **Consumer Secret**
   - Note your **Account ID**

### Step 2: Configure the System

1. **Edit the configuration file:**
   ```bash
   nano configs/etrade-oauth.env
   ```

2. **Replace the placeholder values:**
   ```env
   # Demo Sandbox Credentials
   ETRADE_DEMO_CONSUMER_KEY=your_actual_demo_consumer_key
   ETRADE_DEMO_CONSUMER_SECRET=your_actual_demo_consumer_secret
   ETRADE_DEMO_ACCOUNT_ID=your_actual_demo_account_id

   # Live Account Credentials
   ETRADE_LIVE_CONSUMER_KEY=your_actual_live_consumer_key
   ETRADE_LIVE_CONSUMER_SECRET=your_actual_live_consumer_secret
   ETRADE_LIVE_ACCOUNT_ID=your_actual_live_account_id
   ```

### Step 3: Test the Configuration

1. **Test corrected authentication:**
   ```bash
   python3 scripts/test_corrected_etrade_auth.py
   ```

2. **Test full integration:**
   ```bash
   python3 scripts/simple_etrade_test.py
   ```

### Step 4: Test with Demo Sandbox

1. **Start the system in Demo mode:**
   ```bash
   python3 improved_main.py --etrade-mode demo
   ```

2. **Monitor the logs for authentication success**

## Authorization URL Format

ETrade uses this specific URL format for authorization:
```
https://us.etrade.com/e/t/etws/authorize?key=YOUR_CONSUMER_KEY&token=YOUR_CONSUMER_SECRET
```

## Security Notes

- ⚠️ **Never commit** `configs/etrade-oauth.env` to version control
- 🔒 **Keep credentials secure** and don't share them
- 🧪 **Test with Demo Sandbox first** before using Live credentials
- 📝 **Document your credentials** in a secure password manager

## Troubleshooting

### Common Issues:
1. **"Consumer Key not configured"** - Make sure you've replaced the placeholder values
2. **"Authentication failed"** - Check that your credentials are correct
3. **"API call failed"** - Verify your ETrade account has API access enabled

### Getting Help:
- Check the logs for detailed error messages
- Verify your credentials at https://developer.etrade.com
- Contact ETrade support if needed

## Next Steps After Configuration

1. ✅ Configure credentials
2. ✅ Test authentication
3. ✅ Test with Demo Sandbox
4. 🚀 Deploy to Google Cloud
5. 💰 Switch to Live trading when ready

---

*This guide uses the corrected ETrade OAuth key/token authentication method.*
