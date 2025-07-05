import axios from "axios"
import { API_URL } from "@/utils/config"
import { getToken } from "@/utils/auth/authService"


const api = axios.create({
  baseURL: API_URL,
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
  if (error.response.status === 401) {
    console.error(`Error refreshing token: ${error}.`)

    return Promise.reject(error)
  }

  return Promise.reject(error)
})

export {
  api
}
