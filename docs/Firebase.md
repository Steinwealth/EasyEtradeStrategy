# Frontend ⋅ Firebase Hosting for ETrade OAuth Access Keys
## V2 ETrade Strategy - OAuth Web App Frontend

**Last Updated**: September 15, 2025  
**Version**: 2.0  
**Purpose**: Complete guide for deploying the OAuth token management web app to Firebase Hosting with countdown timer and daily renewal interface.

---

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Frontend Setup](#frontend-setup)
4. [Environment Configuration](#environment-configuration)
5. [Build Process](#build-process)
6. [Firebase Deployment](#firebase-deployment)
7. [OAuth Web App Features](#oauth-web-app-features)
8. [Countdown Timer Implementation](#countdown-timer-implementation)
9. [Troubleshooting](#troubleshooting)
10. [Deployment Commands](#deployment-commands)

---

## 🎯 **Overview**

This guide covers deploying the OAuth token management web app to Firebase Hosting. The frontend provides:

- **Daily Token Renewal Interface**: Mobile-friendly OAuth token management
- **Countdown Timer**: Real-time countdown showing token expiration
- **One-Click Renewal**: Direct links to E*TRADE authorization
- **Status Dashboard**: Token health and renewal history
- **Mobile Optimization**: Responsive design for mobile devices

### Architecture

```
Firebase Hosting (Frontend)
    ↓ (API calls)
Google Cloud Run (OAuth Backend)
    ↓ (stores/retrieves)
Google Secret Manager (Tokens)
    ↓ (notifies)
Pub/Sub (Trading Service Updates)
```

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
