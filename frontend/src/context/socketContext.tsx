import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { io, type Socket } from "socket.io-client"
import { useToast } from "@/components/ui/toast"
import { simulatePushNotification, hasNotificationPermission } from "@/firebase"

interface SocketContextType {
  socket: Socket | null
  isConnected: boolean
}

const SocketContext = createContext<SocketContextType>({
  socket: null,
  isConnected: false,
})

interface SocketProviderProps {
  children: ReactNode
}

export function SocketProvider({ children }: SocketProviderProps) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const { addToast } = useToast()

  useEffect(() => {
    // Connect to Socket.IO server
    // The backend mounts Socket.IO at /ws, so we need to connect with the path
    const socketUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
    const socketInstance = io(`${socketUrl}/ws`, {
      path: "/socket.io", // Socket.IO default path
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    })

    // Connection event
    socketInstance.on("connect", () => {
      console.log("✅ Socket.IO connected:", socketInstance.id)
      setIsConnected(true)
    })

    // Disconnection event
    socketInstance.on("disconnect", () => {
      console.log("❌ Socket.IO disconnected")
      setIsConnected(false)
    })

    // Connection error
    socketInstance.on("connect_error", (error) => {
      console.error("Socket.IO connection error:", error)
      setIsConnected(false)
    })

    // Listen for initial connection confirmation
    socketInstance.on("connected", (data: { message: string }) => {
      console.log("Socket.IO server confirmation:", data.message)
    })

    // Listen for donor status updates
    socketInstance.on("donor_status_update", (eventData: {
      type: string
      data: {
        id: number
        name: string
        blood_group: string
        available: boolean
        last_donation_date?: string | null
        lat?: number
        lng?: number
      }
      timestamp?: string
    }) => {
      console.log("📢 Received donor status update:", eventData.data)
      
      // Show toast notification
      addToast(
        `Donor ${eventData.data.name} is now ${eventData.data.available ? "available" : "unavailable"}`,
        "info"
      )

      // Emit custom event for components to listen to
      window.dispatchEvent(
        new CustomEvent("donor_status_update", {
          detail: eventData.data,
        })
      )
    })

    // Listen for new requests
    socketInstance.on("new_request", (eventData: {
      type: string
      data: {
        id: number
        hospital_id: number
        hospital_name?: string
        blood_type: string
        urgency: string
        status: string
        created_at?: string
      }
      timestamp?: string
    }) => {
      console.log("📢 Received new request:", eventData.data)
      
      const hospitalName = eventData.data.hospital_name || "Unknown Hospital"
      const bloodType = eventData.data.blood_type
      const urgency = eventData.data.urgency
      
      // Show toast notification
      addToast(
        `New ${bloodType} request from ${hospitalName}`,
        "success"
      )

      // Simulate push notification for urgent requests
      if (hasNotificationPermission() && (urgency === "High" || urgency === "Critical")) {
        const title = urgency === "Critical" ? "🚨 Critical Blood Request" : "⚠️ Urgent Blood Request"
        const body = `Urgent ${bloodType} request from ${hospitalName}`
        
        simulatePushNotification(title, body, {
          requestId: eventData.data.id,
          hospitalId: eventData.data.hospital_id,
          bloodType,
          urgency,
        })
      }

      // Emit custom event for components to listen to
      window.dispatchEvent(
        new CustomEvent("new_request", {
          detail: eventData.data,
        })
      )
    })

    setSocket(socketInstance)

    // Cleanup on unmount
    return () => {
      socketInstance.close()
      setSocket(null)
      setIsConnected(false)
    }
  }, [addToast])

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  )
}

export function useSocket() {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error("useSocket must be used within SocketProvider")
  }
  return context
}

