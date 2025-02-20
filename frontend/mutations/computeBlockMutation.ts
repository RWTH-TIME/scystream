import type { SetAlertType } from "@/hooks/useAlert";
import displayStandardAxiosErrors from "@/utils/errors";
import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { api } from "@/utils/axios";

const GET_COMPUTE_BLOCK_INFO = "compute_block/information"

type ComputeBlockDTO = {
  cbc_url: string,
}

export function useGetComputeBlockInfoMutation(setAlert: SetAlertType) {
  // const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function getComputeBlockFromURL(compute_block: ComputeBlockDTO) {
      const response = await api.post(GET_COMPUTE_BLOCK_INFO, JSON.stringify(compute_block))
      return response.data
    },
    onSuccess: () => {
      // TODO: invalidate queries?
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Creating Project failed: ${error}`)
    }
  })
}

// TODO: export function getComputeBlockQuery()
