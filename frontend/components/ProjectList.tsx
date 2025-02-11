import type { Dispatch, SetStateAction } from "react"
import LoadingAndError from "./LoadingAndError"
import type { Project } from "@/utils/types"
import { useProjectsQuery } from "@/mutations/projectMutation"

export type ProjectListProps = {
  selectedProject: Project | undefined,
  setSelectedProject: Dispatch<SetStateAction<Project | undefined>>,
}

export default function ProjectList({ selectedProject, setSelectedProject }: ProjectListProps) {
  const { data: projects, isLoading, isError } = useProjectsQuery()

  return (
    <LoadingAndError loading={isLoading} error={isError}>
      <div>
        {
          projects?.map((project: Project) => (
            <li
              key={project.uuid}
              onClick={() => setSelectedProject(project)}
              className={`p-4 rounded-sm flex-grow items-center justify-between relative ${selectedProject?.uuid === project.uuid ? "bg-gray-200" : ""
                } overflow-y-auto hover:bg-gray-100 hover:cursor-pointer`}
            >
              <div>
                <h3 className="text-md">{project.name}</h3>
                <p className="text-sm text-gray-400">{new Date(project.created_at).toLocaleDateString()}</p>
              </div>

              <span className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-[90%] border-b border-gray-300"></span>
            </li>
          ))
        }
      </div>
    </LoadingAndError>
  )
}
