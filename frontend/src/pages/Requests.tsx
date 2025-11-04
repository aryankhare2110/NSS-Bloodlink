import { useState } from "react"
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

interface Request {
  id: number
  hospitalName: string
  bloodGroup: string
  urgency: "Low" | "Medium" | "High" | "Critical"
  distance: string
  location: string
}

const dummyRequests: Request[] = [
  {
    id: 1,
    hospitalName: "Apollo Hospital",
    bloodGroup: "O+",
    urgency: "Critical",
    distance: "2.5 km",
    location: "Delhi",
  },
  {
    id: 2,
    hospitalName: "AIIMS",
    bloodGroup: "A+",
    urgency: "High",
    distance: "5.1 km",
    location: "Delhi",
  },
  {
    id: 3,
    hospitalName: "Max Hospital",
    bloodGroup: "B+",
    urgency: "Medium",
    distance: "8.3 km",
    location: "Delhi",
  },
  {
    id: 4,
    hospitalName: "Fortis Hospital",
    bloodGroup: "AB-",
    urgency: "High",
    distance: "12.7 km",
    location: "Delhi",
  },
  {
    id: 5,
    hospitalName: "Safdarjung Hospital",
    bloodGroup: "O-",
    urgency: "Critical",
    distance: "3.2 km",
    location: "Delhi",
  },
  {
    id: 6,
    hospitalName: "BLK Hospital",
    bloodGroup: "B-",
    urgency: "Low",
    distance: "9.5 km",
    location: "Delhi",
  },
]

const getUrgencyBadge = (urgency: string) => {
  if (urgency === "High" || urgency === "Critical") {
    return <Badge className="bg-yellow-500 text-white">High Priority</Badge>
  }
  return <Badge className="bg-gray-400 text-white">Normal</Badge>
}

export default function Requests() {
  const { addToast } = useToast()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [formData, setFormData] = useState({
    hospitalName: "",
    bloodGroup: "",
    urgency: "",
    location: "",
  })

  const handleNotifyDonors = () => {
    addToast("Alert sent to matching donors.", "success")
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    addToast("Request created successfully!", "success")
    setIsDialogOpen(false)
    setFormData({
      hospitalName: "",
      bloodGroup: "",
      urgency: "",
      location: "",
    })
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
          <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-2">
            {dummyRequests.map((request, index) => (
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
                          {request.location} • {request.distance}
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
                    Hospital Name
                  </label>
                  <Input
                    required
                    value={formData.hospitalName}
                    onChange={(e) =>
                      setFormData({ ...formData, hospitalName: e.target.value })
                    }
                    placeholder="Enter hospital name"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Blood Group
                  </label>
                  <Select
                    required
                    value={formData.bloodGroup}
                    onChange={(e) =>
                      setFormData({ ...formData, bloodGroup: e.target.value })
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
                    <option value="">Select urgency level</option>
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Critical">Critical</option>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Location
                  </label>
                  <Input
                    required
                    value={formData.location}
                    onChange={(e) =>
                      setFormData({ ...formData, location: e.target.value })
                    }
                    placeholder="Enter location"
                  />
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