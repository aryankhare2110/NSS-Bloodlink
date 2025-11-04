import { useState, useEffect } from "react"
import { LogOut } from "lucide-react"
import { motion } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/components/ui/toast"
import { PageTransition } from "@/components/PageTransition"

export default function Settings() {
  const { addToast } = useToast()
  const [darkMode, setDarkMode] = useState(false)
  const [notificationsEnabled, setNotificationsEnabled] = useState(true)

  // Load dark mode preference from localStorage
  useEffect(() => {
    const savedDarkMode = localStorage.getItem("darkMode") === "true"
    setDarkMode(savedDarkMode)
    if (savedDarkMode) {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }
  }, [])

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

  const handleNotificationsToggle = (checked: boolean) => {
    setNotificationsEnabled(checked)
    addToast(
      checked
        ? "Push notifications enabled"
        : "Push notifications disabled",
      "info"
    )
  }

  const handleLogout = () => {
    addToast("Logged out successfully", "success")
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
                        NSS Coordinator
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
                        coordinator@nssbloodlink.org
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
                    <Button
                      onClick={handleLogout}
                      variant="destructive"
                      className="w-full sm:w-auto hover:shadow-lg transition-all"
                    >
                      <LogOut className="mr-2 h-5 w-5" />
                      Logout
                    </Button>
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