import axios from "axios"
import { getConfig } from "./config"

const config = getConfig()

/*
  This is the global configuration for axios
*/

const api = axios.create({
  baseURL: config.apiUrl,
})

api.defaults.headers.common["Content-Type"] = "application/json"

api.interceptors.request.use(function(reqconf) {
  // Attach the authentication token, if existant
  const token = localStorage.getItem(config.accessTokenKey)
  if (token !== null) {
    reqconf.headers.Authorization = `Bearer ${token}`
  }

  return reqconf
}, function(error) {
  console.error(`request error ${error}`)
})

api.interceptors.response.use(function(response) {
  // Status code in range of 2xx
  return response
}, async function(error) {
  // Status code outside range of 2xx
  console.log(error)
  if (error.response.status === 401) {
    try {
      const refreshToken = localStorage.getItem(config.refreshTokenKey)
      const response = await api.post("user/refresh", {
        refresh_token: refreshToken
      })
      const { access_token: accessToken, refresh_token: newRefreshToken } = response.data
      localStorage.setItem(config.accessTokenKey, accessToken)
      localStorage.setItem(config.refreshTokenKey, newRefreshToken)
      return response
    } catch (error) {
      console.error(`Error refreshing token: ${error}.`)

      localStorage.removeItem(config.accessTokenKey)
      localStorage.removeItem(config.refreshTokenKey)

      // TODO: navigate back to the login

      return Promise.reject(error)
    }
  }

  return Promise.reject(error)
})

export {
  api
}
