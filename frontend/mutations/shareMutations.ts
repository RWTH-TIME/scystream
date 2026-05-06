import { api } from "@/utils/axios"
import displayStandardAxiosErrors from "@/utils/errors"
import { useMutation } from "@tanstack/react-query"

import type { AxiosError } from "axios"
import { AlertType, type SetAlertType } from "@/hooks/useAlert"

export function useGenerateShareLinkMutation(
  setAlert: SetAlertType
) {
  return useMutation({
    mutationFn: async function generateShareLink( {project_id, type}: { project_id: string, type: "invite" | "template" }) {
      const response = await api.post(`project/${project_id}/share`)
      const token = response.data.token

      return `${window.location.origin}/${type}/${token}`
    },

    onError: (error: AxiosError) => {


      displayStandardAxiosErrors(error, setAlert)
      console.error(`Generating share link failed: ${error}`)
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
      const status = error.response?.status
      console.log("Status", status)

      if (status === 409) {
        setAlert("You are already a member of this project", AlertType.DEFAULT)
        return
      }

      displayStandardAxiosErrors(error, setAlert)
      console.error(`Accepting invite failed: ${error}`)
    }
  })
}

export function useAcceptTemplateMutation(setAlert: SetAlertType) {
  return useMutation({
    mutationFn: async function acceptInvite({token, project_name}: {token: string, project_name: string}) {
      const response = await api.post(`project/template/${token}/accept`, {project_name})
      return response.data
    },

    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Accepting invite failed: ${error}`)
    }
  })
}
