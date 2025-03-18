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

export function useProjectStatusWS(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  useEffect(() => {
    const websocket = new WebSocket(`${config.wsUrl}${PROJECT_STATUS_WS}`)

    websocket.onopen = () => {
      console.log("WebSocket connection for project status established")
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      // Update project with id
      queryClient.setQueryData([QueryKeys.projects], (oldData: Project[]) => {
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
      console.error("WebSocket for project status error:", error)
      setAlert("Error fetching Project Status", AlertType.ERROR)
    }

    websocket.onclose = (event) => {
      console.log("WebSocket for project status: connection closed", event)
    }
  }, [queryClient, setAlert])
}

export function useComputeBlockStatusWS(setAlert: SetAlertType, project_id: string | undefined) {
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
