"use client"

import { QueryClientProvider, QueryClient } from "@tanstack/react-query"
import { useState, type ReactNode } from "react"

export default function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}
