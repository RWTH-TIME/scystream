import type { SetAlertType } from "@/hooks/useAlert"
import { AlertType } from "@/hooks/useAlert"
import { api } from "@/utils/axios"
import { getConfig } from "@/utils/config"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { useEffect } from "react"
import { QueryKeys } from "./queryKeys"
import { ProjectStatus, type Project } from "@/utils/types"
import type { ComputeBlockByProjectResponse } from "./computeBlockMutation"
import { webSocketManager } from "@/utils/websocketManager"

const config = getConfig()
const PROJECT_STATUS_WS = "workflow/ws/project_status"
const CB_STATUS_WS = "workflow/ws/workflow_status/"
const TRIGGER_WORKFLOW = "workflow/"

type ProjectStatusEvent = Record<string, string>

export function useTriggerWorkflowMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function triggerWorkflow(project_id: string) {
      await api.post(TRIGGER_WORKFLOW + project_id)
      return project_id
    },
    onSuccess: (project_id) => {
      queryClient.setQueryData([QueryKeys.projects], (oldData: ProjectStatusEvent[] | undefined) => {
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
      console.error(error)
      // TODO: Handle the error more specifically. The backend returns which computeblocks might miss configs
      setAlert("Failed while triggering the project run. Check your Compute Blocks In- & Outputs as well as their connections.", AlertType.ERROR)
    }
  })
}



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
              status: data[project.uuid] ?? project.status,
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

type WfStatusData = {
  state: string,
}
type WorflowStatusEvent = Record<string, WfStatusData>

export function useComputeBlockStatusWS(setAlert: SetAlertType, project_id: string | undefined) {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!project_id) return

    const connectionString = `${config.wsUrl}${CB_STATUS_WS}${project_id}`

    const websocket = webSocketManager.getConnection<WorflowStatusEvent>(connectionString)

    function handleCBStatusMessage(data: WorflowStatusEvent) {
      queryClient.setQueryData([QueryKeys.cbByProject, project_id], (oldData: ComputeBlockByProjectResponse) => {
        if (!oldData) return
        const updated = oldData.blocks.map(block => {
          return {
            ...block,
            data: {
              ...block.data,
              status: data[block.id] ?? block.data.status
            }
          }
        })
        return {
          ...oldData,
          blocks: updated
        }
      })
    }

    function handleWebsocketError() {
      setAlert("Failed to get compute block status updates", AlertType.ERROR)
    }

    websocket.addListener(handleCBStatusMessage)
    websocket.addErrorHandler(handleWebsocketError)

    return () => {
      websocket.removeListener(handleCBStatusMessage)
      webSocketManager.removeConnection(connectionString)
    }
  }, [queryClient, setAlert, project_id])

}
