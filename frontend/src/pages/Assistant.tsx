import { useState, useRef, useEffect } from "react"
import { Send, Bot, Heart } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { PageTransition } from "@/components/PageTransition"
import { Card } from "@/components/ui/card"

interface Message {
  id: string
  text: string
  sender: "user" | "ai"
  timestamp: Date
  isTyping?: boolean
}

// Typing animation component
function TypingMessage({ text }: { text: string }) {
  const [displayedText, setDisplayedText] = useState("")
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText((prev) => prev + text[currentIndex])
        setCurrentIndex((prev) => prev + 1)
      }, 30) // 30ms per character for smooth typing

      return () => clearTimeout(timer)
    }
  }, [currentIndex, text])

  return <span>{displayedText}</span>
}

export default function Assistant() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)
    setIsTyping(true)

    try {
      await new Promise((resolve) => setTimeout(resolve, 1500))

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: "Sure, finding O+ donors near Saket Hospital. I found 3 available donors within 5km radius. Would you like me to notify them?",
        sender: "ai",
        timestamp: new Date(),
        isTyping: true,
      }

      setMessages((prev) => [...prev, aiResponse])
      
      // Wait for typing animation to complete
      setTimeout(() => {
        setIsTyping(false)
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiResponse.id ? { ...msg, isTyping: false } : msg
          )
        )
      }, aiResponse.text.length * 30)
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I encountered an error. Please try again.",
        sender: "ai",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
      setIsTyping(false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const isEmpty = messages.length === 0

  return (
    <PageTransition>
      <div className="flex h-[calc(100vh-4rem)] flex-col bg-background">
        <div className="mx-auto w-full max-w-4xl">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-foreground mb-4">AI Assistant</h1>
            <p className="text-muted-foreground">
              Get help with blood donation queries and donor matching
            </p>
          </div>

          {/* Chat Window - Glassmorphism */}
          <Card className="flex h-[calc(100vh-20rem)] flex-col overflow-hidden bg-white/70 backdrop-blur-lg border border-white/20 shadow-lg">
            {/* Messages Container */}
            <div className="flex-1 overflow-y-auto p-6">
              <AnimatePresence>
                {isEmpty ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3 }}
                    className="flex h-full items-center justify-center"
                  >
                    <Card className="bg-white/80 backdrop-blur-sm border border-white/30 shadow-md hover:shadow-lg transition-shadow p-8 text-center max-w-md rounded-2xl">
                      <div className="flex flex-col items-center gap-4">
                        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 shadow-sm hover:shadow-md transition-shadow">
                          <Bot className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-foreground mb-2">
                            Welcome to AI Assistant
                          </h3>
                          <p className="text-muted-foreground">
                            Ask me anything about donors, camps, or emergencies{" "}
                            <Heart className="inline h-5 w-5 text-primary" />
                          </p>
                        </div>
                      </div>
                    </Card>
                  </motion.div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((message, index) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.05 }}
                        className={`flex ${
                          message.sender === "user" ? "justify-end" : "justify-start"
                        }`}
                      >
                        <div
                          className={`flex max-w-[80%] items-start gap-3 ${
                            message.sender === "user" ? "flex-row-reverse" : "flex-row"
                          }`}
                        >
                          {/* AI Avatar - Only for AI messages */}
                          {message.sender === "ai" && (
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 shadow-sm hover:shadow-md transition-shadow">
                              <Bot className="h-5 w-5 text-primary" />
                            </div>
                          )}

                          {/* Message Bubble */}
                          <div
                            className={`rounded-2xl px-4 py-3 transition-shadow ${
                              message.sender === "user"
                                ? "bg-primary text-white shadow-md hover:shadow-lg"
                                : "bg-white/90 text-foreground border border-gray-200 shadow-sm hover:shadow-md"
                            }`}
                          >
                            {message.isTyping && message.sender === "ai" ? (
                              <p className="text-sm leading-relaxed">
                                <TypingMessage text={message.text} />
                                <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse" />
                              </p>
                            ) : (
                              <p className="text-sm leading-relaxed">{message.text}</p>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))}

                    {/* Loading Indicator */}
                    {isLoading && !isTyping && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex justify-start"
                      >
                    <div className="flex items-start gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 shadow-sm">
                        <Bot className="h-5 w-5 text-primary" />
                      </div>
                          <div className="rounded-2xl bg-white/90 border border-gray-200 px-4 py-3 shadow-sm">
                            <div className="flex gap-1">
                              <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]"></div>
                              <div className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]"></div>
                              <div className="h-2 w-2 animate-bounce rounded-full bg-primary"></div>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>
                )}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <div className="border-t border-white/20 bg-white/50 backdrop-blur-sm p-4">
              <div className="flex gap-2">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your request…"
                  disabled={isLoading}
                  className="flex-1 rounded-full shadow-sm border-border bg-white/90 focus:shadow-md focus:bg-white transition-all"
                />
                <Button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isLoading}
                  size="icon"
                  className="rounded-2xl shadow-sm hover:shadow-md"
                >
                  <Send className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </PageTransition>
  )
}