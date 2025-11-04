import { useState, useEffect } from "react"
import { HeartPulse, Hospital, Users, Sparkles, Bot } from "lucide-react"
import { motion } from "framer-motion"
import { DonorMap } from "@/components/DonorMap"
import { PageTransition } from "@/components/PageTransition"
import { CardSkeleton, MapSkeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  progress: number
  delay: number
}

function StatCard({ title, value, icon, progress, delay }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className="overflow-hidden">
        {/* Gradient Header */}
        <div className="h-20 bg-gradient-to-r from-red-600 to-red-400 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/20 backdrop-blur-sm shadow-sm">
              {icon}
            </div>
            <div>
              <p className="text-sm font-medium text-white/90">{title}</p>
              <p className="text-2xl font-bold text-white">{value}</p>
            </div>
          </div>
        </div>
        
        {/* Progress Indicator */}
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">Progress</span>
            <span className="text-xs font-medium text-foreground">{progress}%</span>
          </div>
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.8, delay: delay + 0.2 }}
              className="h-full bg-gradient-to-r from-red-600 to-red-400 rounded-full"
            />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 1000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <PageTransition>
      <div className="min-h-screen bg-background">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-foreground mb-4">
            Welcome back, NSS Coordinator!
          </h1>
          <p className="text-muted-foreground">
            Here's what's happening with your blood donation platform today.
          </p>
        </div>

          {/* Stats Cards */}
          <div className="mb-12 grid gap-6 sm:grid-cols-1 md:grid-cols-3">
            {isLoading ? (
              <>
                <CardSkeleton />
                <CardSkeleton />
                <CardSkeleton />
              </>
            ) : (
              <>
                <StatCard
                  title="Active Donors"
                  value={156}
                  icon={<HeartPulse className="h-5 w-5 text-white" />}
                  progress={78}
                  delay={0.1}
                />
                <StatCard
                  title="Open Requests"
                  value={24}
                  icon={<Hospital className="h-5 w-5 text-white" />}
                  progress={60}
                  delay={0.2}
                />
                <StatCard
                  title="Upcoming Camps"
                  value={8}
                  icon={<Users className="h-5 w-5 text-white" />}
                  progress={40}
                  delay={0.3}
                />
              </>
            )}
          </div>

          {/* Map Section */}
          <div className="mb-12">
            <h2 className="text-lg font-medium text-gray-700 mb-2">
              Live Donor Map
            </h2>
            {isLoading ? (
              <MapSkeleton />
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
                className="relative"
              >
                <Card className="rounded-2xl border border-border shadow-md overflow-hidden p-0 h-[400px] hover:shadow-lg transition-shadow">
                  <DonorMap />
                  {/* Translucent Overlay Panel */}
                  <div className="absolute top-4 right-4 z-10 rounded-2xl bg-white/90 backdrop-blur-md border border-border/50 shadow-lg px-4 py-3 hover:shadow-xl transition-shadow">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                      <div>
                        <p className="text-xs font-medium text-muted-foreground">Active Donors</p>
                        <p className="text-lg font-bold text-foreground">28</p>
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}
          </div>

          {/* AI Insights Section */}
          <div>
            <h2 className="text-lg font-medium text-gray-700 mb-2 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              AI Insights
            </h2>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
            >
              <Card className="rounded-2xl border border-border shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="flex items-start gap-4 p-6">
                  {/* AI Avatar */}
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 shadow-sm">
                    <Bot className="h-5 w-5 text-primary" />
                  </div>
                  {/* AI Message */}
                  <div className="flex-1">
                    <div className="mb-1">
                      <span className="text-sm font-medium text-foreground">AI Assistant</span>
                    </div>
                    <p className="text-foreground leading-relaxed">
                      High potential donor activity detected near South Delhi. Consider scheduling a donation camp in this area to maximize engagement.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
      </div>
    </PageTransition>
  )
}