import { SetAlertType } from "@/hooks/useAlert"
import { api } from "@/utils/axios"
import displayStandardAxiosErrors from "@/utils/errors"
import { useMutation } from "@tanstack/react-query"
import type { AxiosError } from "axios"

export function useGenerateInviteLinkMutation(setAlert: SetAlertType) {
  return useMutation({
    mutationFn: async function generateInviteLink(project_id: string) {
      const response = await api.post(`project/${project_id}/invite`)
      const token = response.data.token
      const inviteLink = `${window.location.origin}/invite/${token}`

      return inviteLink
    },

    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Generating invite link failed: ${error}`)
    }
  })
}

export function useAcceptInviteMutation(setAlert: SetAlertType) {
  return useMutation({
    mutationFn: async function acceptInvite(token: string) {
      const response = await api.post(`project/invite/${token}/accept`)
      return response.data
    },

    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Accepting invite failed: ${error}`)
    }
  })
}
