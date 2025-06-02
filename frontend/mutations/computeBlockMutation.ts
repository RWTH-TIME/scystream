import { AlertType, type SetAlertType } from "@/hooks/useAlert"
import displayStandardAxiosErrors from "@/utils/errors"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { api } from "@/utils/axios"
import type { InputOutputType } from "@/components/CreateComputeBlockModal"
import { IOType, type RecordValueType } from "@/components/CreateComputeBlockModal"
import type { ComputeBlockNodeType } from "@/components/nodes/ComputeBlockNode"
import { QueryKeys } from "./queryKeys"

const GET_COMPUTE_BLOCK_INFO = "compute_block/information"
const CREATE_COMPUTE_BLOCK = "compute_block/"
const UPDATE_COMPUTE_BLOCK = "compute_block/"
const GET_COMPUTE_BLOCK_BY_PROJECT = "compute_block/by_project/"
const GET_CONFIGS_BY_PROJECT = "compute_block/configurations/by_project/{project_id}"
const GET_ENVS = "compute_block/entrypoint/{entry_id}/envs"
const GET_IOS = "compute_block/entrypoint/{entry_id}/io/?io_type={io_type}"
const UPDATE_IOS = "compute_block/entrypoint/io/"
const DELETE_COMPUTE_BLOCK = "compute_block/"
const CREATE_EDGE = "compute_block/edge/"
const DELETE_EDGE = "compute_block/edge/delete"

type ComputeBlockInfoDTO = {
  cbc_url: string,
}

export type InputOutputDTO = {
  name: string,
  data_type: InputOutputType,
  description: string,
  config: Record<string, RecordValueType>,
  selected_file_b64?: string,
  selected_file_type?: string,
}

type EntrypointDTO = {
  name: string,
  description: string,
  inputs: InputOutputDTO[],
  outputs: InputOutputDTO[],
  envs: Record<string, RecordValueType>,
}

export type CreateComputeBlockDTO = {
  project_id: string,
  cbc_url: string,
  name: string,
  custom_name: string,
  description: string,
  author: string,
  image: string,
  selected_entrypoint: EntrypointDTO,
  x_pos: number,
  y_pos: number,
}

export type ComputeBlockByProjectResponse = {
  blocks: ComputeBlockNodeType[],
  edges: EdgeDTO[],
}

export function useGetComputeBlockInfoMutation(setAlert: SetAlertType) {
  return useMutation({
    mutationFn: async function getComputeBlockFromURL(compute_block: ComputeBlockInfoDTO) {
      const response = await api.post(GET_COMPUTE_BLOCK_INFO, JSON.stringify(compute_block))
      return response.data
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Getting Compute Block Info failed: ${error}`)
    }
  })
}

export function useComputeBlocksByProjectQuery(id: string | undefined) {
  return useQuery({
    queryKey: [QueryKeys.cbByProject, id],
    queryFn: async function getProjects() {
      if (!id) return
      const response = await api.get(GET_COMPUTE_BLOCK_BY_PROJECT + id)
      return response.data
    },
    enabled: !!id,
  })
}

export function useGetComputeBlocksConfigurationByProjectQuery(id: string | undefined) {
  return useQuery({
    queryKey: [QueryKeys.cbConfigsByProject, id],
    queryFn: async function getConfigurationsByProject() {
      if (!id) return
      const response = await api.get(GET_CONFIGS_BY_PROJECT.replace("{project_id}", id))
      return response.data
    },
    refetchOnWindowFocus: false,
    enabled: !!id,
  })
}

export function useComputeBlockEnvsQuery(entrypointId: string | undefined) {
  return useQuery({
    queryKey: [QueryKeys.cbEnvs, entrypointId],
    queryFn: async function getEvns() {
      if (!entrypointId) return
      const response = await api.get(GET_ENVS.replace("{entry_id}", entrypointId))
      return response.data
    },
    refetchOnWindowFocus: false,
    enabled: !!entrypointId
  })
}

export function useComputeBlocksIOsQuery(io_type: IOType, entrypointId?: string) {
  return useQuery({
    queryKey: [io_type === IOType.INPUT ? QueryKeys.cbInputs : QueryKeys.cbOutputs, entrypointId],
    queryFn: async function getEvns() {
      if (!entrypointId) return
      const response = await api.get(GET_IOS.replace("{entry_id}", entrypointId).replace("{io_type}", io_type))
      return response.data
    },
    refetchOnWindowFocus: false,
    enabled: !!entrypointId
  })
}

export function useCreateComputeBlockMutation(setAlert: SetAlertType, project_id?: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function createComputeBlock(compute_block: CreateComputeBlockDTO) {
      const response = await api.post(CREATE_COMPUTE_BLOCK, JSON.stringify(compute_block))
      return response.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData([QueryKeys.cbByProject, project_id], (oldData: ComputeBlockByProjectResponse) => {
        if (oldData) {
          return {
            ...oldData,
            blocks: [...oldData.blocks, data]
          }
        }
        return {
          edges: [],
          blocks: [data]
        }
      })
      setAlert("Successfully created Compute Block.", AlertType.SUCCESS)
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Creating Compute Block failed: ${error}`)
    }
  })
}

