import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { QueryKeys } from "./queryKeys"
import { api } from "@/utils/axios"
import type { SetAlertType } from "@/hooks/useAlert"
import displayStandardAxiosErrors from "@/utils/errors"
import { InputTypes } from "@/components/nodes/ComputeBlockNode"
import type { ComputeBlock } from "@/components/nodes/ComputeBlockNode"

const GET_PROJECTS_ENDPOINT = "project/read_all"
const CREATE_PROJECT_ENDPOINT = "project"
// TODO: const GET_PROJECT_DETAILS_ENDPOINT = "project/get_dag"

export type Node = {
  id: string,
  position: { x: number, y: number },
  type: string,
  data: ComputeBlock
}

const MOCK_DAG_DATA: Node[][] = [
  [
    {
      id: "node-1-cb-uuid",
      position: { x: 0, y: 0 },
      type: "computeBlock",
      data: {
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
      position: { x: 100, y: 100 },
      type: "computeBlock",
      data: {
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

function useProjectDetailsQuery(id: string) {
  return useQuery({
    queryKey: [id],
    queryFn: async function getProjects() {
      /* TODO:
      const response = await api.get(GET_PROJECT_DETAILS_ENDPOINT)
      return response.data
      */
      return MOCK_DAG_DATA[Math.random() < 0.5 ? 1 : 0]
    }
  })
}

export {
  useProjectsQuery,
  useCreateProjectMutation,
  useProjectDetailsQuery
}
