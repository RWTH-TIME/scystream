import type { SetAlertType } from "@/hooks/useAlert";
import displayStandardAxiosErrors from "@/utils/errors";
import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { api } from "@/utils/axios";

const CREATE_COMPUTE_BLOCK_ENDPOINT = "compute_block/"

type ComputeBlockDTO = {
  compute_block_title: string,
  cbc_url: string,
}

export function useCreateComputeBlockMutation(setAlert: SetAlertType) {
  // const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function createComputeBlock(compute_block: ComputeBlockDTO) {
      const response = await api.post(CREATE_COMPUTE_BLOCK_ENDPOINT, JSON.stringify(compute_block))
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
