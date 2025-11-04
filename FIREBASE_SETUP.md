# Firebase Setup Guide

## Quick Setup Steps

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"** or select existing project
3. Enter project name: `NSS BloodLink` (or your preferred name)
4. Click **"Continue"** → **"Create project"** → Wait for completion

### 2. Add Web App
1. In Firebase Console, click the **Web icon** (`</>`)
2. Register app with nickname: `NSS BloodLink Web`
3. **Copy the Firebase config object** (you'll see it in a code block)

### 3. Enable Email/Password Authentication
1. Go to **Authentication** → **Sign-in method**
2. Click on **Email/Password**
3. Toggle **Enable** to ON
4. Click **Save**

### 4. Update `.env` File
Open `/frontend/.env` and replace with your Firebase config:

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_FIREBASE_API_KEY=AIzaSy...your-actual-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
VITE_FIREBASE_APP_ID=1:123456789012:web:abc123def456
VITE_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
```

### 5. Restart Development Server
After updating `.env`:
```bash
# Stop the server (Ctrl+C)
# Restart it
cd frontend
npm run dev
```

## Where to Find Your Firebase Config

### Method 1: From Firebase Console
1. Go to **Project Settings** (gear icon)
2. Scroll to **"Your apps"** section
3. Click on your web app
4. You'll see the config object with all values

### Method 2: From Add App Dialog
When you first add the web app, the config is shown immediately

## Example Firebase Config Object

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567",
  authDomain: "nss-bloodlink.firebaseapp.com",
  projectId: "nss-bloodlink",
  storageBucket: "nss-bloodlink.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abc123def456",
  measurementId: "G-XXXXXXXXXX"
}
```

## Troubleshooting

### Error: "api-key-not-valid"
- ✅ Make sure you copied the **complete** API key from Firebase Console
- ✅ API key should start with `AIzaSy...`
- ✅ Restart the dev server after updating `.env`

### Error: "auth/operation-not-allowed"
- ✅ Enable Email/Password in Authentication → Sign-in method

### Error: "auth/network-request-failed"
- ✅ Check your internet connection
- ✅ Check Firebase project is active

### Still having issues?
1. Clear browser cache
2. Check browser console for detailed error messages
3. Verify all environment variables are correct in `.env`
4. Make sure dev server was restarted after `.env` changes

