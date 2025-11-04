import { Avatar, AvatarFallback } from "@/components/ui/avatar"

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 flex h-16 items-center border-b border-border bg-card/80 backdrop-blur-lg backdrop-brightness-95 px-6 shadow-md">
      <div className="flex flex-1 items-center justify-between">
        <h1 className="text-xl font-semibold text-foreground">
          NSS BloodLink
        </h1>
        <div className="flex items-center gap-4">
          <Avatar className="rounded-2xl hover:shadow-md transition-shadow">
            <AvatarFallback className="bg-primary text-primary-foreground font-medium rounded-2xl">
              U
            </AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  )
}