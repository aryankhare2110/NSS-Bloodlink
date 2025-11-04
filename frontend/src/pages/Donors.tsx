import { useState, useEffect } from "react"
import { Search } from "lucide-react"
import { motion } from "framer-motion"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { PageTransition } from "@/components/PageTransition"
import { TableSkeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/toast"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { getDonors, type Donor as APIDonor } from "@/services/api"

interface Donor {
  id: number
  name: string
  bloodGroup: string
  availability: "Available" | "Unavailable"
  lastDonationDate: string | null
  location: string
}

export default function Donors() {
  const { addToast } = useToast()
  const [searchQuery, setSearchQuery] = useState("")
  const [bloodGroupFilter, setBloodGroupFilter] = useState("all")
  const [availabilityFilter, setAvailabilityFilter] = useState(true)
  const [isLoading, setIsLoading] = useState(true)
  const [donors, setDonors] = useState<Donor[]>([])
  const [allDonors, setAllDonors] = useState<Donor[]>([])

  useEffect(() => {
    const fetchDonors = async () => {
      try {
        setIsLoading(true)
        const apiDonors = await getDonors()
        
        // Transform API donors to component format
        const transformedDonors: Donor[] = apiDonors.map((donor: APIDonor) => ({
          id: donor.id,
          name: donor.name,
          bloodGroup: donor.blood_group,
          availability: donor.available ? "Available" : "Unavailable",
          lastDonationDate: donor.last_donation_date,
          location: `Lat: ${donor.lat.toFixed(3)}, Lng: ${donor.lng.toFixed(3)}`, // Use coordinates as location for now
        }))
        
        setAllDonors(transformedDonors)
        setDonors(transformedDonors)
      } catch (error) {
        console.error("Error fetching donors:", error)
        addToast("Server unavailable", "error")
      } finally {
        setIsLoading(false)
      }
    }

    fetchDonors()
  }, [addToast])

  // Listen for real-time donor status updates via Socket.IO
  useEffect(() => {
    const handleDonorUpdate = (event: CustomEvent) => {
      const donorData = event.detail as {
        id: number
        name: string
        blood_group: string
        available: boolean
        last_donation_date?: string | null
      }

      // Update the donor in the list
      setDonors((prevDonors) =>
        prevDonors.map((donor) =>
          donor.id === donorData.id
            ? {
                ...donor,
                availability: donorData.available ? "Available" : "Unavailable",
                bloodGroup: donorData.blood_group,
                lastDonationDate: donorData.last_donation_date || null,
              }
            : donor
        )
      )

      // Also update allDonors
      setAllDonors((prevDonors) =>
        prevDonors.map((donor) =>
          donor.id === donorData.id
            ? {
                ...donor,
                availability: donorData.available ? "Available" : "Unavailable",
                bloodGroup: donorData.blood_group,
                lastDonationDate: donorData.last_donation_date || null,
              }
            : donor
        )
      )
    }

    // Listen for custom events from Socket.IO context
    const eventHandler = (event: Event) => {
      handleDonorUpdate(event as CustomEvent)
    }
    window.addEventListener("donor_status_update", eventHandler)

    return () => {
      window.removeEventListener("donor_status_update", eventHandler)
    }
  }, [])

  const filteredDonors = donors.filter((donor) => {
    const matchesSearch =
      donor.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      donor.location.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesBloodGroup =
      bloodGroupFilter === "all" || donor.bloodGroup === bloodGroupFilter
    const matchesAvailability =
      availabilityFilter === true
        ? donor.availability === "Available"
        : true

    return matchesSearch && matchesBloodGroup && matchesAvailability
  })

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never"
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <PageTransition>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-foreground mb-4">Donors</h1>
          <p className="text-muted-foreground">Manage donor database</p>
        </div>

          {/* Filters Bar - Floating Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="mb-8"
          >
            <Card className="shadow-md backdrop-blur-sm bg-white/95 hover:shadow-lg transition-shadow">
              <div className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center">
                {/* Search Input - Rounded Full */}
                <div className="relative flex-1">
                  <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                  <Input
                    type="text"
                    placeholder="Search by name or location..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-12 rounded-full shadow-sm border-border focus:shadow-md transition-all hover:shadow-md"
                  />
                </div>

                {/* Blood Group Dropdown */}
                <div className="flex items-center gap-2 sm:w-48">
                  <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                    Blood Group:
                  </label>
                  <Select
                    value={bloodGroupFilter}
                    onChange={(e) => {
                      setBloodGroupFilter(e.target.value)
                      addToast(`Filtered by ${e.target.value === "all" ? "all" : e.target.value}`, "info")
                    }}
                    className="w-full"
                  >
                    <option value="all">All</option>
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

                {/* Availability Toggle */}
                <div className="flex items-center gap-3">
                  <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                    Available Only:
                  </label>
                  <Switch
                    checked={availabilityFilter}
                    onCheckedChange={(checked) => {
                      setAvailabilityFilter(checked)
                      addToast(
                        checked
                          ? "Showing only available donors"
                          : "Showing all donors",
                        "info"
                      )
                    }}
                  />
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Table */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className="overflow-hidden p-0 hover:shadow-md transition-shadow">
              <div className="overflow-x-auto max-h-[600px] overflow-y-auto scroll-smooth">
                <Table>
                  <TableHeader className="sticky top-0 z-10 bg-white shadow-sm">
                    <TableRow className="border-b border-border hover:bg-transparent">
                      <TableHead className="text-foreground font-semibold bg-white sticky top-0">Name</TableHead>
                      <TableHead className="text-foreground font-semibold bg-white sticky top-0">Blood Group</TableHead>
                      <TableHead className="text-foreground font-semibold bg-white sticky top-0">Availability</TableHead>
                      <TableHead className="text-foreground font-semibold bg-white sticky top-0">Last Donation Date</TableHead>
                      <TableHead className="text-foreground font-semibold bg-white sticky top-0">Location</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {isLoading ? (
                      <TableRow>
                        <TableCell colSpan={5} className="bg-white">
                          <TableSkeleton />
                        </TableCell>
                      </TableRow>
                    ) : filteredDonors.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground py-8 bg-white">
                          No donors found matching your criteria
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredDonors.map((donor, index) => (
                        <TableRow
                          key={donor.id}
                          className={`
                            transition-all duration-200 cursor-pointer
                            ${index % 2 === 0 ? 'bg-white' : 'bg-[#fafafa]'}
                            hover:bg-white hover:-translate-y-1 hover:shadow-sm
                          `}
                        >
                          <TableCell className="font-medium text-foreground">{donor.name}</TableCell>
                          <TableCell>
                            <Badge variant="default">{donor.bloodGroup}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={donor.availability === "Available" ? "available" : "unavailable"}
                              className="rounded-full"
                            >
                              {donor.availability}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {formatDate(donor.lastDonationDate)}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {donor.location}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </Card>
          </motion.div>

            {/* Results Count */}
            <div className="mt-6 text-sm text-muted-foreground">
              Showing {filteredDonors.length} of {allDonors.length} donors
            </div>
      </div>
    </PageTransition>
  )
}