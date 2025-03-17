import type { SetAlertType } from "@/hooks/useAlert"
import { AlertType } from "@/hooks/useAlert"
import { api } from "@/utils/axios"
import { getConfig } from "@/utils/config"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { useEffect } from "react"
import { QueryKeys } from "./queryKeys"
import { ProjectStatus, type Project } from "@/utils/types"

const config = getConfig()
const PROJECT_STATUS_WS = "workflow/ws/project_status"
const TRIGGER_WORKFLOW = "workflow/"

export function useTriggerWorkflowMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function triggerWorkflow(project_id: string) {
      await api.post(TRIGGER_WORKFLOW + project_id)
      return project_id
    },
    onSuccess: (project_id) => {
      queryClient.setQueryData([QueryKeys.projects], (oldData: Project[] | undefined) => {
        if (!oldData) return []

        return oldData.map(project => {
          if (project.uuid === project_id) {
            return { ...project, status: ProjectStatus.RUNNING }
          }
          return project
        })
      })
      setAlert("Successfully triggered project run.", AlertType.SUCCESS)
    },
    onError: (error: AxiosError) => {
      // TODO: Handle Error
      console.log(error)
    }
  })
}

export function useProjectStatusWS(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  useEffect(() => {
    const websocket = new WebSocket(`${config.wsUrl}${PROJECT_STATUS_WS}`)

    websocket.onopen = () => {
      console.log("WebSocket connection established")
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      // Update project with id
      queryClient.setQueryData([QueryKeys.projects], (oldData: Project[]) => {
        if (!oldData) return oldData
        const updatedProjects = oldData.map((project: Project) => {
          if (data[project.uuid]) {
            return {
              ...project,
              status: data[project.uuid],
            }
          }
          return project
        })

        return updatedProjects
      })
    }

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error)
      setAlert("Error fetching Project Status", AlertType.ERROR)
    }

    websocket.onclose = (event) => {
      console.log("WebSocket connection closed", event)
    }
  }, [queryClient, setAlert])
}
