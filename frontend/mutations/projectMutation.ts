import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { v4 as uuidv4 } from "uuid"
import { QueryKeys } from "./queryKeys"
import { api } from "@/utils/axios"
import { AlertType, type SetAlertType } from "@/hooks/useAlert"
import displayStandardAxiosErrors from "@/utils/errors"
import { InputTypes } from "@/components/nodes/ComputeBlockNode"
import type { ComputeBlock } from "@/components/nodes/ComputeBlockNode"

const GET_PROJECTS_ENDPOINT = "project/read_all"
const CREATE_PROJECT_ENDPOINT = "project"
// TODO: const GET_PROJECT_DETAILS_ENDPOINT = "project/get_dag"
const DELETE_PROJECT_ENDPOINT = "project/"
const UPDATE_PROJECT_ENDPOINT = "project/"

export type Node = {
  id: string,
  position: { x: number, y: number },
  type: string,
  data: ComputeBlock,
}


// TODO: How do we handle updates of the compute blocks?
// selectedEntrypoint can be undefined theoretically (for new blocks only)
// Inputs Outputs can be undefeined (for new block only)
const MOCK_DAG_DATA: Node[][] = [
  [
    {
      id: "node-1-cb-uuid",
      position: { x: 250, y: 5 },
      type: "computeBlock",
      data: {
        uuid: uuidv4(),
        name: "Crawl Tagesschau",
        selectedEntrypoint: "crawl_tagesschau",
        author: "Jon Doe",
        dockerImage: "ghcr.io/RWTH-TIME/crawler",
        inputs: [
          {
            description: "URLs Files",
            type: InputTypes.FILE,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
        ],
        outputs: [
          {
            description: "Processed Data",
            type: InputTypes.FILE,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
          {
            description: "Processed Data",
            type: InputTypes.DB,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
          {
            description: "Processed Data",
            type: InputTypes.DB,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
        ],
      },
    },
    {
      id: "node-2-cb-uuid",
      position: { x: 300, y: 150 },
      type: "computeBlock",
      data: {
        uuid: uuidv4(),
        name: "Topic Modelling",
        selectedEntrypoint: "topic_modelling",
        author: "Markus Meilenstein",
        dockerImage: "ghcr.io/RWTH-TIME/nlp",
        inputs: [
          {
            description: "Text Files",
            type: InputTypes.DB,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
        ],
        outputs: [
          {
            description: "Topic Model",
            type: InputTypes.FILE,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
        ],
      },
    },
  ],
  [
    {
      id: "node-1-cb-uuid",
      position: { x: 0, y: 0 },
      type: "computeBlock",
      data: {
        uuid: uuidv4(),
        name: "Crawl Tagesschau",
        selectedEntrypoint: "crawl_tagesschau",
        author: "Jon Doe",
        dockerImage: "ghcr.io/RWTH-TIME/crawler",
        inputs: [
          {
            description: "URLs Files",
            type: InputTypes.FILE,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
        ],
        outputs: [
          {
            description: "Processed Data",
            type: InputTypes.FILE,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
          {
            description: "Processed Data",
            type: InputTypes.DB,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
          {
            description: "Processed Data",
            type: InputTypes.DB,
            config: {
              MINIO_ENDPOINT: "localhost:9000",
              MINIO_PORT: 5432,
            },
          },
        ],
      },
    },
  ]
]

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

function useUpdateProjectMutation(setAlert: SetAlertType) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async function updateProject(project: UpdateProjectDTO) {
      const response = await api.put(UPDATE_PROJECT_ENDPOINT, JSON.stringify(project))
      return response.data.project_uudi
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

// TODO id here right?
function useProjectDetailsQuery(id: string | undefined) {
  return useQuery({
    queryKey: [id],
    queryFn: async function getProjects() {
      /* TODO:
      const response = await api.get(GET_PROJECT_DETAILS_ENDPOINT)
      return response.data
      */
      return MOCK_DAG_DATA[Math.random() < 0.5 ? 1 : 0]
    },
    enabled: !!id
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
  useProjectDetailsQuery,
  useDeleteProjectMutation,
}
