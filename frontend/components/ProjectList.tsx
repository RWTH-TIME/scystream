import { useState } from "react"
import AddIcon from "@mui/icons-material/Add"
import LoadingAndError from "./LoadingAndError"
import CreateProjectModal from "./CreateProjectModal"
import { ProjectStatus, type Project } from "@/utils/types"
import { useProjectsQuery } from "@/mutations/projectMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import { useProjectStatusWS } from "@/mutations/workflowMutations"
import { useAlert } from "@/hooks/useAlert"
import { ProjectStatusIndicator } from "./ProjectStatusIndicator"


export default function ProjectList() {
  const [createProjectOpen, setCreateProjectOpen] = useState<boolean>(false)
  const { selectedProject, setSelectedProject } = useSelectedProject()
  const { setSelectedComputeBlock } = useSelectedComputeBlock()
  const { data: projects, isLoading, isError } = useProjectsQuery()
  const { setAlert } = useAlert()

  useProjectStatusWS(setAlert)

  return (
    <LoadingAndError loading={isLoading} error={isError}>
      <div>
        <div
          className="p-4 rounded-sm flex-grow items-center justify-between relative overflow-y-auto bg-gray-100 hover:bg-gray-200 hover:cursor-pointer"
          onClick={() => setCreateProjectOpen(true)}
        >
          <AddIcon /> Add Project
        </div>
        {
          projects?.map((project: Project) => (
            <li
              key={project.uuid}
              onClick={() => {
                setSelectedProject(project)
                setSelectedComputeBlock(undefined)
              }}
              className={`p-4 rounded-sm flex flex-grow items-center justify-between relative ${selectedProject?.uuid === project.uuid ? "bg-gray-200" : ""
                } overflow-y-auto hover:bg-gray-100 hover:cursor-pointer`}
            >
              <div>
                <h3 className="text-md">{project.name}</h3>
                <p className="text-sm text-gray-400">{new Date(project.created_at).toLocaleDateString()}</p>
              </div>
              <div className="flex items-center space-x-2">
                <ProjectStatusIndicator s={project.status ?? ProjectStatus.IDLE} />
              </div>

              <span className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-[90%] border-b border-gray-300"></span>
            </li>
          ))
        }
      </div>
      <CreateProjectModal
        isOpen={createProjectOpen}
        onClose={() => setCreateProjectOpen(false)}
      >
      </CreateProjectModal>
    </LoadingAndError >
  )
}
