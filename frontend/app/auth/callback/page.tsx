"use client"

import type { NextPage } from "next"
import { Suspense, useEffect } from "react"
import { handleCallback } from "@/utils/auth/authService"
import { useSearchParams } from "next/navigation"
import { useRouter } from "next/navigation"


const AuthCallback: NextPage = () => {
  const searchParams = useSearchParams()
  const router = useRouter()

  useEffect(() => {
    const checkAuthCallback = async () => {
      if (searchParams.get("code") && searchParams.get("state")) {
        console.log("Processing OIDC callback...")
        try {
          await handleCallback()

          const redirect = searchParams.get("redirect_uri")
          const isValidRedirect = redirect && new URL(redirect).host === window.location.host
          const defaultRedirect = "/"
          if (!isValidRedirect) {
            console.warn(`Redirect URL is invalid, redirecting to default route ${defaultRedirect}`)
            router.push(defaultRedirect)
          } else {
            console.info(`Redirecting to ${redirect ?? defaultRedirect}`)
            router.push(redirect ?? defaultRedirect)
          }
        } catch (error) {
          console.error("OIDC callback error:", error)
        }
      }
    }

    checkAuthCallback().catch(console.error)
  }, [searchParams, router])

  return <></>
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<p>Loading callback...</p>}>
      <AuthCallback />
    </Suspense>
  )
}