export function useDeleteComputeBlockMutation(setAlert: SetAlertType, project_id?: string) {
  const queryClient = useQueryClient()

  return useMutation<void, AxiosError, string>({
    mutationFn: async function deleteComputeBlock(id: string): Promise<void> {
      await api.delete(DELETE_COMPUTE_BLOCK + id)
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Deleting compute block failed ${error}`)
    },
    onSuccess: (_, del_block_id) => {
      queryClient.setQueryData([QueryKeys.cbByProject, project_id], (oldData: ComputeBlockByProjectResponse) => {
        if (!oldData) return
        const updatedBlocks = oldData.blocks.filter(block => block.id !== del_block_id)
        return {
          ...oldData,
          blocks: updatedBlocks
        }
      })
      setAlert("Compute block sucessfully deleted!", AlertType.SUCCESS)
    }
  })
}

export type EdgeDTO = {
  id?: string,
  source: string,
  sourceHandle: string,
  target: string,
  targetHandle: string,
}

export function useCreateEdgeMutation(setAlert: SetAlertType, project_id?: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async function createEdge(data: EdgeDTO) {
      const response = await api.post(CREATE_EDGE, JSON.stringify(data))
      return {
        response_data: response.data,
        dto: data
      }
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Creating Edge failed ${error}`)
    },
    onSuccess: (data) => {
      // Invalidate Inputs  we connected to
      queryClient.invalidateQueries({ queryKey: [QueryKeys.cbInputs, data.response_data.id] })
      // Add the edge to the project data
      queryClient.setQueryData([QueryKeys.cbByProject, project_id], (oldData: ComputeBlockByProjectResponse) => {
        return {
          ...oldData,
          edges: [...oldData.edges, {
            id: `${data.dto.sourceHandle}-${data.dto.targetHandle}`,
            ...data.dto
          }]
        }
      })
    }
  })
}

export function useDeleteEdgeMutation(setAlert: SetAlertType, project_id?: string) {
  const queryClient = useQueryClient()

  return useMutation<void, AxiosError, EdgeDTO>({
    mutationFn: async (data: EdgeDTO): Promise<void> => {
      await api.post(DELETE_EDGE, JSON.stringify(data))
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Deleting Edge failed ${error}`)
    },
    onSuccess: (_, del_edge) => {
      const edgeId = del_edge.id
      queryClient.setQueryData([QueryKeys.cbByProject, project_id], (oldData: ComputeBlockByProjectResponse) => {
        const updatedEdges = oldData.edges.filter(edge => edge.id !== edgeId)
        return {
          ...oldData,
          edges: updatedEdges,
        }
      })
    }
  })
}

export type UpdateInputOutputDTO = {
  id: string,
  type: IOType,
  entrypoint_id?: string, // Set in response
  config?: Record<string, RecordValueType>,
  selected_file_b64?: string,
  selected_file_type?: string,
}

export type UpdateEntrypointDTO = {
  id: string,
  envs?: Record<string, RecordValueType>,
}

export type UpdateComputeBlockDTO = {
  id: string,
  custom_name?: string,
  x_pos?: number,
  y_pos?: number,
}

export function useUpdateComputeBlocksIOsMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function updateIO(data: UpdateInputOutputDTO[]) {
      const response = await api.put(UPDATE_IOS, data)
      return response.data
    },
    onSuccess: (data) => {
      data.forEach((updatedIo: UpdateInputOutputDTO) => {
        queryClient.setQueryData(
          [updatedIo.type === IOType.INPUT ? QueryKeys.cbInputs : QueryKeys.cbOutputs, updatedIo.entrypoint_id],
          (oldData: UpdateInputOutputDTO[] | undefined) => {
            if (!oldData) return []

            return oldData.map((io) => {
              if (io.id === updatedIo.id) {
                return { ...io, ...updatedIo }
              }
              return io
            })
          }
        )
      })
    }
  })
}

export function useUpdateComputeBlockMutation(setAlert: SetAlertType, project_id?: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function updateComputeBlock(update_dto: Partial<UpdateComputeBlockDTO>) {
      const response = await api.put(UPDATE_COMPUTE_BLOCK, update_dto)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.setQueryData([QueryKeys.cbByProject, project_id], (oldData: ComputeBlockByProjectResponse) => {
        const cbID = data.id

        const updated = oldData.blocks.map(block => {
          if (block.id === cbID) {
            return {
              ...block,
              data: {
                ...block.data,
                custom_name: data.custom_name,
                envs: data.envs,
              },
              position: {
                x: data.x_pos,
                y: data.y_pos
              }
            }
          }
          return block
        })

        return {
          ...oldData,
          blocks: updated
        }
      })

    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Updating Compute Block failed: ${error}`)
    }
  })
}
