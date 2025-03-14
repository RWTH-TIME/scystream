import type { SetAlertType } from "@/hooks/useAlert";
import { AlertType } from "@/hooks/useAlert";
import { api } from "@/utils/axios";
import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";

const TRIGGER_WORKFLOW = "workflow/"

export function useTriggerWorkflowMutation(setAlert: SetAlertType) {
  //const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function triggerWorkflow(project_id: string) {
      await api.post(TRIGGER_WORKFLOW + project_id)
    },
    onSuccess: () => {
      // Invalidate Status of Project
      setAlert("Successfully triggered project run.", AlertType.SUCCESS)
    },
    onError: (error: AxiosError) => {
      // TODO: Handle Error
      console.log(error)
    }
  })
}
