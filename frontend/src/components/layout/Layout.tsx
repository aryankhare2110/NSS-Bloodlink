import { Outlet } from "react-router-dom"
import { Sidebar, BottomNavbar } from "./Sidebar"
import { Navbar } from "./Navbar"
import { Footer } from "./Footer"

export function Layout() {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:block">
          <Sidebar />
        </aside>

        {/* Main Content */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-y-auto pb-20 lg:pb-0 scroll-smooth px-6">
            <div className="mx-auto max-w-[1440px] py-6">
              <Outlet />
            </div>
          </main>
          <Footer />
        </div>
      </div>

      {/* Mobile Bottom Navbar */}
      <BottomNavbar />
    </div>
  )
}