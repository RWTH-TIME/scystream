import { useMutation } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { api } from "@/utils/axios"
import { getConfig } from "@/utils/config"
import type { setAlertType } from "@/hooks/useAlert"
import displayStandardAxiosErrors from "@/utils/errors"

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

function useRegisterMutation(setAlert: setAlertType) {
  return useMutation({
    mutationFn: async function register(user: UserDTO) {
      const response = await api.post(REGISTER_ENDPOINT, JSON.stringify(user))
      return response.data
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Registration failed: ${error}`)
    }
  })
}

function useLoginMutation(setAlert: setAlertType) {
  return useMutation({
    mutationFn: async function login(user: UserDTO) {
      const response = await api.post(LOGIN_ENDPOINT, JSON.stringify(user))

      localStorage.setItem(config.accessTokenKey, response.data.access_token)
      localStorage.setItem(config.refreshTokenKey, response.data.refresh_token)

      return response.data
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Login failed ${error}`)
    },
    onSuccess: () => {
      window.location.href = "/dashboard"
    }
  })
}

function useRefreshMutation() {
  return useMutation({
    mutationFn: async function login(refresh: RefreshDTO) {
      const response = await api.post(REFRESH_ENDPOINT, JSON.stringify(refresh))

      localStorage.setItem(config.accessTokenKey, response.data.new_access_token)
      localStorage.setItem(config.refreshTokenKey, response.data.refresh_token)

      return response.data
    },
    onError: (error) => {
      console.error(`Refreshing failed: ${error}`)
    }
  })
}

function useTestMutation() {
  return useMutation({
    mutationFn: async function test(test: RefreshDTO) {
      const response = await api.post(TEST_ENDPOINT, JSON.stringify(test))

      return response.data
    },
    onError: (error) => {
      console.log(`Test failed: ${error}`)
    }
  })
}

export {
  useRegisterMutation,
  useLoginMutation,
  useRefreshMutation,
  useTestMutation
}
