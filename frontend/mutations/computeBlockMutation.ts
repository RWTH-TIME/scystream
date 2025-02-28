import { AlertType, type SetAlertType } from "@/hooks/useAlert";
import displayStandardAxiosErrors from "@/utils/errors";
import { QueryClient, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { api } from "@/utils/axios";
import type { InputOutputType, RecordValueType } from "@/components/CreateComputeBlockModal";

const GET_COMPUTE_BLOCK_INFO = "compute_block/information"
const CREATE_COMPUTE_BLOCK = "compute_block/"
const UPDATE_COMPUTE_BLOCK = "compute_block/"
const GET_COMPUTE_BLOCK_BY_PROJECT = "compute_block/by_project/"
const DELETE_COMPUTE_BLOCK = "compute_block/"

type ComputeBlockInfoDTO = {
  cbc_url: string,
}

export function useGetComputeBlockInfoMutation(setAlert: SetAlertType) {
  // const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function getComputeBlockFromURL(compute_block: ComputeBlockInfoDTO) {
      const response = await api.post(GET_COMPUTE_BLOCK_INFO, JSON.stringify(compute_block))
      return response.data
    },
    onSuccess: () => {
      // TODO: invalidate queries?
    },
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

type UpdateInputOutputDTO = {
  id: string,
  config?: Record<string, RecordValueType>,
}

type UpdateEntrypointDTO = {
  id: string,
  inputs?: UpdateInputOutputDTO[],
  outputs?: UpdateInputOutputDTO[],
  envs?: Record<string, RecordValueType>,
}

type UpdateComputeBlockDTO = {
  id: string,
  custom_name?: string,
  selected_entrypoint?: UpdateEntrypointDTO,
  x_pos?: number,
  y_pos?: number,
}

function removeEmptyFields(obj: object): object {
  return Object.fromEntries(
    Object.entries(obj)
      .filter(([_, value]) => value !== undefined && value !== null)
      .map(([key, value]) => [key, value])
  )
}

export function useUpdateComputeBlockMutation(setAlert: SetAlertType) {
  return useMutation({
    mutationFn: async function updateComputeBlock(update_dto: UpdateComputeBlockDTO) {
      const cleaned = removeEmptyFields(update_dto)
      const response = await api.put(UPDATE_COMPUTE_BLOCK, JSON.stringify(cleaned))
      return response.data;
    },
    onSuccess: () => { },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Updating Compute Block failed: ${error}`)
    }
  })
}


export function useDeleteComputeBlockMutation(setAlert: SetAlertType, project_id?: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function deleteComputeBlock(id: string) {
      await api.delete(DELETE_COMPUTE_BLOCK + id)
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.log(`Deleting compute block failed ${error}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [project_id] })
      setAlert("Compute block sucessfully deleted!", AlertType.SUCCESS)
    }
  })
}
