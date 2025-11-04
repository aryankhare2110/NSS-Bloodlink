import { NavLink } from "react-router-dom"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  ClipboardList,
  Users,
  MapPin,
  Bot,
  Settings,
} from "lucide-react"

const navigationItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/requests", label: "Requests", icon: ClipboardList },
  { to: "/donors", label: "Donors", icon: Users },
  { to: "/camps", label: "Camps", icon: MapPin },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
  { to: "/settings", label: "Settings", icon: Settings },
]

export function Sidebar() {
  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-card lg:flex rounded-r-2xl">
      <div className="flex h-16 items-center border-b border-border px-6">
        <h2 className="text-lg font-semibold text-foreground">NSS BloodLink</h2>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navigationItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "relative flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all duration-200 hover:shadow-sm",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-foreground/70 hover:bg-muted hover:text-foreground"
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-0 h-full w-1 rounded-r-full bg-primary-foreground" />
                  )}
                  <Icon className="h-5 w-5" />
                  {item.label}
                </>
              )}
            </NavLink>
          )
        })}
      </nav>
    </div>
  )
}

export function BottomNavbar() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around border-t border-border bg-card px-2 py-2 backdrop-blur-lg backdrop-brightness-95 lg:hidden shadow-lg rounded-t-2xl">
      {navigationItems.map((item) => {
        const Icon = item.icon
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "flex flex-col items-center gap-1 rounded-2xl px-3 py-2 text-xs transition-all duration-200 hover:shadow-sm",
                isActive
                  ? "text-primary shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )
            }
          >
            <Icon className="h-5 w-5" />
            <span className="text-[10px] font-medium">{item.label}</span>
          </NavLink>
        )
      })}
    </nav>
  )
}