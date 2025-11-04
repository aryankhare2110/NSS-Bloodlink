import * as React from "react"
import { X, CheckCircle2, AlertCircle, Info } from "lucide-react"
import { cn } from "@/lib/utils"

export type ToastType = "success" | "error" | "info"

interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (message: string, type?: ToastType) => void
  removeToast: (id: string) => void
}

const ToastContext = React.createContext<ToastContextValue | undefined>(
  undefined
)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([])

  const addToast = React.useCallback(
    (message: string, type: ToastType = "info") => {
      const id = Math.random().toString(36).substring(7)
      setToasts((prev) => [...prev, { id, message, type }])
      setTimeout(() => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id))
      }, 3000)
    },
    []
  )

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = React.useContext(ToastContext)
  if (!context) {
    throw new Error("useToast must be used within ToastProvider")
  }
  return context
}

function ToastContainer({
  toasts,
  removeToast,
}: {
  toasts: Toast[]
  removeToast: (id: string) => void
}) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "flex items-center gap-3 rounded-2xl border border-border glass p-4 shadow-lg backdrop-blur-lg backdrop-brightness-95 transition-all duration-200 animate-fade-in hover:shadow-xl",
            toast.type === "success" && "border-green-200/50",
            toast.type === "error" && "border-red-200/50",
            toast.type === "info" && "border-secondary/50"
          )}
        >
          {toast.type === "success" && (
            <CheckCircle2 className="h-5 w-5 text-green-600" />
          )}
          {toast.type === "error" && (
            <AlertCircle className="h-5 w-5 text-red-600" />
          )}
          {toast.type === "info" && (
            <Info className="h-5 w-5 text-secondary" />
          )}
          <p className="flex-1 text-sm font-medium text-foreground">
            {toast.message}
          </p>
          <button
            onClick={() => removeToast(toast.id)}
            className="rounded-2xl p-1 text-muted-foreground transition-all hover:bg-muted hover:text-foreground hover:shadow-sm"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  )
}