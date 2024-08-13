import { useRouter } from "next/navigation"
import { api } from "./axios"
import { getConfig } from "./config"

/*
  Within this file, our request and repsponse interceptors are defined
*/

const envConfig = getConfig()

api.interceptors.request.use(function(config) {
  // Attach the authentication token, if existant
  const token = localStorage.getItem(envConfig.accessTokenKey)

  if (token !== null) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
}, function(error) {
  console.error(`request error ${error}`)
})

api.interceptors.response.use(function(response) {
  // Status code in range of 2xx
  return response
}, async function(error) {
  // Status code outside range of 2xx
  if (error.response.status === 401) {
    try {
      const refreshToken = localStorage.getItem(envConfig.refreshTokenKey)
      const response = await api.post("user/refresh", {
        refresh_token: refreshToken
      })
      const { access_token: accessToken, refresh_token: newRefreshToken } = response.data
      localStorage.setItem(envConfig.accessTokenKey, accessToken)
      localStorage.setItem(envConfig.refreshTokenKey, newRefreshToken)
      return response
    } catch (error) {
      console.error(`Error refreshing token: ${error}.`)

      const router = useRouter()

      localStorage.removeItem(envConfig.accessTokenKey)
      localStorage.removeItem(envConfig.refreshTokenKey)

      router.push("/login")

      return Promise.reject(error)
    }
  }

  return Promise.reject(error)
})
