import { z } from "zod"
import { env } from "next-runtime-env"

const schema = z.object({
  NODE_ENV: z.literal("production").or(z.literal("development")).default("production"),
  NEXT_PUBLIC_API_URL: z.string().url().default("http://localhost:4000/"),
  NEXT_PUBLIC_WS_URL: z.string().url().default("ws://localhost:4000/"),
  NEXT_PUBLIC_OIDC_PROVIDER: z.string().url().default("http://keycloak"),
  NEXT_PUBLIC_CLIENT_ID: z.string().default("scystream-frontend"),
  NEXT_PUBLIC_REDIRECT_URI: z.string().url().default("http://localhost:3000"),
  NEXT_PUBLIC_POST_LOGOUT_REDIRECT_URI: z.string().url().default("http://localhost:3000")
})

const parsed = schema.safeParse({
  NODE_ENV: process.env.NODE_ENV,
  NEXT_PUBLIC_API_URL: env("NEXT_PUBLIC_API_URL"),
  NEXT_PUBLIC_WS_URL: env("NEXT_PUBLIC_WS_URL"),
  NEXT_PUBLIC_OIDC_PROVIDER: env("NEXT_PUBLIC_OIDC_PROVIDER"),
  NEXT_PUBLIC_CLIENT_ID: env("NEXT_PUBLIC_CLIENT_ID"),
  NEXT_PUBLIC_REDIRECT_URI: env("NEXT_PUBLIC_REDIRECT_URI"),
  NEXT_PUBLIC_POST_LOGOUT_REDIRECT_URI: env("NEXT_PUBLIC_POST_LOGOUT_REDIRECT_URI"),
})

if (!parsed.success) {
  throw new Error(`Invalid environment variables:\n${parsed.error}`)
}

const data = parsed.data

export const NODE_ENV = data.NODE_ENV
export const API_URL = data.NEXT_PUBLIC_API_URL
export const WS_URL = data.NEXT_PUBLIC_WS_URL
export const OIDC_PROVIDER = data.NEXT_PUBLIC_OIDC_PROVIDER
export const CLIENT_ID = data.NEXT_PUBLIC_CLIENT_ID
export const REDIRECT_URI = data.NEXT_PUBLIC_REDIRECT_URI
export const POST_LOGOUT_REDIRECT_URI = data.NEXT_PUBLIC_POST_LOGOUT_REDIRECT_URI

export const CONFIG = {
  NODE_ENV,
  API_URL,
  WS_URL,
  OIDC_PROVIDER,
  CLIENT_ID,
  REDIRECT_URI,
  POST_LOGOUT_REDIRECT_URI
}
