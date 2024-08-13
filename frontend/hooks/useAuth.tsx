"use client"

import { useState, useEffect } from "react"
import { z } from "zod"
import { useRouter } from "next/navigation"
import { getConfig } from "@/utils/config"

const TokenPayloadSchema = z.object({
  email: z.string().email(),
  iat: z.number(),
  exp: z.number()
}).transform((obj) => ({
  email: obj.email,
  iat: obj.iat,
  exp: obj.exp
}))

type tokenSchema = z.output<typeof TokenPayloadSchema>

export type User = {
  email: string
}

function parseJWTPayload(token: string): JSON {
  const payloadBase64 = token.split(".")[1] as string
  const decodedPayload = Buffer.from(payloadBase64, "base64").toString()
  return JSON.parse(decodedPayload)
}

function tokenToPayload(token: string): tokenSchema | null {
  const decoded = parseJWTPayload(token)
  const parsed = TokenPayloadSchema.safeParse(decoded)

  return parsed.success ? parsed.data : null
}

function isJWTExpired(exp: number): boolean {
  return (Date.now() / 1000 >= exp)
}

/*
  This hook handles the authentication,
  it will validate the token, wherever it is used.
  It supplies the signOut utility.
*/
export default function useAuth() {
  const [user, setUser] = useState<User | undefined>(undefined)
  const config = getConfig()
  const router = useRouter()

  function signOut() {
    localStorage.removeItem(config.accessTokenKey)
    localStorage.removeItem(config.refreshTokenKey)
    window.location.reload()
  }

  useEffect(() => {
    // TODO: refreshToken
    try {
      const token = localStorage.getItem(config.accessTokenKey)

      if (!token) throw new Error("No token set.")

      const tokenPayload = tokenToPayload(token)
      if (!tokenPayload) throw new Error("Payload not set.")

      if (isJWTExpired(tokenPayload.exp)) throw new Error("Token expired.")

      setUser({
        email: tokenPayload.email
      })
    } catch (_) {
      setUser(undefined)
      localStorage.removeItem(config.accessTokenKey)
      router.push("/login")
    }
  }, [config.accessTokenKey, router])

  return { user, signOut }
}
