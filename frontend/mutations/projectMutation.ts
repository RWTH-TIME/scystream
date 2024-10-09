import { useQuery } from "@tanstack/react-query"
import { QueryKeys } from "./queryKeys"
import { api } from "@/utils/axios"

// TODO: define the correct endpoint here
const GET_PROJECTS_ENDPOINT = "project/"

function useProjectsQuery() {
  return useQuery({
    queryKey: [QueryKeys.projects],
    queryFn: async function getProjects() {
      const response = await api.get(GET_PROJECTS_ENDPOINT)
      return response.data
    }
  })
}

export {
  useProjectsQuery
}
