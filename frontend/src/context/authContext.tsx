import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  type User,
} from "firebase/auth"
import { auth } from "@/firebase"

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, name: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!auth) {
      setLoading(false)
      return
    }

    // Listen for auth state changes
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser)
      setLoading(false)

      // Store JWT token in localStorage
      if (firebaseUser) {
        firebaseUser.getIdToken().then((token) => {
          localStorage.setItem("auth_token", token)
          localStorage.setItem("user_email", firebaseUser.email || "")
          localStorage.setItem("user_name", firebaseUser.displayName || "")
          localStorage.setItem("user_uid", firebaseUser.uid)
        })
      } else {
        localStorage.removeItem("auth_token")
        localStorage.removeItem("user_email")
        localStorage.removeItem("user_name")
        localStorage.removeItem("user_uid")
      }
    })

    return () => unsubscribe()
  }, [])

  const login = async (email: string, password: string) => {
    if (!auth) {
      throw new Error("Firebase Auth not initialized")
    }

    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password)
      const token = await userCredential.user.getIdToken()
      localStorage.setItem("auth_token", token)
      localStorage.setItem("user_email", userCredential.user.email || "")
      localStorage.setItem("user_name", userCredential.user.displayName || "")
      localStorage.setItem("user_uid", userCredential.user.uid)
    } catch (error: any) {
      console.error("Login error:", error)
      throw new Error(error.message || "Failed to login")
    }
  }

  const signup = async (email: string, password: string, name: string) => {
    if (!auth) {
      throw new Error("Firebase Auth not initialized")
    }

    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password)
      
      // Update user profile with display name
      if (userCredential.user) {
        // Note: updateProfile requires additional Firebase imports
        // For now, we'll store the name in localStorage
        const token = await userCredential.user.getIdToken()
        localStorage.setItem("auth_token", token)
        localStorage.setItem("user_email", userCredential.user.email || "")
        localStorage.setItem("user_name", name)
        localStorage.setItem("user_uid", userCredential.user.uid)
      }
    } catch (error: any) {
      console.error("Signup error:", error)
      throw new Error(error.message || "Failed to sign up")
    }
  }

  const logout = async () => {
    if (!auth) {
      throw new Error("Firebase Auth not initialized")
    }

    try {
      await signOut(auth)
      localStorage.removeItem("auth_token")
      localStorage.removeItem("user_email")
      localStorage.removeItem("user_name")
      localStorage.removeItem("user_uid")
    } catch (error: any) {
      console.error("Logout error:", error)
      throw new Error(error.message || "Failed to logout")
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}

