import { AlertType, type SetAlertType } from "@/hooks/useAlert";
import displayStandardAxiosErrors from "@/utils/errors";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { api } from "@/utils/axios";
import type { InputOutputType, RecordValueType } from "@/components/CreateComputeBlockModal";

const GET_COMPUTE_BLOCK_INFO = "compute_block/information"
const CREATE_COMPUTE_BLOCK = "compute_block/"
const GET_COMPUTE_BLOCK_BY_PROJECT = "compute_block/by_project/"

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
