import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { QueryKeys } from "./queryKeys"
import { api } from "@/utils/axios"
import type { SetAlertType } from "@/hooks/useAlert"
import displayStandardAxiosErrors from "@/utils/errors"

const GET_PROJECTS_ENDPOINT = "project/read_all"
const CREATE_PROJECT_ENDPOINT = "project"

type ProjectDTO = {
  name: string
}

function useProjectsQuery() {
  return useQuery({
    queryKey: [QueryKeys.projects],
    queryFn: async function getProjects() {
      const response = await api.get(GET_PROJECTS_ENDPOINT)
      return response.data.projects
    }
  })
}

function useCreateProjectMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function createProject(project: ProjectDTO) {
      const response = await api.post(CREATE_PROJECT_ENDPOINT, JSON.stringify(project))
      return response.data.project_uuid
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QueryKeys.projects] })
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Creating Project failed: ${error}`)
    }
  })
}

export {
  useProjectsQuery,
  useCreateProjectMutation,
}
