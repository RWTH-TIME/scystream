import { AlertType, type SetAlertType } from "@/hooks/useAlert"
import displayStandardAxiosErrors from "@/utils/errors"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { api } from "@/utils/axios"
import type { InputOutputType, RecordValueType } from "@/components/CreateComputeBlockModal"
import type { ComputeBlockNodeType } from "@/components/nodes/ComputeBlockNode"

const GET_COMPUTE_BLOCK_INFO = "compute_block/information"
const CREATE_COMPUTE_BLOCK = "compute_block/"
const UPDATE_COMPUTE_BLOCK = "compute_block/"
const GET_COMPUTE_BLOCK_BY_PROJECT = "compute_block/by_project/"
const DELETE_COMPUTE_BLOCK = "compute_block/"
const CREATE_EDGE = "compute_block/edge/"
const DELETE_EDGE = "compute_block/edge/delete"

type ComputeBlockInfoDTO = {
  cbc_url: string,
}

export function useGetComputeBlockInfoMutation(setAlert: SetAlertType) {
  return useMutation({
    mutationFn: async function getComputeBlockFromURL(compute_block: ComputeBlockInfoDTO) {
      const response = await api.post(GET_COMPUTE_BLOCK_INFO, JSON.stringify(compute_block))
      return response.data
    },
    onSuccess: () => { },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Getting Compute Block Info failed: ${error}`)
    }
  })
}

export type InputOutputDTO = {
  name: string,
  data_type: InputOutputType,
  description: string,
  config: Record<string, RecordValueType>,
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

export function useCreateComputeBlockMutation(setAlert: SetAlertType, project_id?: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function createComputeBlock(compute_block: CreateComputeBlockDTO) {
      const response = await api.post(CREATE_COMPUTE_BLOCK, JSON.stringify(compute_block))
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [project_id] })
      setAlert("Successfully created Compute Block.", AlertType.SUCCESS)
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Creating Compute Block failed: ${error}`)
    }
  })
}

type ComputeBlockByProjectResponse = {
  blocks: ComputeBlockNodeType[],
  edges: EdgeDTO[],
}

export function useComputeBlocksByProjectQuery(id: string | undefined) {
  return useQuery({
    queryKey: [id],
    queryFn: async function getProjects() {
      if (!id) return
      const response = await api.get(GET_COMPUTE_BLOCK_BY_PROJECT + id)
      return response.data
    },
    enabled: !!id
  })
}

export type UpdateInputOutputDTO = {
  id: string,
  config?: Record<string, RecordValueType>,
}

export type UpdateEntrypointDTO = {
  id: string,
  inputs?: UpdateInputOutputDTO[],
  outputs?: UpdateInputOutputDTO[],
  envs?: Record<string, RecordValueType>,
}

export type UpdateComputeBlockDTO = {
  id: string,
  custom_name?: string,
  selected_entrypoint?: UpdateEntrypointDTO,
  x?: number,
  y?: number,
}

function removeEmptyFields(obj: object): object {
  return Object.fromEntries(
    Object.entries(obj)
      .filter(([_, value]) => value !== undefined && value !== null)
      .map(([key, value]) => [key, value])
  )
}

type UpdateComputeBlockCoordsDTO = {
  id: string,
  x_pos: number,
  y_pos: number,
}
export function useUpdateComputeBlockCoords(setAlert: SetAlertType, project_id?: string) {
  const queryClient = useQueryClient()

  return useMutation<void, AxiosError, UpdateComputeBlockCoordsDTO>({
    mutationFn: async function updateComputeBlockCoords(coords: UpdateComputeBlockCoordsDTO) {
      await api.put(UPDATE_COMPUTE_BLOCK, JSON.stringify(coords))
    },
    onSuccess: (_, new_coords) => {
      queryClient.setQueryData([project_id], (oldData: ComputeBlockByProjectResponse) => {
        const cbID = new_coords.id

        const updated = oldData.blocks.map(block => {
          if (block.id === cbID) {
            return {
              ...block,
              position: {
                x: new_coords.x_pos,
                y: new_coords.y_pos
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

export function useUpdateComputeBlockMutation(setAlert: SetAlertType, project_id?: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function updateComputeBlock(update_dto: Partial<UpdateComputeBlockDTO>) {
      const cleaned = removeEmptyFields(update_dto)
      const response = await api.put(UPDATE_COMPUTE_BLOCK, JSON.stringify(cleaned))
      return response.data
    },
    onSuccess: () => {
      if (project_id) {
        // We are invalidating here, theoretically we could use setQueryDate here and update logic
        // here for the update compute block alone. However, as this seems to be very complex and
        // error prone we just requery.
        queryClient.invalidateQueries({ queryKey: [project_id] })
        setAlert("Compute block sucessfully updated!", AlertType.SUCCESS)
      }
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Updating Compute Block failed: ${error}`)
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
      queryClient.setQueryData([project_id], (oldData: ComputeBlockByProjectResponse) => {
        // TODO: handle edges here aswell
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
      await api.post(CREATE_EDGE, JSON.stringify(data))
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Creating Edge failed ${error}`)
    },
    onSuccess: () => {
      // Invalidate Queries, as inputs might be overwritten
      // We could also implement overwriting logic here, and then we
      // could save this extra query
      queryClient.invalidateQueries({ queryKey: [project_id] })
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
      queryClient.setQueryData([project_id], (oldData: ComputeBlockByProjectResponse) => {
        const updatedEdges = oldData.edges.filter(edge => edge.id !== edgeId)
        return {
          ...oldData,
          edges: updatedEdges,
        }
      })
    }
  })
}

