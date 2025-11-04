import { useState, useEffect } from "react"
import { Plus, Bell, MapPin } from "lucide-react"
import { motion } from "framer-motion"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { useToast } from "@/components/ui/toast"
import { PageTransition } from "@/components/PageTransition"
import { Badge } from "@/components/ui/badge"
import { getRequests, postRequest, type Request as APIRequest } from "@/services/api"

interface Request {
  id: number
  hospitalName: string
  bloodGroup: string
  urgency: "Low" | "Medium" | "High" | "Critical"
  location: string
}

const getUrgencyBadge = (urgency: string) => {
  if (urgency === "High" || urgency === "Critical") {
    return <Badge className="bg-yellow-500 text-white">High Priority</Badge>
  }
  return <Badge className="bg-gray-400 text-white">Normal</Badge>
}

export default function Requests() {
  const { addToast } = useToast()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [requests, setRequests] = useState<Request[]>([])
  const [formData, setFormData] = useState({
    hospital_id: "",
    blood_type: "",
    urgency: "Medium",
    status: "Pending",
  })

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        setIsLoading(true)
        const apiRequests = await getRequests()
        
        // Transform API requests to component format
        const transformedRequests: Request[] = apiRequests.map((req: APIRequest) => ({
          id: req.id,
          hospitalName: req.hospital?.name || "Unknown Hospital",
          bloodGroup: req.blood_type,
          urgency: req.urgency,
          location: req.hospital?.location || "Unknown",
        }))
        
        setRequests(transformedRequests)
      } catch (error) {
        console.error("Error fetching requests:", error)
        addToast("Server unavailable", "error")
      } finally {
        setIsLoading(false)
      }
    }

    fetchRequests()
  }, [addToast])

  // Listen for real-time new requests via Socket.IO
  useEffect(() => {
    const handleNewRequest = async (event: CustomEvent) => {
      const requestData = event.detail as {
        id: number
        hospital_id: number
        hospital_name?: string
        blood_type: string
        urgency: string
        status: string
        created_at?: string
      }

      // Fetch full request details to get hospital information
      try {
        const apiRequests = await getRequests()
        const newRequest = apiRequests.find((req: APIRequest) => req.id === requestData.id)
        
        if (newRequest) {
          const transformedRequest: Request = {
            id: newRequest.id,
            hospitalName: newRequest.hospital?.name || requestData.hospital_name || "Unknown Hospital",
            bloodGroup: newRequest.blood_type,
            urgency: newRequest.urgency,
            location: newRequest.hospital?.location || "Unknown",
          }

          // Add new request to the list if it doesn't already exist
          setRequests((prevRequests) => {
            // Check if request already exists
            if (prevRequests.some((req) => req.id === transformedRequest.id)) {
              return prevRequests
            }
            // Add new request at the beginning
            return [transformedRequest, ...prevRequests]
          })
        } else {
          // If we can't fetch full details, create a basic request from the socket data
          const transformedRequest: Request = {
            id: requestData.id,
            hospitalName: requestData.hospital_name || "Unknown Hospital",
            bloodGroup: requestData.blood_type,
            urgency: requestData.urgency as "Low" | "Medium" | "High" | "Critical",
            location: "Unknown", // We don't have location in socket data
          }

          setRequests((prevRequests) => {
            // Check if request already exists
            if (prevRequests.some((req) => req.id === transformedRequest.id)) {
              return prevRequests
            }
            // Add new request at the beginning
            return [transformedRequest, ...prevRequests]
          })
        }
      } catch (error) {
        console.error("Error fetching new request details:", error)
        // Still add the request with basic info
        const transformedRequest: Request = {
          id: requestData.id,
          hospitalName: requestData.hospital_name || "Unknown Hospital",
          bloodGroup: requestData.blood_type,
          urgency: requestData.urgency as "Low" | "Medium" | "High" | "Critical",
          location: "Unknown",
        }

        setRequests((prevRequests) => {
          if (prevRequests.some((req) => req.id === transformedRequest.id)) {
            return prevRequests
          }
          return [transformedRequest, ...prevRequests]
        })
      }
    }

    // Listen for custom events from Socket.IO context
    const eventHandler = (event: Event) => {
      handleNewRequest(event as CustomEvent)
    }
    window.addEventListener("new_request", eventHandler)

    return () => {
      window.removeEventListener("new_request", eventHandler)
    }
  }, [addToast])

  const handleNotifyDonors = () => {
    addToast("Alert sent to matching donors.", "success")
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await postRequest({
        hospital_id: parseInt(formData.hospital_id),
        blood_type: formData.blood_type,
        urgency: formData.urgency as "Low" | "Medium" | "High" | "Critical",
        status: formData.status as "Pending" | "Active" | "Fulfilled" | "Cancelled",
      })
      
      addToast("Request created successfully!", "success")
      setIsDialogOpen(false)
      setFormData({
        hospital_id: "",
        blood_type: "",
        urgency: "Medium",
        status: "Pending",
      })
      
      // Refresh requests list
      const apiRequests = await getRequests()
      const transformedRequests: Request[] = apiRequests.map((req: APIRequest) => ({
        id: req.id,
        hospitalName: req.hospital?.name || "Unknown Hospital",
        bloodGroup: req.blood_type,
        urgency: req.urgency,
        location: req.hospital?.location || "Unknown",
      }))
      setRequests(transformedRequests)
    } catch (error) {
      console.error("Error creating request:", error)
      addToast("Server unavailable", "error")
    }
  }

  return (
    <PageTransition>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-foreground mb-4">Requests</h1>
          <p className="text-muted-foreground">
            Manage blood donation requests from hospitals
          </p>
        </div>

            {/* Request Cards Grid - 2 Columns Masonry */}
            {isLoading ? (
              <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-2">
                {[...Array(4)].map((_, i) => (
                  <Card key={i} className="animate-pulse">
                    <CardHeader className="h-24 bg-gray-200" />
                    <CardContent className="p-6 space-y-4">
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                      <div className="h-4 bg-gray-200 rounded w-1/2" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-2">
                {requests.map((request, index) => (
              <motion.div
                key={request.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
              >
                <Card className="overflow-hidden">
                  {/* Gradient Header */}
                  <CardHeader className="bg-gradient-to-r from-red-500 to-red-400 p-6">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg font-bold text-white">
                        {request.hospitalName}
                      </CardTitle>
                      {getUrgencyBadge(request.urgency)}
                    </div>
                  </CardHeader>
                  
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      {/* Blood Group Badge */}
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-muted-foreground">
                          Blood Group:
                        </span>
                        <Badge className="bg-red-500 text-white">
                          {request.bloodGroup}
                        </Badge>
                      </div>
                      
                        {/* Location */}
                        <div className="flex items-center gap-2">
                          <MapPin className="h-5 w-5 text-gray-400" />
                          <span className="text-sm text-gray-500">
                            {request.location}
                          </span>
                        </div>
                    </div>
                  </CardContent>
                  
                  <CardFooter className="p-6 pt-0">
                    <Button
                      onClick={handleNotifyDonors}
                      className="w-full focus:ring-2 focus:ring-red-500 focus:ring-offset-2 hover:animate-pulse hover:shadow-lg transition-all"
                    >
                      <Bell className="mr-2 h-5 w-5" />
                      Notify Donors
                    </Button>
                  </CardFooter>
                  </Card>
                </motion.div>
              ))}
              </div>
            )}

          {/* Floating Action Button - Circular Red */}
          <motion.button
            onClick={() => setIsDialogOpen(true)}
            className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg transition-all hover:scale-110 hover:shadow-xl hover:shadow-primary/50"
            aria-label="New Request"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <Plus className="h-5 w-5" />
          </motion.button>

          {/* New Request Dialog - Glassy Backdrop with Scale Animation */}
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>New Blood Request</DialogTitle>
                <DialogDescription>
                  Create a new blood donation request for a hospital.
                </DialogDescription>
              </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">
                      Hospital ID
                    </label>
                    <Input
                      required
                      type="number"
                      value={formData.hospital_id}
                      onChange={(e) =>
                        setFormData({ ...formData, hospital_id: e.target.value })
                      }
                      placeholder="Enter hospital ID (e.g., 1, 2, 3)"
                    />
                    <p className="text-xs text-muted-foreground">
                      Use existing hospital IDs from the database
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">
                      Blood Group
                    </label>
                    <Select
                      required
                      value={formData.blood_type}
                      onChange={(e) =>
                        setFormData({ ...formData, blood_type: e.target.value })
                      }
                    >
                      <option value="">Select blood group</option>
                      <option value="A+">A+</option>
                      <option value="A-">A-</option>
                      <option value="B+">B+</option>
                      <option value="B-">B-</option>
                      <option value="O+">O+</option>
                      <option value="O-">O-</option>
                      <option value="AB+">AB+</option>
                      <option value="AB-">AB-</option>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">
                      Urgency
                    </label>
                    <Select
                      required
                      value={formData.urgency}
                      onChange={(e) =>
                        setFormData({ ...formData, urgency: e.target.value })
                      }
                    >
                      <option value="Low">Low</option>
                      <option value="Medium">Medium</option>
                      <option value="High">High</option>
                      <option value="Critical">Critical</option>
                    </Select>
                  </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Submit Request</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
      </div>
    </PageTransition>
  )
}