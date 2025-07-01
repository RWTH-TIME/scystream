import { CLIENT_ID, OIDC_PROVIDER, POST_LOGOUT_REDIRECT_URI, REDIRECT_URI } from "@/utils/config"

import type { User } from "oidc-client-ts"
import { UserManager } from "oidc-client-ts"

const userManager = new UserManager({
  authority: OIDC_PROVIDER || "",
  client_id: CLIENT_ID || "",
  redirect_uri: REDIRECT_URI || "",
  response_type: "code",
  scope: "openid profile email",
  post_logout_redirect_uri: POST_LOGOUT_REDIRECT_URI,
})

export const signUp = () => {
  return userManager.signinRedirect()
}

export const login = (redirectURI?: string) => {
  return userManager.signinRedirect({ redirect_uri: redirectURI })
}

export const handleCallback = async () => {
  return await userManager.signinRedirectCallback()
}

export const getUser = async (): Promise<User | null> => {
  return await userManager.getUser()
}

export const removeUser = async () => {
  return await userManager.removeUser()
}
export const onTokenExpiringCallback = (callback: () => void) => {
  userManager.events.addAccessTokenExpiring(callback)
}


const parseJwt = (token: string): { exp: number } | null => {
  try {
    const base64Payload = token.split(".")[1]
    const payload = atob(base64Payload)
    return JSON.parse(payload)
  } catch {
    return null
  }
}

export const storeToken = (token: string) => {
  const parsed = parseJwt(token)
  if (!parsed || !parsed.exp) return

  const expiry = parsed.exp * 1000
  const value = JSON.stringify({ token, expiry })
  localStorage.setItem("token", value)
}

export const removeToken = () => {
  localStorage.removeItem("token")
}

export const getToken = (): string | null => {
  const value = localStorage.getItem("token")
  if (!value) return null

  try {
    const { token, expiry } = JSON.parse(value)
    if (Date.now() > expiry) {
      localStorage.removeItem("access_token")
      return null
    }
    return token
  } catch {
    localStorage.removeItem("access_token")
    return null
  }
}

export const restoreSession = async (): Promise<User | null> => {
  const user = await userManager.getUser()

  if (user) {
    storeToken(user.access_token)
  } else {
    removeToken()
  }
  return user
}

export const renewToken = async (): Promise<User | null> => {
  const user = await userManager.signinSilent().catch(() => null)

  if (user) {
    storeToken(user.access_token)
  } else {
    removeToken()
  }
  return user
}

export const logout = async () => {
  removeToken()
  await userManager.signoutRedirect()
}
