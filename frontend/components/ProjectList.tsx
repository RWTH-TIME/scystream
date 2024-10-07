import { v4 as uuidv4 } from "uuid"
import type { Project } from "@/utils/types"
import { useProjectsQuery } from "@/mutations/projectMutation"

// TODO: remove
const dummyProjects: Project[] = [
  {
    uuid: uuidv4(),
    name: "Projekt 1 - Das ist ein Name",
    created_at: new Date()
  },
  {
    uuid: uuidv4(),
    name: "Was ist Scystream?",
    created_at: new Date()
  },
  {
    uuid: uuidv4(),
    name: "Downloader",
    created_at: new Date()
  },
]

export type ProjectListProps = {
  selectedProject: Project | undefined,
  setSelectedProject: (value: Project | undefined) => void
}

export default function ProjectList({ selectedProject, setSelectedProject }: ProjectListProps) {
  const { data: projects, isLoading, isError } = useProjectsQuery()

  // TODO: handle error instead of displaying dummyProjects
  const renderedProjects: Project[] = isError ? dummyProjects : projects as Project[]

  // TODO: find a more generic way of handling the load state
  if (isLoading) {
    return <p>Loading</p>
  }

  return (
    <div className="shadow h-full">
      {
        renderedProjects.map((project: Project) => (
          <li
            key={project.uuid}
            onClick={() => setSelectedProject(project)}
            className={`p-4 rounded-sm flex-grow items-center justify-between relative ${selectedProject?.uuid === project.uuid ? "bg-gray-200" : ""
              } overflow-y-auto hover:bg-gray-100`}
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
  )
}
