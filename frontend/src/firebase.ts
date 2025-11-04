import { initializeApp, getApps, type FirebaseApp } from "firebase/app"
import { getAuth, type Auth } from "firebase/auth"
import { getMessaging, getToken, onMessage, type Messaging } from "firebase/messaging"

// Dummy Firebase configuration (replace with actual config later)
const firebaseConfig = {
  apiKey: "AIzaSyDummy-Key-Replace-With-Actual-Key",
  authDomain: "nss-bloodlink-dummy.firebaseapp.com",
  projectId: "nss-bloodlink-dummy",
  storageBucket: "nss-bloodlink-dummy.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:dummy-app-id",
  measurementId: "G-DUMMY12345",
}

// VAPID key for web push notifications (dummy - replace with actual key)
const VAPID_KEY = "BEl62iUYgUivxIkv69yViEuiBIa40HIe9F5jVkS3z3K8jJ7F3jJ7F3jJ7F3jJ7F3jJ7F3jJ7F3jJ7F3jJ7F3jJ7F3jJ7F3j"

// Initialize Firebase app
let app: FirebaseApp | null = null
let auth: Auth | null = null
let messaging: Messaging | null = null

export function initializeFirebase(): FirebaseApp | null {
  // Only initialize if not already initialized
  if (getApps().length === 0) {
    try {
      app = initializeApp(firebaseConfig)
      console.log("✅ Firebase initialized successfully")
      
      // Initialize Auth
      if (typeof window !== "undefined") {
        try {
          auth = getAuth(app)
          console.log("✅ Firebase Auth initialized successfully")
        } catch (error) {
          console.warn("⚠️ Firebase Auth initialization failed:", error)
        }
      }
      
      // Initialize messaging only in browser environment
      if (typeof window !== "undefined" && "serviceWorker" in navigator) {
        try {
          messaging = getMessaging(app)
          console.log("✅ Firebase Messaging initialized successfully")
        } catch (error) {
          console.warn("⚠️ Firebase Messaging initialization failed:", error)
          // Messaging might not be available in development
        }
      }
    } catch (error) {
      console.error("❌ Firebase initialization error:", error)
      return null
    }
  } else {
    app = getApps()[0]
  }
  
  return app
}

/**
 * Request browser notification permission
 * @returns Promise<string | null> - Returns FCM token if successful, null otherwise
 */
export async function requestPermission(): Promise<string | null> {
  try {
    // Check if browser supports notifications
    if (!("Notification" in window)) {
      console.warn("⚠️ This browser does not support notifications")
      return null
    }

    // Check if service worker is supported
    if (!("serviceWorker" in navigator)) {
      console.warn("⚠️ This browser does not support service workers")
      return null
    }

    // Request notification permission
    const permission = await Notification.requestPermission()
    
    if (permission === "granted") {
      console.log("✅ Notification permission granted")
      
      // Initialize Firebase if not already initialized
      if (!app) {
        initializeFirebase()
      }

      // Get FCM token if messaging is available
      if (messaging) {
        try {
          const token = await getToken(messaging, {
            vapidKey: VAPID_KEY,
          })
          
          if (token) {
            console.log("✅ FCM token obtained:", token)
            // Store token in localStorage for persistence
            localStorage.setItem("fcm_token", token)
            return token
          } else {
            console.warn("⚠️ No FCM token available")
            return null
          }
        } catch (error) {
          console.error("❌ Error getting FCM token:", error)
          return null
        }
      } else {
        console.warn("⚠️ Firebase Messaging not available")
        return null
      }
    } else if (permission === "denied") {
      console.warn("⚠️ Notification permission denied")
      return null
    } else {
      console.warn("⚠️ Notification permission dismissed")
      return null
    }
  } catch (error) {
    console.error("❌ Error requesting notification permission:", error)
    return null
  }
}

/**
 * Setup listener for incoming FCM messages
 * @param callback - Callback function to handle incoming messages
 */
export function onMessageListener(callback: (payload: any) => void): (() => void) | null {
  if (!messaging) {
    // Initialize Firebase if not already initialized
    if (!app) {
      initializeFirebase()
    }
    
    if (!messaging) {
      console.warn("⚠️ Firebase Messaging not available")
      return null
    }
  }

  try {
    // Listen for foreground messages
    const unsubscribe = onMessage(messaging, (payload) => {
      console.log("📨 Received foreground message:", payload)
      callback(payload)
    })

    return unsubscribe
  } catch (error) {
    console.error("❌ Error setting up message listener:", error)
    return null
  }
}

/**
 * Check if notification permission is granted
 */
export function hasNotificationPermission(): boolean {
  if (!("Notification" in window)) {
    return false
  }
  return Notification.permission === "granted"
}

/**
 * Simulate receiving a push notification (for testing)
 * This will trigger a browser notification and callback
 */
export function simulatePushNotification(
  title: string,
  body: string,
  data?: any
): void {
  if (hasNotificationPermission()) {
    // Show browser notification
    new Notification(title, {
      body,
      icon: "/favicon.ico", // You can add a custom icon
      badge: "/favicon.ico",
      tag: "blood-request", // Prevents duplicate notifications
      requireInteraction: false,
      data,
    })

    // Also trigger the callback as if it came from FCM
    const mockPayload = {
      notification: {
        title,
        body,
      },
      data: data || {},
    }

    // Dispatch custom event for components to listen to
    window.dispatchEvent(
      new CustomEvent("fcm_message", {
        detail: mockPayload,
      })
    )
  }
}

// Initialize Firebase on module load
if (typeof window !== "undefined") {
  initializeFirebase()
}

export { app, auth, messaging }

