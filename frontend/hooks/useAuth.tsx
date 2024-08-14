"use client"

import { useState, useEffect } from "react"
import { z } from "zod"
import { useRouter } from "next/navigation"
import { getConfig } from "@/utils/config"
import { useRefreshMutation } from "@/mutations/userMutation"

const TokenPayloadSchema = z.object({
  uuid: z.string().uuid(),
  email: z.string().email(),
  iat: z.number(),
  exp: z.number()
}).transform((obj) => ({
  uuid: obj.uuid,
  email: obj.email,
  iat: obj.iat,
  exp: obj.exp
}))

type tokenSchema = z.output<typeof TokenPayloadSchema>

export type User = {
  uuid: string,
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
  const [loading, setLoading] = useState<boolean>(true)
  const { mutateAsync } = useRefreshMutation()
  const config = getConfig()
  const router = useRouter()

  function signOut() {
    localStorage.removeItem(config.accessTokenKey)
    localStorage.removeItem(config.refreshTokenKey)
    window.location.reload()
  }

  useEffect(() => {
    // TODO: refreshToken
    async function checkToken() {
      try {
        const token = localStorage.getItem(config.accessTokenKey)
        const refreshToken = localStorage.getItem(config.refreshTokenKey)

        if (!token) throw new Error("No token set.")

        const tokenPayload = tokenToPayload(token)
        if (!tokenPayload) throw new Error("Payload not set.")

        if (isJWTExpired(tokenPayload.exp)) {
          if (!refreshToken) throw new Error("No refresh token availible.")

          const res = await mutateAsync({ refresh_token: refreshToken, access_token: token })
          if (!res) throw new Error("Refreshing token failed.")
        }

        setUser({
          uuid: tokenPayload.uuid,
          email: tokenPayload.email
        })
        setLoading(false)
      } catch (_) {
        setUser(undefined)
        localStorage.removeItem(config.accessTokenKey)
        localStorage.removeItem(config.refreshTokenKey)
        router.push("/login")
      }
    }
    checkToken()
  }, [config.accessTokenKey, router, mutateAsync, config.refreshTokenKey])

  return { user, loading, signOut }
}
