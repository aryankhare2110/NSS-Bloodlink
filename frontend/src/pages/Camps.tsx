import { useState } from "react"
import { Calendar, MapPin, Users, Sparkles, Loader2 } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useToast } from "@/components/ui/toast"
import { PageTransition } from "@/components/PageTransition"

interface ScheduledCamp {
  id: number
  name: string
  location: string
  date: string
  volunteers: number
}

const dummyCamps: ScheduledCamp[] = [
  {
    id: 1,
    name: "Community Blood Drive - Jan 2024",
    location: "Connaught Place, Delhi",
    date: "2024-01-25",
    volunteers: 12,
  },
  {
    id: 2,
    name: "NSS Blood Donation Camp",
    location: "Dwarka Sector 14, Delhi",
    date: "2024-02-10",
    volunteers: 8,
  },
  {
    id: 3,
    name: "Corporate Blood Donation Drive",
    location: "Gurgaon Sector 15",
    date: "2024-02-28",
    volunteers: 15,
  },
  {
    id: 4,
    name: "University Blood Camp",
    location: "Delhi University North Campus",
    date: "2024-03-15",
    volunteers: 10,
  },
]

interface AIRecommendation {
  area: string
  reason: string
}

export default function Camps() {
  const { addToast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [aiRecommendation, setAiRecommendation] = useState<AIRecommendation | null>({
    area: "South Delhi",
    reason: "High Donor Density",
  })

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  const handleAskAI = async () => {
    setIsLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500))
      
      const mockRecommendations = [
        { area: "South Delhi", reason: "High Donor Density" },
        { area: "Dwarka", reason: "Growing Population & High Engagement" },
        { area: "Rohini", reason: "Excellent Volunteer Network" },
        { area: "Noida Sector 62", reason: "Corporate Hub with Active Donors" },
      ]
      
      const randomRecommendation =
        mockRecommendations[
          Math.floor(Math.random() * mockRecommendations.length)
        ]
      
      setAiRecommendation(randomRecommendation)
      addToast("AI recommendation generated successfully!", "success")
    } catch (error) {
      addToast("Failed to get AI recommendation. Please try again.", "error")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <PageTransition>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-foreground mb-4">Camps</h1>
          <p className="text-muted-foreground">
            Manage blood donation camps and get AI-powered location recommendations
          </p>
        </div>

          {/* Scheduled Camps Section - Horizontal Cards */}
          <div className="mb-12">
            <h2 className="text-lg font-medium text-gray-700 mb-6">
              Scheduled Camps
            </h2>
            <div className="space-y-4">
              {dummyCamps.map((camp, index) => (
                <motion.div
                  key={camp.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: index * 0.1 }}
                >
                  <Card className="relative overflow-hidden border-l-4 border-l-primary bg-white shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-4 p-6">
                      {/* Camp Name */}
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-foreground mb-3 sm:mb-0">
                          {camp.name}
                        </h3>
                      </div>
                      
                      {/* Icons and Details */}
                      <div className="flex flex-wrap items-center gap-4 sm:gap-6">
                        <div className="flex items-center gap-2">
                          <MapPin className="h-5 w-5 text-primary" />
                          <span className="text-sm text-foreground">
                            {camp.location}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-5 w-5 text-primary" />
                          <span className="text-sm text-foreground">
                            {formatDate(camp.date)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Users className="h-5 w-5 text-primary" />
                          <span className="text-sm text-foreground">
                            {camp.volunteers} volunteers
                          </span>
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>

          {/* AI Recommendation Section */}
          <div>
            <h2 className="text-lg font-medium text-gray-700 mb-6 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              AI Recommendation
            </h2>

            {/* AI Recommendation Card - Larger with Gradient */}
            <AnimatePresence mode="wait">
              {aiRecommendation && (
                <motion.div
                  key={aiRecommendation.area}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  className="mb-6"
                >
                  <Card className="bg-gradient-to-br from-white to-[#fdf2f2] border border-border shadow-sm hover:shadow-md transition-shadow">
                    <CardHeader>
                      <div className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-primary" />
                        <CardTitle>Best Area to Host Next Camp</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                        className="space-y-2"
                      >
                        <p className="text-2xl font-semibold text-foreground">
                          {aiRecommendation.area}
                        </p>
                        <p className="text-muted-foreground">
                          {aiRecommendation.reason}
                        </p>
                      </motion.div>
                    </CardContent>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Ask AI Button - With Shimmer Animation */}
            <Button
              onClick={handleAskAI}
              disabled={isLoading}
              className="w-full sm:w-auto relative overflow-hidden hover:shadow-lg"
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <span className="relative z-10 flex items-center">
                    <Sparkles className="mr-2 h-5 w-5" />
                    Ask AI for New Suggestion
                  </span>
                  {/* Shimmer Effect */}
                  <span className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                </>
              )}
            </Button>
        </div>
      </div>
    </PageTransition>
  )
}