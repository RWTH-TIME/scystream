import type { ComponentType, PropsWithChildren } from "react"
import { createContext, useContext, useEffect, useState } from "react"
import { login, logout, restoreSession, renewToken, onTokenExpiringCallback, removeUser } from "@/api/auth/authService"
import type { User } from "oidc-client-ts"
import { REDIRECT_URI } from "@/api/config"

type AuthContextType = {
  identity: User,
  token: string,
  logout: () => void,
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: PropsWithChildren) => {
  const [identity, setIdentity] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const forceLogin = async () => {
    await removeUser()
    await login(`${REDIRECT_URI}?redirect_uri=${encodeURIComponent(window.location.href)}`)
  }

  const handleLogout = async () => {
    await logout()
  }

  useEffect(() => {
    const initAuth = async () => {
      try {
        const user = await restoreSession()
        if (!user) {
          throw new Error("No user session")
        }

        setIdentity(user)
        onTokenExpiringCallback(async () => {
          console.log("Token expiring. Attempting silent renewal...")
          const refreshed = await renewToken()
          if (refreshed) {
            setIdentity(refreshed)
          } else {
            await forceLogin()
          }
        })
      } catch {
        console.warn("Session restore failed, logging in.")
        await forceLogin()
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  if (loading) return null

  if (!identity) return null

  return (
    <AuthContext.Provider
      value={{
        identity,
        token: identity.access_token,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}


export const withAuth = <P extends object>(Component: ComponentType<P>) => {
  const WrappedComponent = (props: P) => (
    <AuthProvider>
      <Component {...props} />
    </AuthProvider>
  )
  WrappedComponent.displayName = `withAuth(${Component.displayName || Component.name || "Component"})`

  return WrappedComponent
}


export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }

  return { ...context }
}
