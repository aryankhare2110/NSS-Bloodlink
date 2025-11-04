import { useEffect, useState } from "react"
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet"
import { Icon } from "leaflet"
import "leaflet/dist/leaflet.css"

// Fix for default marker icons in react-leaflet
import L from "leaflet"
import icon from "leaflet/dist/images/marker-icon.png"
import iconShadow from "leaflet/dist/images/marker-shadow.png"
import { getDonors, type Donor } from "@/services/api"

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

L.Marker.prototype.options.icon = DefaultIcon

// Custom red marker icon for donors
const createDonorIcon = () => {
  return new Icon({
    iconUrl: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(`
      <svg width="32" height="40" viewBox="0 0 32 40" xmlns="http://www.w3.org/2000/svg">
        <path fill="#e11d48" d="M16 0C7.163 0 0 7.163 0 16c0 10.5 16 24 16 24s16-13.5 16-24C32 7.163 24.837 0 16 0z"/>
        <circle cx="16" cy="16" r="6" fill="white"/>
      </svg>
    `),
    iconSize: [32, 40],
    iconAnchor: [16, 40],
    popupAnchor: [0, -40],
  })
}

export function DonorMap() {
  const [donors, setDonors] = useState<Donor[]>([])
  const [center, setCenter] = useState<[number, number]>([28.545, 77.273])

  useEffect(() => {
    const fetchDonors = async () => {
      try {
        const donorList = await getDonors(true) // Only available donors
        setDonors(donorList)
        
        // Calculate center from donors if available
        if (donorList.length > 0) {
          const avgLat = donorList.reduce((sum, d) => sum + d.lat, 0) / donorList.length
          const avgLng = donorList.reduce((sum, d) => sum + d.lng, 0) / donorList.length
          setCenter([avgLat, avgLng])
        }
      } catch (error) {
        console.error("Error fetching donors for map:", error)
        // Keep default center if fetch fails
      }
    }

    fetchDonors()
  }, [])

  return (
    <div className="h-full w-full rounded-2xl overflow-hidden">
      <MapContainer
        center={center}
        zoom={13}
        style={{ height: "100%", width: "100%", zIndex: 0 }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {donors.map((donor) => (
          <Marker
            key={donor.id}
            position={[donor.lat, donor.lng] as [number, number]}
            icon={createDonorIcon()}
          >
            <Popup>
              <div className="text-center">
                <p className="font-semibold text-foreground">{donor.name}</p>
                <p className="text-sm text-muted-foreground">{donor.blood_group}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {donor.available ? "Available" : "Unavailable"}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}