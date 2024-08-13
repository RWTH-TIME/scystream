import React, { useEffect, type ComponentType } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/hooks/useAuth"

export default function withProtectedRoute<P extends object>(WrappedComponent: ComponentType<P>) {
  return function WithAuth(props: P) {
    const { user } = useAuth()
    const router = useRouter()

    useEffect(() => {
      if (!user) {
        router.push("/login")
      }
    }, [user, router])

    return user ? <WrappedComponent {...props as P} /> : undefined
  }
}
