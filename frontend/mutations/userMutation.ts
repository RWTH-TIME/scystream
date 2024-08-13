import { useMutation } from "@tanstack/react-query"
import { api } from "@/utils/axios"
import { getConfig } from "@/utils/config"

const config = getConfig()

const REGISTER_ENDPOINT = "user/create"
const LOGIN_ENDPOINT = "user/login"
const REFRESH_ENDPOINT = "user/refresh"

type UserDTO = {
  email: string,
  password: string
}

type RefreshDTO = {
  refresh_token: string
}

function useRegisterMutation() {
  return useMutation({
    mutationFn: async function register(user: UserDTO) {
      try {
        const response = await api.post(REGISTER_ENDPOINT, JSON.stringify(user))

        return response.data
      } catch (error) {
        // TODO: Handle error
        console.error("Registration failed")
      }
    },
  })
}

function useLoginMutation() {
  return useMutation({
    mutationFn: async function login(user: UserDTO) {
      try {
        const response = await api.post(LOGIN_ENDPOINT, JSON.stringify(user))

        localStorage.setItem(config.accessTokenKey, response.data.access_token)
        localStorage.setItem(config.refreshTokenKey, response.data.refresh_token)

        return response.data
      } catch (error) {
        // TODO: Handle error
        console.error("Login failed")
        throw error
      }
    },
  })
}

function useRefreshMutation() {
  return useMutation({
    mutationFn: async function login(refresh: RefreshDTO) {
      try {
        const response = await api.post(REFRESH_ENDPOINT, JSON.stringify(refresh))

        localStorage.setItem(config.accessTokenKey, response.data.access_token)
        localStorage.setItem(config.refreshTokenKey, response.data.refresh_token)

        return response.data
      } catch (error) {
        // TODO: Handle error
        console.error("Refreshing failed")
      }
    },
  })
}

export {
  useRegisterMutation,
  useLoginMutation,
  useRefreshMutation
}
