import type { SetAlertType } from "@/hooks/useAlert"
import { AlertType } from "@/hooks/useAlert"
import { api } from "@/utils/axios"
import { getConfig } from "@/utils/config"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { useEffect, useRef } from "react"
import { QueryKeys } from "./queryKeys"
import { ProjectStatus, type Project } from "@/utils/types"
import type { ComputeBlockByProjectResponse } from "./computeBlockMutation"
import { webSocketManager } from "@/utils/websocketManager"

const config = getConfig()
const PROJECT_STATUS_WS = "workflow/ws/project_status"
const CB_STATUS_WS = "workflow/ws/workflow_status/"
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

type ProjectStatusEvent = Record<string, string>

export function useProjectStatusWS(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  useEffect(() => {
    const websocket = webSocketManager.getConnection<ProjectStatusEvent>(`${config.wsUrl}${PROJECT_STATUS_WS}`)

    function handleProjectStatusMessage(data: ProjectStatusEvent) {
      queryClient.setQueryData([QueryKeys.projects], (oldData: Project[]) => {
        if (!oldData) return
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

    function handleWebsocketError() {
      setAlert("Failed to get project status updates", AlertType.ERROR)
    }

    websocket.addListener(handleProjectStatusMessage)
    websocket.addErrorHandler(handleWebsocketError)

    return () => {
      websocket.removeListener(handleProjectStatusMessage)
    }
  }, [queryClient, setAlert])
}

export function useComputeBlockStatusWS(setAlert: SetAlertType, project_id: string | undefined) {
  // TODO: Use the WebsocketManager here aswell
  const queryClient = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!project_id) return

    if (wsRef.current) {
      wsRef.current.close()
    }

    const websocket = new WebSocket(`${config.wsUrl}${CB_STATUS_WS}${project_id}`)
    wsRef.current = websocket

    websocket.onopen = () => {
      console.log("WebSocket connection for compute block status established")
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      queryClient.setQueryData([project_id], (oldData: ComputeBlockByProjectResponse) => {
        if (!oldData) return
        const updated = oldData.blocks.map(block => {
          return {
            ...block,
            data: {
              ...block.data,
              status: data[block.id].state
            }
          }
        })
        return {
          ...oldData,
          blocks: updated
        }
      })
    }

    websocket.onerror = (error) => {
      console.error("Websocket for cb status error:", error)
      setAlert("Error fetching the Compute Blocks status", AlertType.ERROR)
    }

    websocket.onclose = (event) => {
      console.log("Websocket for cb status connection closed", event)
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }

  }, [queryClient, setAlert, project_id])
}
