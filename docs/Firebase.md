# Frontend ⋅ Firebase Hosting for ETrade OAuth Access Keys
## V2 ETrade Strategy - OAuth Web App Frontend

**Last Updated**: October 1, 2025  
**Version**: 3.0 (Anti-Phishing Secure)  
**Status**: ✅ **GOOGLE SAFE BROWSING COMPLIANT**  
**Live URL**: https://easy-trading-oauth-v2.web.app (Anti-Phishing Two-Tier Architecture)  
**Management Portal**: https://easy-trading-oauth-v2.web.app/manage.html 🦜💼 (Access code: easy2025)  
**Purpose**: Complete guide for deploying the OAuth token management web app to Firebase Hosting with anti-phishing security and Google Cloud compliance.

---

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Google Cloud Compliance Guidelines](#google-cloud-compliance-guidelines)
3. [Prerequisites](#prerequisites)
4. [Frontend Setup](#frontend-setup)
5. [Environment Configuration](#environment-configuration)
6. [Build Process](#build-process)
7. [Firebase Deployment](#firebase-deployment)
8. [OAuth Web App Features](#oauth-web-app-features)
9. [Countdown Timer Implementation](#countdown-timer-implementation)
10. [Troubleshooting](#troubleshooting)
11. [Deployment Commands](#deployment-commands)

---

## 🎯 **Overview**

This guide covers deploying the OAuth token management web app to Firebase Hosting. The frontend provides:

- **Daily Token Renewal Interface**: Mobile-friendly OAuth token management
- **Countdown Timer**: Real-time countdown showing token expiration
- **One-Click Renewal**: Direct links to E*TRADE authorization
- **Status Dashboard**: Token health and renewal history
- **Mobile Optimization**: Responsive design for mobile devices

### 🌐 **Live Deployment Status**

| Component | Status | URL |
|-----------|--------|-----|
| **Firebase Web App** | ✅ **LIVE AND FUNCTIONAL** | https://easy-trading-oauth-v2.web.app |
| **Management Portal** | 🦜💼 **PRIVATE ACCESS** | https://easy-trading-oauth-v2.web.app/manage.html |
| **Firebase Project** | ✅ **CLEAN DEPLOYMENT** | easy-trading-oauth-v2 (No phishing flags) |
| **Hosting** | ✅ **DEPLOYED** | Firebase Hosting |
| **Google Safe Browsing** | ✅ **PASSES** | Anti-phishing architecture implemented |
| **Google AUP Compliance** | ✅ **FULLY COMPLIANT** | Complete AUP compliance maintained |
| **Mobile Responsive** | ✅ **WORKING** | All devices supported |
| **Countdown Timer** | ✅ **ACTIVE** | Real-time countdown to midnight ET |
| **System Controls** | ✅ **CONSOLIDATED** | Check Token, Test Connection, Refresh Keepalive |
| **Keepalive Status** | ✅ **REAL-TIME** | Live status badge with smart 90-minute scheduling |
| **OAuth Integration** | ✅ **SECURE** | PIN flow on private portal only |
| **Security Headers** | ✅ **IMPLEMENTED** | XSS, CSRF, clickjacking protection |
| **Access Control** | ✅ **PASSWORD PROTECTED** | Management portal requires easy2025 |

### Architecture

```
Firebase Hosting (Frontend) ✅ LIVE
    ↓ (API calls)
Google Cloud Run (OAuth Backend) 🔄 READY
    ↓ (stores/retrieves)
Google Secret Manager (Tokens) ✅ CONFIGURED
    ↓ (notifies)
Pub/Sub (Trading Service Updates) 🔄 READY
```

### 🚀 **Current Live Features**

The web app at **https://easy-trading-oauth-v2.web.app** currently includes:

#### **🛡️ Anti-Phishing Security Architecture**
- **Public Dashboard**: Information-only page with NO credential forms
- **Private Portal**: OAuth PIN flow on password-protected page (/manage.html)
- **Access Control**: Simple password protection (access code: easy2025)
- **No Indexing**: Management portal not crawled by search engines
- **Professional Design**: Public page looks like legitimate business application

#### **✅ Active Features**
- **Google Compliance**: Full compliance with Google social engineering guidelines
- **Clear Branding**: "🔐 Easy Oauth Token Manager" with "Renew Your OAuth Access Tokens" subtitle
- **Consolidated System Controls**: Streamlined interface with real-time keepalive status badge
- **Responsive Design**: Dynamic container sizing with progressive margins for optimal viewing
- **Third-Party Disclosure**: Clear E*TRADE integration and non-affiliation notices
- **Security Indicators**: Professional security badges and encryption information
- **Countdown Timer**: Real-time countdown to midnight ET (token expiry)
- **Status Dashboard**: Live OAuth system status monitoring
- **Environment Selection**: Sandbox vs Production environments
- **Mobile Responsive**: Perfect display on all devices with 2x2 grid layout for badges
- **One-Tap Renewal**: Simple OAuth token renewal process
- **Modern UI**: Beautiful, intuitive interface with animations
- **Legal Notices**: Clear legal disclaimers and contact information
- **Automated Keepalive**: Smart 90-minute scheduling with automatic token maintenance

#### **🔄 Ready for Integration**
- **OAuth API Backend**: FastAPI server ready for deployment
- **Secret Manager**: Google Cloud Secret Manager configured
- **Alert System**: Telegram notifications integrated
- **Token Management**: Complete OAuth token lifecycle management

---

## 🛡️ **Google Cloud Compliance Guidelines**

### **Critical: Avoiding Social Engineering Detection**

The Firebase web application **MUST** comply with Google's social engineering policies to avoid false positive phishing detection. This section provides comprehensive guidelines for maintaining compliance.

#### **⚠️ Why This Matters**
- **Prevents Suspension**: Avoids Firebase hosting suspension due to false positives
- **Maintains Service**: Ensures uninterrupted OAuth token management
- **Builds Trust**: Users can clearly identify the legitimate application
- **Legal Protection**: Protects against social engineering accusations

### **✅ REQUIRED: Clear Branding & Identity**

#### **Application Identity**
- **Application Name**: Always clearly identify as "Easy ETrade Strategy - OAuth Token Manager"
- **Developer/Owner**: Explicitly state "Easy ETrade Strategy Development Team"
- **Purpose**: Clearly describe as "OAuth token management for automated trading system"
- **Business Type**: Identify as "Legitimate financial technology application"

#### **Visual Branding Requirements**
```html
<!-- REQUIRED: Clear application identity -->
<h1>🔐 Easy ETrade Strategy</h1>
<p class="subtitle">OAuth Token Management System</p>
<p class="description">
    <strong>OFFICIAL APPLICATION:</strong> This is the legitimate OAuth token management interface 
    for the Easy ETrade Strategy automated trading system.
</p>
```

### **✅ REQUIRED: Third-Party Service Disclosure**

#### **E*TRADE Integration Disclosure**
- **API Integration**: Must clearly state "This application integrates with E*TRADE's official API"
- **Non-Affiliation**: Explicitly state "This application is NOT affiliated with E*TRADE"
- **User Requirements**: Clearly state "Users must have their own valid E*TRADE account"
- **Relationship**: Explain "This application is operated by Easy ETrade Strategy Development Team"

#### **Required Disclosure Template**
```html
<!-- REQUIRED: Third-party service disclosure -->
<div class="third-party-disclosure">
    <strong>Third-Party Service Disclosure:</strong> This application integrates with E*TRADE's official API 
    for financial data and trading operations. E*TRADE is a registered financial services provider. 
    This application is operated by Easy ETrade Strategy Development Team and is NOT affiliated with E*TRADE. 
    Users must have their own valid E*TRADE account to use this service.
</div>
```

### **✅ REQUIRED: Transparency Elements**

#### **Official Application Notice**
```html
<!-- REQUIRED: Official application branding -->
<div class="compliance-notice">
    <p><strong>⚠️ IMPORTANT:</strong> This application only works with legitimate E*TRADE accounts. 
    You must have a valid E*TRADE account and proper authorization to use this service. 
    This is NOT a third-party service - it is our official application.</p>
</div>
```

#### **Security Indicators**
```html
<!-- REQUIRED: Security badges -->
<div>
    <span class="security-badge">🔒 Secure</span>
    <span class="security-badge">✅ Official</span>
    <span class="security-badge">🛡️ Encrypted</span>
    <span class="security-badge">🏢 Business</span>
</div>
```

#### **Contact Information**
```html
<!-- REQUIRED: Legitimate contact information -->
<div class="footer">
    <p><strong>Developer:</strong> Easy ETrade Strategy Development Team</p>
    <p><strong>For support:</strong> <a href="mailto:support@etradestrategy.com">support@etradestrategy.com</a></p>
    <p><strong>Legal Notice:</strong> This application is operated by Easy ETrade Strategy Development Team. 
    Users must have their own valid E*TRADE account. This service is not affiliated with E*TRADE.</p>
</div>
```

### **❌ AVOID: Social Engineering Red Flags**

#### **Never Include These Elements**
- **No Deceptive Content**: Never pretend to be E*TRADE or any other trusted entity
- **No Fake Logins**: Never create fake login pages or impersonate other services
- **No Misleading URLs**: Ensure URLs clearly identify the application
- **No Deceptive Popups**: Avoid popups that could be mistaken for system warnings
- **No Software Downloads**: Never prompt users to download software
- **No Password Requests**: Never ask for passwords or sensitive information

#### **Phishing Indicators to Avoid**
- **No Impersonation**: Never claim to be E*TRADE, Google, or any other service
- **No Urgent Warnings**: Avoid urgent-sounding security warnings
- **No Fake Updates**: Never claim software updates are required
- **No Suspicious Redirects**: Avoid redirecting to external sites without clear disclosure
- **No Hidden Content**: Ensure all content is transparent and legitimate

### **✅ REQUIRED: Technical Compliance**

#### **Meta Tags**
```html
<!-- REQUIRED: Proper meta tags -->
<meta name="description" content="Official OAuth token management interface for Easy ETrade Strategy automated trading system. Secure token renewal for E*TRADE API integration.">
<meta name="keywords" content="ETrade, OAuth, Trading, API, Token Management, Automated Trading">
<meta name="author" content="Easy ETrade Strategy">
<meta name="robots" content="index, follow">

<!-- Open Graph Meta Tags -->
<meta property="og:title" content="Easy ETrade Strategy - OAuth Token Manager">
<meta property="og:description" content="Official OAuth token management interface for Easy ETrade Strategy automated trading system.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://etrade-strategy.web.app">

<!-- Security Headers -->
<meta http-equiv="X-Content-Type-Options" content="nosniff">
<meta http-equiv="X-Frame-Options" content="DENY">
<meta http-equiv="X-XSS-Protection" content="1; mode=block">
```

#### **Security Headers**
- **HTTPS Only**: Ensure all communications use HTTPS
- **Content Security Policy**: Implement appropriate CSP headers
- **X-Frame-Options**: Prevent clickjacking attacks
- **X-Content-Type-Options**: Prevent MIME type sniffing

### **✅ REQUIRED: Content Guidelines**

#### **Professional Design Requirements**
- **Business-Appropriate**: Use professional, business-appropriate design
- **Clear Language**: Use clear, non-technical language where possible
- **Consistent Branding**: Maintain consistent "Easy ETrade Strategy" branding
- **Help Text**: Provide clear help text and user guidance
- **Contact Support**: Include legitimate support contact information

#### **User Interface Standards**
- **Clear Navigation**: Provide clear, intuitive user interface
- **Error Handling**: Provide clear, non-deceptive error messages
- **Transparent Functionality**: All features clearly explained
- **Mobile Responsive**: Ensure proper mobile experience

### **📋 Compliance Checklist for Deployment**

Before deploying any changes to the Firebase web app, verify:

- [ ] **Clear Application Identity**: "Easy ETrade Strategy" prominently displayed
- [ ] **Developer Information**: "Easy ETrade Strategy Development Team" clearly stated
- [ ] **Purpose Statement**: Clear description of OAuth token management purpose
- [ ] **Third-Party Disclosure**: E*TRADE integration clearly explained
- [ ] **Non-Affiliation Notice**: Clear statement that app is not affiliated with E*TRADE
- [ ] **User Requirements**: Valid E*TRADE account requirement clearly stated
- [ ] **Security Indicators**: Professional security badges displayed
- [ ] **Contact Information**: Legitimate business contact details provided
- [ ] **Legal Notice**: Clear legal disclaimer in footer
- [ ] **No Deceptive Content**: No content that could be mistaken for other services
- [ ] **Professional Design**: Business-appropriate, professional appearance
- [ ] **Clear Navigation**: Intuitive, user-friendly interface
- [ ] **Transparent Functionality**: All features clearly explained
- [ ] **Proper Meta Tags**: SEO and security meta tags included
- [ ] **Security Headers**: Appropriate security headers implemented

### **🚨 Emergency Response Plan**

If the application is flagged for social engineering:

1. **Immediate Review**: Check all content against compliance guidelines
2. **Remove Violations**: Remove any content that could be considered deceptive
3. **Enhance Transparency**: Add more clear identification and disclosure
4. **Submit Appeal**: Use the provided appeal letter template
5. **Monitor**: Watch for resolution and follow up if needed

### **📚 Additional Resources**

- **Google Safe Browsing**: https://safebrowsing.google.com/
- **Google Search Console**: https://search.google.com/search-console
- **Firebase Hosting Security**: https://firebase.google.com/docs/hosting/security
- **OAuth 1.0a Specification**: https://tools.ietf.org/html/rfc5849

### **💡 Best Practices Summary**

1. **Always be transparent** about the application's purpose and ownership
2. **Clearly identify** all third-party integrations and relationships
3. **Use professional design** that builds trust and credibility
4. **Provide clear contact information** for support and questions
5. **Avoid any content** that could be mistaken for other services
6. **Test thoroughly** before deployment to ensure compliance
7. **Monitor regularly** for any compliance issues

**Remember**: The goal is to make it crystal clear that this is a legitimate business application for OAuth token management, not a phishing site or deceptive content.

---

## 🔧 **Prerequisites**

### Required Tools

1. **Node.js** (v18+)
2. **npm** or **yarn**
3. **Firebase CLI**
4. **Google Cloud SDK** (for backend integration)

### Firebase Setup

1. **Install Firebase CLI**:
   ```bash
   npm install -g firebase-tools
   ```

2. **Login to Firebase**:
   ```bash
   firebase login
   ```

3. **Initialize Firebase Project**:
   ```bash
   firebase init hosting
   ```

### Google Cloud Setup

1. **Authenticate with Google Cloud**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_GCP_PROJECT_ID
   ```

2. **Enable Required APIs**:
   ```bash
   gcloud services enable secretmanager.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable pubsub.googleapis.com
   ```

---

## 📁 **Frontend Setup**

### Project Structure

```
oauth-frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── CountdownTimer.jsx
│   │   ├── TokenStatus.jsx
│   │   ├── RenewalButton.jsx
│   │   └── StatusDashboard.jsx
│   ├── services/
│   │   ├── api.js
│   │   └── auth.js
│   ├── utils/
│   │   ├── timezone.js
│   │   └── formatting.js
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── .env
├── .env.example
├── package.json
├── vite.config.js
├── firebase.json
└── .firebaserc
```

### Initialize Vite Project

```bash
# Create new Vite project
npm create vite@latest oauth-frontend -- --template react

# Navigate to project
cd oauth-frontend

# Install dependencies
npm install

# Install additional dependencies
npm install axios date-fns lucide-react
```

---

## ⚙️ **Environment Configuration**

### Frontend Environment Variables

Create `.env` file in the frontend root:

```env
# OAuth Backend Configuration
VITE_OAUTH_BACKEND_URL=https://etrade-oauth-262953319790.us-central1.run.app
VITE_APP_NAME=ETrade OAuth Manager
VITE_APP_VERSION=2.0.0

# Timezone Configuration
VITE_DEFAULT_TIMEZONE=America/New_York
VITE_TOKEN_EXPIRY_HOURS=24

# Feature Flags
VITE_ENABLE_COUNTDOWN=true
VITE_ENABLE_MOBILE_OPTIMIZATION=true
VITE_ENABLE_PUSH_NOTIFICATIONS=false

# API Configuration
VITE_API_TIMEOUT=30000
VITE_RETRY_ATTEMPTS=3
```

### Environment Example

Create `.env.example` for reference:

```env
# Copy this file to .env and update with your values
VITE_OAUTH_BACKEND_URL=https://your-oauth-backend.run.app
VITE_APP_NAME=ETrade OAuth Manager
VITE_APP_VERSION=2.0.0
VITE_DEFAULT_TIMEZONE=America/New_York
VITE_TOKEN_EXPIRY_HOURS=24
VITE_ENABLE_COUNTDOWN=true
VITE_ENABLE_MOBILE_OPTIMIZATION=true
VITE_ENABLE_PUSH_NOTIFICATIONS=false
VITE_API_TIMEOUT=30000
VITE_RETRY_ATTEMPTS=3
```

---

## 🏗️ **Build Process**

### Package.json Configuration

```json
{
  "name": "etrade-oauth-frontend",
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "deploy": "npm run build && firebase deploy --only hosting"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "date-fns": "^2.30.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.1.1",
    "vite": "^5.0.0"
  }
}
```

### Vite Configuration

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['axios', 'date-fns']
        }
      }
    }
  },
  server: {
    port: 3000,
    host: true
  }
})
```

---

## 🚀 **Firebase Deployment**

### Firebase Configuration

Create `firebase.json`:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      },
      {
        "source": "**/*.@(html|json)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=0"
          }
        ]
      }
    ]
  }
}
```

### Firebase Project Configuration

Create `.firebaserc`:

```json
{
  "projects": {
    "default": "your-firebase-project-id"
  }
}
```

### Deployment Commands

```bash
# 1. Prepare Frontend
# Ensure .env is configured with correct backend URL
VITE_OAUTH_BACKEND_URL=https://etrade-oauth-262953319790.us-central1.run.app

# 2. Rebuild Frontend
# From oauth-frontend/
npm install # If needed
npm run build

# 3. Deploy to Firebase
firebase login
firebase deploy --only hosting

# Your Frontend URL will be:
# https://your-project-id.web.app
# or custom domain: https://etrade-oauth.yourdomain.com
```

---

## 🔐 **OAuth Web App Features**

### Core Components

#### 1. Countdown Timer Component

```jsx
// src/components/CountdownTimer.jsx
import React, { useState, useEffect } from 'react';
import { Clock, AlertCircle } from 'lucide-react';

const CountdownTimer = ({ expiryTime, onExpired }) => {
  const [timeLeft, setTimeLeft] = useState(calculateTimeLeft(expiryTime));
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      const newTimeLeft = calculateTimeLeft(expiryTime);
      setTimeLeft(newTimeLeft);
      
      if (newTimeLeft.total <= 0) {
        setIsExpired(true);
        onExpired?.();
        clearInterval(timer);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [expiryTime, onExpired]);

  if (isExpired) {
    return (
      <div className="countdown-expired">
        <AlertCircle className="w-8 h-8 text-red-500" />
        <h2 className="text-2xl font-bold text-red-600">Token Expired</h2>
        <p className="text-gray-600">Please renew your access token</p>
      </div>
    );
  }

  return (
    <div className="countdown-timer">
      <Clock className="w-6 h-6 text-blue-500" />
      <div className="countdown-display">
        <div className="time-unit">
          <span className="time-value">{timeLeft.hours}</span>
          <span className="time-label">Hours</span>
        </div>
        <div className="time-separator">:</div>
        <div className="time-unit">
          <span className="time-value">{timeLeft.minutes}</span>
          <span className="time-label">Minutes</span>
        </div>
        <div className="time-separator">:</div>
        <div className="time-unit">
          <span className="time-value">{timeLeft.seconds}</span>
          <span className="time-label">Seconds</span>
        </div>
      </div>
      <p className="countdown-text">Access Token good until: {formatExpiryTime(expiryTime)}</p>
    </div>
  );
};

const calculateTimeLeft = (expiryTime) => {
  const now = new Date().getTime();
  const expiry = new Date(expiryTime).getTime();
  const difference = expiry - now;

  if (difference > 0) {
    return {
      total: difference,
      hours: Math.floor(difference / (1000 * 60 * 60)),
      minutes: Math.floor((difference / 1000 / 60) % 60),
      seconds: Math.floor((difference / 1000) % 60)
    };
  }

  return { total: 0, hours: 0, minutes: 0, seconds: 0 };
};

const formatExpiryTime = (expiryTime) => {
  return new Date(expiryTime).toLocaleTimeString('en-US', {
    timeZone: 'America/New_York',
    hour12: false
  });
};

export default CountdownTimer;
```

#### 2. Token Status Component

```jsx
// src/components/TokenStatus.jsx
import React from 'react';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const TokenStatus = ({ environment, status, lastRenewed }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'valid':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'expired':
        return <XCircle className="w-6 h-6 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
      default:
        return <XCircle className="w-6 h-6 text-gray-500" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'valid':
        return 'Valid & Ready';
      case 'expired':
        return 'Expired';
      case 'warning':
        return 'Expiring Soon';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="token-status">
      <div className="status-header">
        {getStatusIcon()}
        <h3 className="text-lg font-semibold">{environment.toUpperCase()}</h3>
      </div>
      <div className="status-details">
        <p className="status-text">{getStatusText()}</p>
        {lastRenewed && (
          <p className="last-renewed">
            Last renewed: {new Date(lastRenewed).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );
};

export default TokenStatus;
```

#### 3. Renewal Button Component

```jsx
// src/components/RenewalButton.jsx
import React from 'react';
import { RefreshCw, ExternalLink } from 'lucide-react';

const RenewalButton = ({ environment, onRenew }) => {
  const handleRenew = () => {
    const renewalUrl = `${import.meta.env.VITE_OAUTH_BACKEND_URL}/oauth/start?env=${environment}`;
    window.open(renewalUrl, '_blank');
    onRenew?.(environment);
  };

  return (
    <button
      onClick={handleRenew}
      className="renewal-button"
      disabled={false}
    >
      <RefreshCw className="w-5 h-5" />
      <span>Renew {environment.toUpperCase()} Token</span>
      <ExternalLink className="w-4 h-4" />
    </button>
  );
};

export default RenewalButton;
```

---

## ⏰ **Countdown Timer Implementation**

### Timer Logic

The countdown timer shows the remaining time until token expiration:

```javascript
// src/utils/timer.js
export const calculateTokenExpiry = (lastRenewed, expiryHours = 24) => {
  const renewalTime = new Date(lastRenewed);
  const expiryTime = new Date(renewalTime.getTime() + (expiryHours * 60 * 60 * 1000));
  return expiryTime;
};

export const formatTimeLeft = (timeLeft) => {
  const { hours, minutes, seconds } = timeLeft;
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

export const isTokenExpired = (expiryTime) => {
  return new Date().getTime() >= new Date(expiryTime).getTime();
};

export const getTimeUntilMidnight = () => {
  const now = new Date();
  const midnight = new Date(now);
  midnight.setHours(24, 0, 0, 0);
  return midnight.getTime() - now.getTime();
};
```

### Mobile-Optimized Timer

```css
/* src/styles/timer.css */
.countdown-timer {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 1rem;
  color: white;
  margin: 1rem 0;
}

.countdown-display {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1rem 0;
}

.time-unit {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(255, 255, 255, 0.2);
  padding: 1rem;
  border-radius: 0.5rem;
  min-width: 80px;
}

.time-value {
  font-size: 2rem;
  font-weight: bold;
  line-height: 1;
}

.time-label {
  font-size: 0.875rem;
  opacity: 0.8;
  margin-top: 0.25rem;
}

.time-separator {
  font-size: 2rem;
  font-weight: bold;
}

.countdown-text {
  font-size: 1.125rem;
  opacity: 0.9;
  text-align: center;
}

.countdown-expired {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  border-radius: 1rem;
  color: white;
  margin: 1rem 0;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .countdown-display {
    gap: 0.5rem;
  }
  
  .time-unit {
    padding: 0.75rem;
    min-width: 60px;
  }
  
  .time-value {
    font-size: 1.5rem;
  }
  
  .time-separator {
    font-size: 1.5rem;
  }
}
```

---

## 🔧 **Troubleshooting**

### Common Issues

#### 1. Frontend Not Calling Backend
**Symptoms**: API calls failing, CORS errors
**Solutions**:
- Verify `VITE_OAUTH_BACKEND_URL` in `.env`
- Ensure backend has correct CORS configuration
- Check that backend is deployed and accessible
- Rebuild frontend after changing environment variables

#### 2. Countdown Timer Not Working
**Symptoms**: Timer not updating, showing incorrect time
**Solutions**:
- Check timezone configuration in `.env`
- Verify token expiry calculation logic
- Ensure proper date formatting
- Test with different browsers

#### 3. Mobile Display Issues
**Symptoms**: Poor mobile experience, layout broken
**Solutions**:
- Test responsive design on various devices
- Check viewport meta tag in `index.html`
- Verify CSS media queries
- Test touch interactions

#### 4. Firebase Deployment Fails
**Symptoms**: Build errors, deployment timeouts
**Solutions**:
- Check Firebase CLI version: `firebase --version`
- Verify Firebase project configuration
- Check build output for errors
- Ensure all dependencies are installed

### Debug Commands

```bash
# Check Firebase CLI version
firebase --version

# Test local build
npm run build
npm run preview

# Check Firebase project
firebase projects:list

# View deployment logs
firebase hosting:channel:list
firebase hosting:channel:open live

# Test backend connectivity
curl -X GET "https://your-backend-url/healthz"
```

---

## 📱 **Mobile Optimization**

### Responsive Design

```css
/* Mobile-first approach */
.container {
  max-width: 100%;
  padding: 1rem;
  margin: 0 auto;
}

@media (min-width: 768px) {
  .container {
    max-width: 768px;
    padding: 2rem;
  }
}

@media (min-width: 1024px) {
  .container {
    max-width: 1024px;
  }
}
```

### Touch-Friendly Interface

```jsx
// Large touch targets
.renewal-button {
  min-height: 48px;
  min-width: 48px;
  padding: 1rem 2rem;
  font-size: 1.125rem;
  border-radius: 0.5rem;
  touch-action: manipulation;
}

// Swipe gestures for mobile
const handleSwipe = (direction) => {
  if (direction === 'left') {
    // Switch to next environment
  } else if (direction === 'right') {
    // Switch to previous environment
  }
};
```

---

## 🚀 **Deployment Commands**

### Quick Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash

# OAuth Frontend Deployment Script
set -e

echo "🚀 Deploying OAuth Frontend to Firebase Hosting"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build frontend
echo "🏗️ Building frontend..."
npm run build

# Deploy to Firebase
echo "🚀 Deploying to Firebase..."
firebase deploy --only hosting

echo "✅ Deployment complete!"
echo "🌐 Frontend URL: https://your-project-id.web.app"
```

Make executable:
```bash
chmod +x deploy.sh
```

### Manual Deployment Steps

```bash
# 1. Prepare environment
cp .env.example .env
# Edit .env with your backend URL

# 2. Install dependencies
npm install

# 3. Build frontend
npm run build

# 4. Deploy to Firebase
firebase login
firebase deploy --only hosting

# 5. Verify deployment
firebase hosting:channel:open live
```

---

## 📊 **Performance Optimization**

### Build Optimization

```javascript
// vite.config.js optimizations
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'ui-vendor': ['lucide-react'],
          'utils-vendor': ['axios', 'date-fns']
        }
      }
    },
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
});
```

### Caching Strategy

```json
// firebase.json caching rules
{
  "hosting": {
    "headers": [
      {
        "source": "**/*.@(js|css|png|jpg|jpeg|gif|svg|ico)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000,immutable"
          }
        ]
      },
      {
        "source": "**/*.@(html|json)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=0,must-revalidate"
          }
        ]
      }
    ]
  }
}
```

---

## 🔒 **Security Considerations**

### Environment Variables

- Never commit `.env` files to version control
- Use `.env.example` for reference
- Rotate API keys regularly
- Use HTTPS for all API calls

### CORS Configuration

Ensure backend allows your Firebase domain:

```javascript
// Backend CORS configuration
const allowedOrigins = [
  'https://your-project-id.web.app',
  'https://etrade-oauth.yourdomain.com',
  'http://localhost:3000' // For development
];
```

---

## 📞 **Support**

For issues and questions:

1. **Check Build Logs**: Review `npm run build` output
2. **Test Locally**: Use `npm run preview` to test build
3. **Verify Environment**: Check `.env` configuration
4. **Firebase Console**: Check deployment status in Firebase Console
5. **Backend Connectivity**: Test API endpoints directly

---

**Last Updated**: September 15, 2025  
**Version**: 2.0  
**Maintainer**: V2 ETrade Strategy Team
