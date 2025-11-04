import axios from "axios"

// Create Axios instance with base URL from environment variable
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor for logging (optional)
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle network errors
    if (!error.response) {
      throw new Error("Server unavailable")
    }
    throw error
  }
)

// ============ Type Definitions ============

export interface Donor {
  id: number
  name: string
  blood_group: string
  lat: number
  lng: number
  available: boolean
  last_donation_date: string | null
  created_at: string
  updated_at: string
}

export interface DonorCreate {
  name: string
  blood_group: string
  lat: number
  lng: number
  available?: boolean
  last_donation_date?: string | null
}

export interface DonorUpdate {
  name?: string
  blood_group?: string
  lat?: number
  lng?: number
  available?: boolean
  last_donation_date?: string | null
}

export interface Hospital {
  id: number
  name: string
  location: string
  created_at: string
  updated_at: string
}

export interface Request {
  id: number
  hospital_id: number
  blood_type: string
  urgency: "Low" | "Medium" | "High" | "Critical"
  status: "Pending" | "Active" | "Fulfilled" | "Cancelled"
  donor_id: number | null
  created_at: string
  updated_at: string
  hospital?: Hospital
}

export interface RequestCreate {
  hospital_id: number
  blood_type: string
  urgency?: "Low" | "Medium" | "High" | "Critical"
  status?: "Pending" | "Active" | "Fulfilled" | "Cancelled"
}

export interface RequestStatusUpdate {
  status: "Pending" | "Active" | "Fulfilled" | "Cancelled"
}

export interface ChatRequest {
  message: string
}

export interface ChatResponse {
  answer: string
}

export interface LocationRecommendation {
  location: string
  score: number
  reason: string
}

export interface LocationRecommendationsResponse {
  recommendations: LocationRecommendation[]
}

// ============ API Methods ============

/**
 * Get all donors with optional availability filter
 */
export async function getDonors(available?: boolean): Promise<Donor[]> {
  try {
    const params = available !== undefined ? { available } : {}
    const response = await api.get<Donor[]>("/donors/", { params })
    return response.data
  } catch (error) {
    throw new Error("Server unavailable")
  }
}

/**
 * Create a new donor
 */
export async function postDonor(donor: DonorCreate): Promise<Donor> {
  try {
    const response = await api.post<Donor>("/donors/", donor)
    return response.data
  } catch (error) {
    throw new Error("Server unavailable")
  }
}

/**
 * Update donor information
 */
export async function putDonor(
  donorId: number,
  donor: DonorUpdate
): Promise<Donor> {
  try {
    const response = await api.put<Donor>(`/donors/${donorId}`, donor)
    return response.data
  } catch (error) {
    throw new Error("Server unavailable")
  }
}

/**
 * Get all blood requests with optional filters
 */
export async function getRequests(
  statusFilter?: "Pending" | "Active" | "Fulfilled" | "Cancelled",
  hospitalId?: number
): Promise<Request[]> {
  try {
    const params: Record<string, string | number> = {}
    if (statusFilter) params.status_filter = statusFilter
    if (hospitalId) params.hospital_id = hospitalId
    const response = await api.get<Request[]>("/requests/", { params })
    return response.data
  } catch (error) {
    throw new Error("Server unavailable")
  }
}

/**
 * Create a new blood request
 */
export async function postRequest(request: RequestCreate): Promise<Request> {
  try {
    const response = await api.post<Request>("/requests/", request)
    return response.data
  } catch (error) {
    throw new Error("Server unavailable")
  }
}

/**
 * Update request status
 */
export async function putRequestStatus(
  requestId: number,
  statusUpdate: RequestStatusUpdate
): Promise<Request> {
  try {
    const response = await api.put<Request>(
      `/requests/${requestId}/status`,
      statusUpdate
    )
    return response.data
  } catch (error) {
    throw new Error("Server unavailable")
  }
}

/**
 * Chat with AI assistant
 * @param message - User message to send to AI
 * @returns Promise<string> - AI response answer
 * @throws Error with message "Server unavailable" if request fails
 */
export async function getAIChat(message: string): Promise<string> {
  try {
    const response = await api.post<ChatResponse>("/ai/chat", {
      message,
    })
    
    // Check if response has answer field
    if (response.data && response.data.answer) {
      return response.data.answer
    }
    
    // Fallback if response structure is unexpected
    throw new Error("Invalid response format")
  } catch (error: any) {
    // Check if it's a network error or server error
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      if (status === 500 || status === 503) {
        throw new Error("Server unavailable")
      }
      // For other errors, also throw server unavailable for graceful fallback
      throw new Error("Server unavailable")
    } else if (error.request) {
      // Request was made but no response received (network error)
      throw new Error("Server unavailable")
    } else {
      // Something else happened
      throw new Error("Server unavailable")
    }
  }
}

/**
 * Get AI location recommendations for blood camps
 */
export async function getAIRecommendation(): Promise<LocationRecommendation[]> {
  try {
    const response = await api.get<LocationRecommendationsResponse>(
      "/ai/recommend-location"
    )
    return response.data.recommendations
  } catch (error) {
    throw new Error("Server unavailable")
  }
}

// Export the axios instance for direct use if needed
export default api

