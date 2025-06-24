import axios from "axios"
import { getConfig } from "./config"
import { getToken } from "@/api/auth/authService"

const config = getConfig()

const api = axios.create({
  baseURL: config.apiUrl,
})

api.defaults.headers.common["Content-Type"] = "application/json"

api.interceptors.request.use(function(reqconf) {
  // Attach the authentication token, if existant
  const token = getToken()

  if (token !== null) {
    reqconf.headers.Authorization = `Bearer ${token}`
  }

  return reqconf
}, function(error) {
  console.error(`request error ${error}`)
  return Promise.reject(error)
})

api.interceptors.response.use(function(response) {
  // Status code in range of 2xx
  return response
}, async function(error) {
  // Status code outside range of 2xx
  if (error.response.status === 401 && error.config.url !== "user/login") {
    console.error(`Error refreshing token: ${error}.`)

    localStorage.removeItem(config.accessTokenKey)
    localStorage.removeItem(config.refreshTokenKey)

    return Promise.reject(error)
  }

  return Promise.reject(error)
})

export {
  api
}
