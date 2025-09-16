# ETrade Demo Sandbox Setup Guide

## 🎯 Ready for Demo Sandbox Configuration

Your ETrade OAuth configuration is ready with the corrected authentication method. Here's how to set up your Demo Sandbox for testing.

## Step 1: Get ETrade Demo Sandbox Credentials

### 1.1 Visit ETrade Developer Portal
- Go to: https://developer.etrade.com
- Log in with your ETrade account

### 1.2 Create Demo Sandbox Application
- Click "Create New App"
- Select **"Sandbox"** environment (for testing - no real money)
- Fill in application details:
  - **App Name**: "V2 Easy ETrade Strategy Demo"
  - **Description**: "Automated trading system for testing"
  - **Callback URL**: `oob`

### 1.3 Get Your Demo Credentials
After creating the app, you'll receive:
- **Consumer Key** (starts with letters/numbers)
- **Consumer Secret** (longer string)
- **Account ID** (your sandbox account number)

## Step 2: Configure Demo Sandbox Credentials

### 2.1 Edit Configuration File
```bash
nano configs/etrade-oauth.env
```

### 2.2 Update Demo Sandbox Section
Replace these lines with your actual Demo Sandbox credentials:

```env
# Demo Sandbox Credentials
# ------------------------
ETRADE_DEMO_CONSUMER_KEY=your_actual_demo_consumer_key
ETRADE_DEMO_CONSUMER_SECRET=your_actual_demo_consumer_secret
ETRADE_DEMO_ACCOUNT_ID=your_actual_demo_account_id
```

**Example:**
```env
ETRADE_DEMO_CONSUMER_KEY=1c42e17d3aac17706380ad0961581a6f
ETRADE_DEMO_CONSUMER_SECRET=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
ETRADE_DEMO_ACCOUNT_ID=123456789
```

## Step 3: Test Demo Sandbox Configuration

### 3.1 Test Corrected Authentication
```bash
python3 scripts/test_corrected_etrade_auth.py
```

**Expected Output:**
- ✅ Authorization URL Format: PASSED
- ✅ Key/Token Authentication: PASSED (if credentials are correct)
- ✅ Guide Generation: PASSED

### 3.2 Test Simple Integration
```bash
python3 scripts/simple_etrade_test.py
```

**Expected Output:**
- ✅ Credentials: PASSED
- ✅ API Connectivity: PASSED (with correct credentials)
- ✅ OAuth Signature: PASSED
- ✅ Configuration: PASSED

## Step 4: Test Demo Sandbox Trading

### 4.1 Start System in Demo Mode
```bash
python3 improved_main.py --etrade-mode demo --system-mode full_trading
```

### 4.2 Monitor Authentication
The system will:
1. Load your Demo Sandbox credentials
2. Generate the authorization URL
3. Prompt you to visit the URL for authorization
4. Ask for the verification code
5. Complete authentication

### 4.3 Expected Demo Sandbox Features
- **No Real Money**: All trades are simulated
- **Real Market Data**: Uses actual market prices
- **Full API Access**: Complete trading functionality
- **Safe Testing**: Perfect for system validation

## Step 5: Verify Demo Sandbox Access

### 5.1 Check Account Information
The system will display:
- Account ID
- Account type (Demo/Sandbox)
- Trading permissions
- Available balance

### 5.2 Test Trading Functions
- Market data retrieval
- Order placement (simulated)
- Position tracking
- Portfolio monitoring

## Authorization URL Format

Your Demo Sandbox will use this URL format:
```
https://us.etrade.com/e/t/etws/authorize?key=YOUR_DEMO_CONSUMER_KEY&token=YOUR_DEMO_CONSUMER_SECRET
```

## Demo Sandbox Benefits

### ✅ Safe Testing Environment
- No real money at risk
- Full trading functionality
- Real market data
- Complete API access

### ✅ System Validation
- Test all trading strategies
- Validate signal generation
- Check order execution
- Monitor performance

### ✅ Production Preparation
- Verify authentication works
- Test all system components
- Validate configuration
- Prepare for live deployment

## Troubleshooting

### Common Issues:

1. **"Consumer Key not configured"**
   - Make sure you've replaced the placeholder values
   - Check for typos in the configuration file

2. **"Authentication failed"**
   - Verify your credentials are correct
   - Check that you're using Demo Sandbox credentials

3. **"API call failed"**
   - Ensure your ETrade account has API access
   - Check network connectivity

### Getting Help:
- Check the logs for detailed error messages
- Verify credentials at https://developer.etrade.com
- Contact ETrade support if needed

## Next Steps After Demo Setup

1. ✅ Configure Demo Sandbox credentials
2. ✅ Test authentication
3. ✅ Validate trading functionality
4. 🚀 Deploy to Google Cloud
5. 💰 Configure Live trading when ready

## Security Notes

- 🔒 **Keep Demo credentials secure** (even though no real money)
- 📝 **Document your credentials** in a secure password manager
- ⚠️ **Never commit** `configs/etrade-oauth.env` to version control
- 🧪 **Test thoroughly** before moving to Live trading

---

**Status**: Ready for Demo Sandbox Configuration  
**Authentication Method**: Corrected Key/Token Method  
**Next Step**: Configure your Demo Sandbox credentials
