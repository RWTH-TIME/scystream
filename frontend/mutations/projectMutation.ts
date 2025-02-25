import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AxiosError } from "axios"
import { v4 as uuidv4 } from "uuid"
import { QueryKeys } from "./queryKeys"
import { api } from "@/utils/axios"
import { AlertType, type SetAlertType } from "@/hooks/useAlert"
import displayStandardAxiosErrors from "@/utils/errors"
import { InputOutputType, type ComputeBlock } from "@/components/CreateComputeBlockModal"

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
        id: uuidv4(),
        name: "Crawl Tagesschau",
        description: "Crawls news articles from Tagesschau",
        custom_name: "crawler-tagesschau",
        author: "Jon Doe",
        image: "ghcr.io/RWTH-TIME/crawler",
        cbc_url: "http://example.com/crawl",
        selected_entrypoint: {
          id: uuidv4(),
          name: "crawl_news",
          description: "Entry point for crawling news",
          inputs: [
            {
              id: uuidv4(),
              type: "input",
              name: "URL Files",
              description: "URLs Files",
              data_type: InputOutputType.FILE,
              config: {
                MINIO_ENDPOINT: "localhost:9000",
                MINIO_PORT: 5432,
              },
            },
          ],
          outputs: [
            {
              id: uuidv4(),
              type: "output",
              name: "Processed Data",
              description: "Processed news articles",
              data_type: InputOutputType.FILE,
              config: {
                MINIO_ENDPOINT: "localhost:9000",
                MINIO_PORT: 5432,
              },
            },
          ],
          envs: {},
        },
      },
    },
    {
      id: "node-2-cb-uuid",
      position: { x: 300, y: 150 },
      type: "computeBlock",
      data: {
        id: uuidv4(),
        name: "Topic Modelling",
        description: "Performs topic modelling on text data",
        custom_name: "topic-model",
        author: "Markus Meilenstein",
        image: "ghcr.io/RWTH-TIME/nlp",
        cbc_url: "http://example.com/nlp",
        selected_entrypoint: {
          id: uuidv4(),
          name: "topic_analysis",
          description: "Entry point for topic modeling",
          inputs: [
            {
              id: uuidv4(),
              type: "input",
              name: "Text Files",
              description: "Input text for topic modeling",
              data_type: InputOutputType.DB,
              config: {
                MINIO_ENDPOINT: "localhost:9000",
                MINIO_PORT: 5432,
              },
            },
          ],
          outputs: [
            {
              id: uuidv4(),
              type: "output",
              name: "Topic Model",
              description: "Generated topic model",
              data_type: InputOutputType.FILE,
              config: {
                MINIO_ENDPOINT: "localhost:9000",
                MINIO_PORT: 5432,
              },
            },
          ],
          envs: {},
        },
      },
    },
  ],
];

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
      return MOCK_DAG_DATA[0]
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
