"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { z } from "zod"
import { getConfig } from "@/utils/config"

const User = z.object({
  email: z.string().email(),
}).transform((obj) => ({
  email: obj.email,
}))

export type User = z.output<typeof User>

type AuthContextValue = {
  user: User | undefined,
  signOut: () => void
}

const AuthContext = createContext<AuthContextValue>({
  user: undefined,
  signOut: () => { }
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | undefined>(undefined)
  const config = getConfig()

  function signOut() {
    localStorage.removeItem(config.accessTokenKey)
    localStorage.removeItem(config.refreshTokenKey)
    window.location.reload()
  }

  useEffect(() => {
    // TODO: set auth state
    setUser(undefined)
  }, [])

  return (
    <AuthContext.Provider value={{ user, signOut }} >
      {children}
    </ AuthContext.Provider >
  )
}

export function useAuth() { return useContext(AuthContext) }
