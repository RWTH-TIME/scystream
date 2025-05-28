import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { QueryKeys } from "./queryKeys"
import { api } from "@/utils/axios"
import { AlertType, type SetAlertType } from "@/hooks/useAlert"
import displayStandardAxiosErrors from "@/utils/errors"
import type { Project } from "@/utils/types"

const GET_PROJECTS_ENDPOINT = "project/read_all"
const CREATE_PROJECT_ENDPOINT = "project"
const DELETE_PROJECT_ENDPOINT = "project/"
const UPDATE_PROJECT_ENDPOINT = "project/"
const CREATE_PROJECT_FROM_TEMPLATE_ENDPOINT = "project/from_template"

type ProjectDTO = {
  name: string,
}

type UpdateProjectDTO = {
  project_uuid: string,
  new_name: string,
}

function useProjectsQuery() {
  return useQuery({
    queryKey: [QueryKeys.projects],
    queryFn: async function getProjects() {
      const response = await api.get(GET_PROJECTS_ENDPOINT)
      return response.data.projects
    },
    refetchOnWindowFocus: false,
    staleTime: 1000 * 60 * 3
  })
}

function useCreateProjectMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function createProject(project: ProjectDTO) {
      const response = await api.post(CREATE_PROJECT_ENDPOINT, JSON.stringify(project))
      return {
        data: project,
        new_id: response.data.project_uuid
      }
    },
    onSuccess: ({ data, new_id }) => {
      const fullProject = {
        ...data,
        created_at: new Date().toISOString().slice(0, 19).replace("T", " "),
        uuid: new_id,
      }

      queryClient.setQueryData([QueryKeys.projects], (oldData: Project[] | undefined) => {
        if (oldData) {
          return [...oldData, fullProject]
        }
        return [fullProject]
      })
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Creating Project failed: ${error}`)
    }
  })
}

type CreateProjectFromTemplateDTO = {
  name: string,
  template_identifier: string,
}

function useCreateProjectFromTemplateMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function createProjectFromTemplate(project_from_template: CreateProjectFromTemplateDTO) {
      const response = await api.post(CREATE_PROJECT_FROM_TEMPLATE_ENDPOINT, JSON.stringify(project_from_template))
      return {
        data: project_from_template,
        new_id: response.data.project_uuid
      }
    },
    onSuccess: ({ data, new_id }) => {
      const fullProject = {
        created_at: new Date().toISOString().slice(0, 19).replace("T", " "),
        ...data,
        uuid: new_id,
      }
      queryClient.setQueryData([QueryKeys.projects], (oldData: Project[] | undefined) => {
        if (oldData) {
          return [...oldData, fullProject]
        }
        return [fullProject]
      })
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Creating Project failed: ${error}`)
    }
  })
}

function useUpdateProjectMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function updateProject(project: UpdateProjectDTO) {
      const response = await api.put(UPDATE_PROJECT_ENDPOINT, JSON.stringify(project))
      return response.data.project_uuid
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QueryKeys.projects] })
      setAlert("Successfully updated project.", AlertType.SUCCESS)
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.error(`Updating Project failed: ${error}`)
    }
  })
}



function useDeleteProjectMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function delProject(projectID: string) {
      await api.delete(DELETE_PROJECT_ENDPOINT + projectID)
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
      console.log(`Deleting project failed ${error}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QueryKeys.projects] })
      setAlert("Project sucessfully deleted!", AlertType.SUCCESS)
    }
  })
}

export {
  useProjectsQuery,
  useCreateProjectMutation,
  useUpdateProjectMutation,
  useDeleteProjectMutation,
  useCreateProjectFromTemplateMutation
}
