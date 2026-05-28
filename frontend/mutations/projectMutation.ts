import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { QueryKeys } from "./queryKeys"
import { api } from "@/utils/axios"
import { AlertType, type SetAlertType } from "@/hooks/useAlert"
import displayStandardAxiosErrors from "@/utils/errors"
import type { Project } from "@/utils/types"
import { SupersetImportStatus } from "@/utils/types"

const GET_PROJECTS_ENDPOINT = "project/read_by_user"
const GET_PROJECT_ENDPOINT = "project/"
const CREATE_PROJECT_ENDPOINT = "project"
const DELETE_PROJECT_ENDPOINT = "project/"
const UPDATE_PROJECT_ENDPOINT = "project/"
const CREATE_PROJECT_FROM_TEMPLATE_ENDPOINT = "project/from_template"
const UPLOAD_DASHBOARD_EXPORT_ENDPOINT = "project/"

type ProjectDTO = {
  name: string,
}

type UpdateProjectDTO = {
  project_uuid: string,
  new_name: string,
}

function buildCreateProjectFormData(data: ProjectDTO): FormData {
  const formData = new FormData()
  formData.append("name", data.name)
  return formData
}

function useProjectQuery(project_id: string, enabled: boolean) {
  return useQuery({
    queryKey: [project_id],
    queryFn: async function getProject() {
      const response = await api.get(GET_PROJECT_ENDPOINT + project_id)
      return response.data as Project
    },
    refetchOnWindowFocus: false,
    enabled,
    refetchInterval: (query) => {
      const project = query.state.data as Project | undefined
      if (
        project?.superset_import_status === SupersetImportStatus.PENDING
        || project?.superset_import_status === SupersetImportStatus.IMPORTING
      ) {
        return 3000
      }
      return false
    },
  })
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

function useExportProjectMutation() {
  return useMutation({
    mutationFn: async (projectId: string) => {
      const response = await api.get(`project/${projectId}/export`, {
        responseType: "blob",
      })

      return response
    },
    onSuccess: (response, projectId) => {
      // Create file from response
      const blob = new Blob([response.data], {
        type: "application/x-yaml",
      })

      const url = window.URL.createObjectURL(blob)

      const a = document.createElement("a")
      a.href = url

      // Try to extract filename from header
      const contentDisposition = response.headers["content-disposition"]
      let filename = `${projectId}.yaml`

      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/)
        if (match) filename = match[1]
      }

      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()

      window.URL.revokeObjectURL(url)
    },
  })
}

function useCreateProjectMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function createProject(project: ProjectDTO) {
      const response = await api.post(
        CREATE_PROJECT_ENDPOINT,
        buildCreateProjectFormData(project),
        { headers: { "Content-Type": "multipart/form-data" } }
      )
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
        superset_import_status: SupersetImportStatus.NONE,
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

function buildCreateProjectFromTemplateFormData(
  project: CreateProjectFromTemplateDTO
): FormData {
  const formData = new FormData()
  formData.append("name", project.name)
  formData.append("template_identifier", project.template_identifier)
  return formData
}

function useCreateProjectFromTemplateMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function createProjectFromTemplate(
      project_from_template: CreateProjectFromTemplateDTO
    ) {
      const response = await api.post(
        CREATE_PROJECT_FROM_TEMPLATE_ENDPOINT,
        buildCreateProjectFromTemplateFormData(project_from_template),
        { headers: { "Content-Type": "multipart/form-data" } }
      )
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
        superset_import_status: SupersetImportStatus.NONE,
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

function useUploadDashboardExportMutation(
  projectId: string,
  setAlert: SetAlertType
) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function uploadDashboardExport(file: File) {
      const formData = new FormData()
      formData.append("dashboard_export", file)
      const response = await api.put(
        `${UPLOAD_DASHBOARD_EXPORT_ENDPOINT}${projectId}/dashboard_export`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      )
      return response.data as Project
    },
    onSuccess: (project) => {
      queryClient.setQueryData([projectId], project)
      queryClient.setQueryData([QueryKeys.projects], (oldData: Project[] | undefined) => {
        if (!oldData) return oldData
        return oldData.map((item) => (
          item.uuid === projectId ? { ...item, ...project } : item
        ))
      })
      setAlert("Dashboard export uploaded successfully.", AlertType.SUCCESS)
    },
    onError: (error: AxiosError) => {
      displayStandardAxiosErrors(error, setAlert)
    },
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
  useProjectQuery,
  useProjectsQuery,
  useExportProjectMutation,
  useCreateProjectMutation,
  useUpdateProjectMutation,
  useDeleteProjectMutation,
  useCreateProjectFromTemplateMutation,
  useUploadDashboardExportMutation,
}
