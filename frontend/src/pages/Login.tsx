import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Mail, Lock, LogIn } from "lucide-react"
import { motion } from "framer-motion"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/components/ui/toast"
import { useAuth } from "@/context/authContext"
import { PageTransition } from "@/components/PageTransition"

export default function Login() {
  const { addToast } = useToast()
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email.trim() || !password.trim()) {
      addToast("Please fill in all fields", "error")
      return
    }

    setIsLoading(true)
    try {
      await login(email, password)
      addToast("Logged in successfully!", "success")
      navigate("/")
    } catch (error: any) {
      console.error("Login error:", error)
      
      // Provide helpful error messages
      let errorMessage = error.message || "Failed to login. Please check your credentials."
      
      if (error.code === "auth/api-key-not-valid") {
        errorMessage = "Firebase API key is invalid. Please check your .env file and ensure you have valid Firebase credentials. See FIREBASE_SETUP.md for setup instructions."
      } else if (error.code === "auth/user-not-found") {
        errorMessage = "No account found with this email. Please sign up first."
      } else if (error.code === "auth/wrong-password") {
        errorMessage = "Incorrect password. Please try again."
      } else if (error.code === "auth/invalid-email") {
        errorMessage = "Invalid email address. Please check your email format."
      }
      
      addToast(errorMessage, "error")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <PageTransition>
      <div className="flex min-h-screen items-center justify-center bg-background p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          <Card className="rounded-2xl border border-border shadow-md hover:shadow-lg transition-shadow">
            <CardHeader className="space-y-1">
              <div className="flex items-center justify-center mb-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 shadow-sm">
                  <LogIn className="h-8 w-8 text-primary" />
                </div>
              </div>
              <CardTitle className="text-2xl font-semibold text-center">Welcome Back</CardTitle>
              <CardDescription className="text-center">
                Sign in to your NSS BloodLink account
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium text-foreground">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="Enter your email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-12 rounded-2xl shadow-sm focus:shadow-md transition-all"
                      disabled={isLoading}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label htmlFor="password" className="text-sm font-medium text-foreground">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                    <Input
                      id="password"
                      type="password"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-12 rounded-2xl shadow-sm focus:shadow-md transition-all"
                      disabled={isLoading}
                      required
                    />
                  </div>
                </div>
                <Button
                  type="submit"
                  className="w-full rounded-2xl shadow-sm hover:shadow-md transition-all"
                  disabled={isLoading}
                >
                  {isLoading ? "Signing in..." : "Sign In"}
                </Button>
              </form>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4">
              <div className="text-sm text-center text-muted-foreground">
                Don't have an account?{" "}
                <Link
                  to="/signup"
                  className="text-primary hover:underline font-medium transition-all"
                >
                  Sign up
                </Link>
              </div>
            </CardFooter>
          </Card>
        </motion.div>
      </div>
    </PageTransition>
  )
}

