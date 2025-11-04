import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/components/ui/toast"
import { PageTransition } from "@/components/PageTransition"
import { requestPermission, hasNotificationPermission, onMessageListener } from "@/firebase"

export default function Settings() {
  const { addToast } = useToast()
  const [darkMode, setDarkMode] = useState(false)
  const [notificationsEnabled, setNotificationsEnabled] = useState(false)

  // Load preferences from localStorage
  useEffect(() => {
    const savedDarkMode = localStorage.getItem("darkMode") === "true"
    setDarkMode(savedDarkMode)
    if (savedDarkMode) {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }

    // Check if notifications are enabled
    const savedNotifications = localStorage.getItem("notificationsEnabled") === "true"
    setNotificationsEnabled(savedNotifications || hasNotificationPermission())
  }, [])

  // Setup FCM message listener when notifications are enabled
  useEffect(() => {
    if (notificationsEnabled && hasNotificationPermission()) {
      const unsubscribe = onMessageListener((payload) => {
        console.log("📨 Received FCM message:", payload)
        
        // Show toast notification
        const notification = payload.notification
        if (notification) {
          addToast(
            notification.body || notification.title || "New notification",
            "info"
          )
        }
      })

      return () => {
        if (unsubscribe) {
          unsubscribe()
        }
      }
    }
  }, [notificationsEnabled, addToast])

  const handleDarkModeToggle = (checked: boolean) => {
    setDarkMode(checked)
    localStorage.setItem("darkMode", checked.toString())
    if (checked) {
      document.documentElement.classList.add("dark")
      addToast("Dark mode enabled", "success")
    } else {
      document.documentElement.classList.remove("dark")
      addToast("Light mode enabled", "success")
    }
  }

  const handleNotificationsToggle = async (checked: boolean) => {
    if (checked) {
      // Request notification permission
      try {
        const token = await requestPermission()
        
        if (token) {
          setNotificationsEnabled(true)
          localStorage.setItem("notificationsEnabled", "true")
          addToast("Notifications enabled", "success")
        } else {
          // Permission denied or not available
          setNotificationsEnabled(false)
          localStorage.setItem("notificationsEnabled", "false")
          
          if (Notification.permission === "denied") {
            addToast("Notification permission denied. Please enable in browser settings.", "error")
          } else {
            addToast("Failed to enable notifications", "error")
          }
        }
      } catch (error) {
        console.error("Error requesting notification permission:", error)
        setNotificationsEnabled(false)
        localStorage.setItem("notificationsEnabled", "false")
        addToast("Failed to enable notifications", "error")
      }
    } else {
      // Disable notifications
      setNotificationsEnabled(false)
      localStorage.setItem("notificationsEnabled", "false")
      addToast("Notifications disabled", "info")
    }
  }


  return (
    <PageTransition>
      <div className="min-h-screen bg-background flex flex-col">
        <div className="mx-auto max-w-2xl flex-1">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-foreground mb-4">
              Settings
            </h1>
            <p className="text-muted-foreground">
              Manage your account and preferences
            </p>
          </div>

          {/* Main Settings Card - Vertical Layout */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="p-0">
                {/* Profile Section */}
                <div className="p-6">
                  <h2 className="text-gray-600 uppercase text-sm tracking-wider mb-4">
                    Profile
                  </h2>
                  <div className="space-y-4">
                    <div>
                      <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Name
                      </label>
                      <p className="mt-1 text-foreground">
                        {localStorage.getItem("user_name") || "NSS Coordinator"}
                      </p>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Role
                      </label>
                      <p className="mt-1 text-foreground">
                        Administrator
                      </p>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Email
                      </label>
                      <p className="mt-1 text-foreground">
                        {localStorage.getItem("user_email") || "coordinator@nssbloodlink.org"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Divider */}
                <div className="border-t border-gray-200" />

                {/* Notifications Section */}
                <div className="p-6">
                  <h2 className="text-gray-600 uppercase text-sm tracking-wider mb-4">
                    Notifications
                  </h2>
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-foreground">
                        Push Alerts
                      </label>
                      <p className="text-sm text-muted-foreground mt-0.5">
                        Receive notifications for new blood requests
                      </p>
                    </div>
                    <Switch
                      checked={notificationsEnabled}
                      onCheckedChange={handleNotificationsToggle}
                    />
                  </div>
                </div>

                {/* Divider */}
                <div className="border-t border-gray-200" />

                {/* Preferences Section */}
                <div className="p-6">
                  <h2 className="text-gray-600 uppercase text-sm tracking-wider mb-4">
                    Preferences
                  </h2>
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-foreground">
                        Dark Mode
                      </label>
                      <p className="text-sm text-muted-foreground mt-0.5">
                        Switch between light and dark theme
                      </p>
                    </div>
                    <Switch
                      checked={darkMode}
                      onCheckedChange={handleDarkModeToggle}
                    />
                  </div>
                </div>

                {/* Divider */}
                <div className="border-t border-gray-200" />

                    {/* Actions Section */}
                    <div className="p-6">
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                        <a
                          href="#"
                          className="text-sm text-primary hover:underline transition-all"
                          onClick={(e) => {
                            e.preventDefault()
                            addToast("Privacy Policy opened", "info")
                          }}
                        >
                          Privacy Policy
                        </a>
                        <p className="text-xs text-muted-foreground">
                          Use the logout button in the navbar to sign out
                        </p>
                      </div>
                    </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Footer */}
        <div className="mt-auto py-6 text-center">
          <p className="text-sm text-muted-foreground">
            Built with ❤️ by Soup from IIIT-Delhi
          </p>
        </div>
      </div>
    </PageTransition>
  )
}