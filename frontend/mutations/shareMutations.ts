import { api } from "@/utils/axios"
import displayStandardAxiosErrors from "@/utils/errors"
import { useMutation, type UseMutationOptions, useQuery } from "@tanstack/react-query"

import type { AxiosError } from "axios"
import { type SetAlertType } from "@/hooks/useAlert"

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

export function useTemplatePreviewQuery(token: string) {
  return useQuery({
    queryKey: ["templatePrev", token],
    queryFn: async function requestTemplatePreview() {
      if (!token) return
      const response = await api.get(`project/template/${token}/preview`)
      return response.data
    },
    enabled: !!token
  })
}

type AcceptInviteQueryResponse = {
  detail: string,
  is_already_member?: boolean,
  project_uuid: string
}

export function useAcceptInviteQuery(token: string, options?: UseMutationOptions<AcceptInviteQueryResponse>) {
  return useQuery({
    queryKey: ["inviteAccept", token],
    queryFn: async () => {
        const response = await api.get(`project/invite/${token}/accept`)
        return response.data
      },
      retry: false,
      ...options,
    })
}

type AcceptTemplatePayload = {
  token: string,
  project_name: string
}

type AcceptTemplateMutationResponse = {
  project_uuid: string
}

export function useAcceptTemplateMutation(setAlert: SetAlertType, options?: UseMutationOptions<AcceptTemplateMutationResponse, AxiosError, AcceptTemplatePayload>) {
  return useMutation({
    mutationFn: async function acceptInvite({token, project_name}: AcceptTemplatePayload) {
      const response = await api.post(`project/template/${token}/accept`, {project_name})
      return response.data
    },

    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Accepting invite failed: ${error}`)
    },
    ...options,
  })
}
