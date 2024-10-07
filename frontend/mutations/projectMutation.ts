import { useQuery } from "@tanstack/react-query"
import { api } from "@/utils/axios"
import { getConfig } from "@/utils/config"
import { QueryKeys } from "./queryKeys"

// TODO: define the correct endpoint here
const GET_PROJECTS_ENDPOINT = "project/"

function useProjectsQuery() {
  return useQuery({
    queryKey: [QueryKeys.projects],
    queryFn: async function getProjects() {
      const response = await api.get(GET_PROJECTS_ENDPOINT)
      return response.data
    },
    onError: (error) => {
      console.error(`Getting all projects failed ${error}`)
    },
  })
}

export {
  useProjectsQuery
}
