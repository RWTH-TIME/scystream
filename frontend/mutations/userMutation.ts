import { useMutation } from "@tanstack/react-query"
import { api } from "@/utils/axios"
import { getConfig } from "@/utils/config"

const config = getConfig()

const REGISTER_ENDPOINT = "user/create"
const LOGIN_ENDPOINT = "user/login"
const REFRESH_ENDPOINT = "user/refresh"
const TEST_ENDPOINT = "user/test"

type UserDTO = {
  email: string,
  password: string
}

type RefreshDTO = {
  old_access_token: string,
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
        console.error(`Registration failed: ${error}`)
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
        console.error(`Login failed ${error}`)
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

        localStorage.setItem(config.accessTokenKey, response.data.new_access_token)
        localStorage.setItem(config.refreshTokenKey, response.data.refresh_token)

        return response.data
      } catch (error) {
        // TODO: Handle error
        console.error(`Refreshing failed: ${error}`)
      }
    },
  })
}

function useTestMutation() {
  return useMutation({
    mutationFn: async function test(test: RefreshDTO) {
      try {
        const response = await api.post(TEST_ENDPOINT, JSON.stringify(test))

        return response.data
      } catch (error) {
        console.log(`Test failed: ${error}`)
      }
    }
  })
}

export {
  useRegisterMutation,
  useLoginMutation,
  useRefreshMutation,
  useTestMutation
}
