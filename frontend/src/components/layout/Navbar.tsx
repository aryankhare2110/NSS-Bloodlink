import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { useAuth } from "@/context/authContext"
import { LogOut } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { useToast } from "@/components/ui/toast"
import { Button } from "@/components/ui/button"

export function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { addToast } = useToast()

  const handleLogout = async () => {
    try {
      await logout()
      addToast("Logged out successfully", "success")
      navigate("/login")
    } catch (error: any) {
      console.error("Logout error:", error)
      addToast("Failed to logout", "error")
    }
  }

  // Get user info from localStorage or Firebase user
  const userName = user?.displayName || localStorage.getItem("user_name") || "User"
  const userEmail = user?.email || localStorage.getItem("user_email") || ""
  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center border-b border-border bg-card/80 backdrop-blur-lg backdrop-brightness-95 px-6 shadow-md">
      <div className="flex flex-1 items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">
          NSS BloodLink
        </h1>
        <div className="flex items-center gap-4">
          {/* User Info */}
          {user && (
            <div className="hidden sm:flex flex-col items-end mr-2">
              <p className="text-sm font-medium text-foreground">{userName}</p>
              <p className="text-xs text-muted-foreground">{userEmail}</p>
            </div>
          )}
          
          {/* Avatar */}
          <Avatar className="rounded-2xl hover:shadow-md transition-shadow">
            <AvatarFallback className="bg-primary text-primary-foreground font-medium rounded-2xl">
              {initials}
            </AvatarFallback>
          </Avatar>
          
          {/* Logout Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={handleLogout}
            className="rounded-2xl hover:shadow-sm transition-all"
            title="Logout"
          >
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </header>
  )
}