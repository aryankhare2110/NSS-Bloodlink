import { useState, useEffect } from "react"
import { HeartPulse, Hospital, Users, Sparkles, Bot } from "lucide-react"
import { motion } from "framer-motion"
import { DonorMap } from "@/components/DonorMap"
import { PageTransition } from "@/components/PageTransition"
import { CardSkeleton, MapSkeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { useToast } from "@/components/ui/toast"
import { getDonors, getRequests, getAIRecommendation, type LocationRecommendation } from "@/services/api"

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
  const { addToast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState({
    activeDonors: 0,
    openRequests: 0,
    upcomingCamps: 8, // Mock for now, can be replaced with camps API later
  })
  const [aiRecommendation, setAiRecommendation] = useState<LocationRecommendation | null>(null)
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(true)
  const [availableDonorCount, setAvailableDonorCount] = useState(0)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        
        // Fetch donors and requests in parallel
        const [donors, requests] = await Promise.all([
          getDonors(true), // Only available donors
          getRequests("Pending"), // Only pending requests
        ])

        // Calculate stats
        const activeDonors = donors.length
        const openRequests = requests.length

        // Get available donor count for map overlay
        const allDonors = await getDonors()
        const availableCount = allDonors.filter((d) => d.available).length

        setStats({
          activeDonors,
          openRequests,
          upcomingCamps: 8, // Mock for now
        })
        setAvailableDonorCount(availableCount)
      } catch (error) {
        console.error("Error fetching dashboard data:", error)
        addToast("Server unavailable", "error")
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [addToast])

  // Listen for real-time updates via Socket.IO
  useEffect(() => {
    const handleDonorUpdate = async () => {
      // Refresh donor stats when donor status changes
      try {
        const donors = await getDonors(true)
        const allDonors = await getDonors()
        const availableCount = allDonors.filter((d) => d.available).length
        
        setStats((prev) => ({
          ...prev,
          activeDonors: donors.length,
        }))
        setAvailableDonorCount(availableCount)
      } catch (error) {
        console.error("Error refreshing donor stats:", error)
      }
    }

    const handleNewRequest = async () => {
      // Refresh request stats when new request is created
      try {
        const requests = await getRequests("Pending")
        setStats((prev) => ({
          ...prev,
          openRequests: requests.length,
        }))
      } catch (error) {
        console.error("Error refreshing request stats:", error)
      }
    }

    // Listen for custom events from Socket.IO context
    window.addEventListener("donor_status_update", handleDonorUpdate)
    window.addEventListener("new_request", handleNewRequest)

    return () => {
      window.removeEventListener("donor_status_update", handleDonorUpdate)
      window.removeEventListener("new_request", handleNewRequest)
    }
  }, [])

  // Fetch AI recommendation on mount and auto-refresh every 5 minutes
  useEffect(() => {
    const fetchRecommendation = async () => {
      try {
        setIsLoadingRecommendation(true)
        const recommendations = await getAIRecommendation()
        
        if (recommendations && recommendations.length > 0) {
          // Use the top recommendation (first one)
          setAiRecommendation(recommendations[0])
        } else {
          // Fallback if no recommendations
          setAiRecommendation((prev) => prev || null)
        }
      } catch (error) {
        console.error("Error fetching AI recommendation:", error)
        // Keep previous recommendation if available, otherwise set to null
        setAiRecommendation((prev) => prev || null)
      } finally {
        setIsLoadingRecommendation(false)
      }
    }

    // Fetch immediately on mount
    fetchRecommendation()

    // Auto-refresh every 5 minutes (300000ms)
    const refreshInterval = setInterval(() => {
      fetchRecommendation()
    }, 5 * 60 * 1000)

    return () => {
      clearInterval(refreshInterval)
    }
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
                  value={stats.activeDonors}
                  icon={<HeartPulse className="h-5 w-5 text-white" />}
                  progress={Math.min(100, (stats.activeDonors / 200) * 100)}
                  delay={0.1}
                />
                <StatCard
                  title="Open Requests"
                  value={stats.openRequests}
                  icon={<Hospital className="h-5 w-5 text-white" />}
                  progress={Math.min(100, (stats.openRequests / 50) * 100)}
                  delay={0.2}
                />
                <StatCard
                  title="Upcoming Camps"
                  value={stats.upcomingCamps}
                  icon={<Users className="h-5 w-5 text-white" />}
                  progress={Math.min(100, (stats.upcomingCamps / 20) * 100)}
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
                        <p className="text-lg font-bold text-foreground">{availableDonorCount}</p>
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
            {isLoadingRecommendation ? (
              <Card className="rounded-2xl border border-border shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="flex items-start gap-4 p-6">
                  {/* Shimmer loading skeleton */}
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 shadow-sm">
                    <Bot className="h-5 w-5 text-primary animate-pulse" />
                  </div>
                  <div className="flex-1 space-y-3">
                    <div className="h-4 w-48 animate-pulse rounded-2xl bg-muted" />
                    <div className="h-5 w-32 animate-pulse rounded-2xl bg-muted" />
                    <div className="h-4 w-full animate-pulse rounded-2xl bg-muted" />
                    <div className="h-4 w-3/4 animate-pulse rounded-2xl bg-muted" />
                  </div>
                </CardContent>
              </Card>
            ) : aiRecommendation ? (
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
                    {/* AI Recommendation */}
                    <div className="flex-1">
                      <div className="mb-2">
                        <h3 className="text-sm font-semibold text-foreground">
                          AI Recommended Camp Area
                        </h3>
                      </div>
                      <div className="mb-2">
                        <p className="text-lg font-semibold text-primary">
                          {aiRecommendation.location}
                        </p>
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {aiRecommendation.reason}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ) : (
              <Card className="rounded-2xl border border-border shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="flex items-start gap-4 p-6">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 shadow-sm">
                    <Bot className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-muted-foreground">
                      No recommendation available at this time. Please try again later.
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
      </div>
    </PageTransition>
  )
}