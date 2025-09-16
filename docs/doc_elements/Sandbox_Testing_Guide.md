# 🧪 Sandbox Testing Guide

## Current Sandbox Status

### **Environment Setup**
- ✅ **Sandbox OAuth**: Working correctly
- ✅ **API Endpoints**: `https://apisb.etrade.com` configured
- ✅ **Token Management**: Valid sandbox tokens
- ⚠️ **Demo Accounts**: 0 accounts (normal for fresh sandbox)

### **ETrade Sandbox Characteristics**
- **Stored Data**: Uses canned/stored responses for testing
- **No Real Money**: All transactions are simulated
- **Limited Real-time Data**: Responses may not be current
- **Symbol Flexibility**: May return data for different symbols than requested
- **Purpose**: Test application logic and syntax without real account impact

## Sandbox Testing Strategy

### **Phase 1: API Integration Testing**
Test all API endpoints and OAuth functionality:

```bash
# Test OAuth integration
python3 ETradeOAuth/simple_oauth_cli.py test sandbox

# Test account list (may return 0 accounts)
python3 ETradeOAuth/correct_oauth_balance_checker.py --sandbox

# Test market data endpoints
python3 tests/test_sandbox_market_data.py
```

### **Phase 2: Mock Account Testing**
Create mock account scenarios for comprehensive testing:

```python
# Mock sandbox account scenarios
SANDBOX_SCENARIOS = {
    "small_account": {
        "balance": 1000.0,
        "cash_available": 800.0,
        "description": "Small demo account ($1000)"
    },
    "medium_account": {
        "balance": 10000.0,
        "cash_available": 8000.0,
        "description": "Medium demo account ($10k)"
    },
    "large_account": {
        "balance": 100000.0,
        "cash_available": 80000.0,
        "description": "Large demo account ($100k)"
    }
}
```

### **Phase 3: Risk Management Testing**
Test all risk management scenarios with mock data:

1. **Position Sizing**: Test with different account sizes
2. **Confidence Scaling**: Validate confidence multipliers
3. **Safe Mode**: Test drawdown protection
4. **News Sentiment**: Test sentiment filtering
5. **Transaction Costs**: Validate cost modeling

### **Phase 4: Trading Workflow Testing**
Test complete trading workflow with sandbox endpoints:

1. **Signal Generation**: Test all signal types
2. **Order Preview**: Test order validation (no execution)
3. **Position Tracking**: Test position management
4. **Risk Assessment**: Test all risk scenarios
5. **Monitoring**: Test alerts and reporting

## Implementation Plan

### **Step 1: Create Sandbox Test Suite**
Create comprehensive test suite for sandbox environment:

```python
# tests/test_sandbox_complete.py
class SandboxTestSuite:
    def test_sandbox_oauth_integration(self):
        """Test OAuth with sandbox endpoints"""
    
    def test_mock_account_scenarios(self):
        """Test with mock account data"""
    
    def test_risk_management_sandbox(self):
        """Test risk management with sandbox"""
    
    def test_trading_workflow_sandbox(self):
        """Test complete trading workflow"""
```

### **Step 2: Mock Data Integration**
Integrate mock data for comprehensive testing:

```python
# Mock ETrade API responses for testing
MOCK_SANDBOX_RESPONSES = {
    "account_list": {
        "Accounts": {
            "Account": [
                {
                    "accountId": "SANDBOX001",
                    "accountIdKey": "sandbox_key_001",
                    "accountName": "Demo Account 1",
                    "accountMode": "CASH",
                    "institutionType": "BROKERAGE",
                    "accountStatus": "ACTIVE"
                }
            ]
        }
    },
    "account_balance": {
        "BalanceResponse": {
            "Computed": {
                "cashAvailableForInvestment": "8000.00",
                "cashBuyingPower": "8000.00",
                "totalAccountValue": "10000.00"
            }
        }
    }
}
```

### **Step 3: Sandbox-Specific Testing**
Test sandbox-specific features and limitations:

1. **API Response Handling**: Test with stored data responses
2. **Error Handling**: Test sandbox error scenarios
3. **Data Validation**: Test with non-real-time data
4. **Symbol Mapping**: Test symbol flexibility
5. **Performance Testing**: Test with sandbox response times

## Testing Scenarios

### **Scenario 1: Small Account ($1,000)**
- **Balance**: $1,000
- **Trading Cash**: $800 (80%)
- **Cash Reserve**: $200 (20%)
- **Max Position**: $80 (10% of trading cash)
- **Positions**: 10 concurrent max

### **Scenario 2: Medium Account ($10,000)**
- **Balance**: $10,000
- **Trading Cash**: $8,000 (80%)
- **Cash Reserve**: $2,000 (20%)
- **Max Position**: $800 (10% of trading cash)
- **Positions**: 12 concurrent max

### **Scenario 3: Large Account ($100,000)**
- **Balance**: $100,000
- **Trading Cash**: $80,000 (80%)
- **Cash Reserve**: $20,000 (20%)
- **Max Position**: $8,000 (10% of trading cash)
- **Positions**: 20 concurrent max

### **Scenario 4: High Confidence Trading**
- **Confidence**: 0.997 (ultra-high)
- **Multiplier**: 1.5x position size
- **Risk Level**: Optimized for high-confidence signals
- **Target**: Maximum profit capture

### **Scenario 5: Safe Mode Testing**
- **Drawdown**: 12% (exceeds 10% limit)
- **Safe Mode**: Activated
- **Protection**: No new trades allowed
- **Recovery**: Wait for drawdown reduction

## Expected Outcomes

### **API Integration**
- ✅ All sandbox endpoints accessible
- ✅ OAuth authentication working
- ✅ Account data retrieval (mock or real)
- ✅ Market data access (stored data)

### **Risk Management**
- ✅ Position sizing with different account sizes
- ✅ Confidence-based scaling
- ✅ Safe mode activation
- ✅ News sentiment filtering
- ✅ Transaction cost modeling

### **Trading Workflow**
- ✅ Signal generation and validation
- ✅ Risk assessment and approval
- ✅ Order preview and validation
- ✅ Position tracking and management
- ✅ Performance monitoring

## Next Steps

1. **Create Mock Account System**: Implement mock account scenarios
2. **Build Sandbox Test Suite**: Comprehensive testing framework
3. **Test All Scenarios**: Validate with different account sizes
4. **Document Results**: Record all test outcomes
5. **Prepare for Production**: Final validation before live trading

## Conclusion

The sandbox environment is ready for comprehensive testing. Even with 0 accounts, we can:

1. **Test API Integration**: Validate all endpoints and OAuth
2. **Mock Account Scenarios**: Test with different account sizes
3. **Validate Risk Management**: Test all risk scenarios
4. **Test Trading Workflow**: Complete end-to-end testing
5. **Prepare for Production**: Final validation before deployment

This approach provides thorough testing while working within sandbox limitations and prepares the system for production deployment with confidence.
