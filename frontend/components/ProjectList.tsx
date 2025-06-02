import { useState } from "react"
import AddIcon from "@mui/icons-material/Add"
import LoadingAndError from "./LoadingAndError"
import CreateProjectModal from "./CreateProjectModal"
import { ProjectStatus, type Project } from "@/utils/types"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import { ProjectStatusIndicator } from "./ProjectStatusIndicator"
import { useProjectsQuery } from "@/mutations/projectMutation"
import { useRouter } from "next/navigation"
import { useAlert } from "@/hooks/useAlert"
import { useCreateProjectMutation } from "@/mutations/projectMutation"

export default function ProjectList() {
  const { setAlert } = useAlert()
  const router = useRouter()

  const [createProjectOpen, setCreateProjectOpen] = useState<boolean>(false)
  const { setSelectedComputeBlock } = useSelectedComputeBlock()

  const { data: projects, isLoading, isError } = useProjectsQuery()
  const { mutate: createProjectMutate, isPending: loading } = useCreateProjectMutation(setAlert)


  return (
    <LoadingAndError loading={isLoading} error={isError}>
      <div className="space-y-2 pr-2">
        <div
          className="p-3 rounded-sm flex-grow items-center justify-between relative overflow-y-auto bg-gray-100 hover:bg-gray-200 hover:cursor-pointer"
          onClick={() => setCreateProjectOpen(true)}
        >
          <AddIcon /> Add Project
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {projects?.map((project: Project) => (
            <div
              key={project.uuid}
              onClick={() => {
                setSelectedComputeBlock(undefined)
                router.push(`/dashboard/project/${project.uuid}`)
              }}
              className="rounded-sm border border-gray-200  p-4 bg-white flex justify-between items-center transition-colors duration-200 hover:bg-gray-50 cursor-pointer"
            >
              <div>
                <h3 className="text-lg font-bold">{project.name}</h3>
                <p className="text-sm text-gray-500">
                  Created on {new Date(project.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex-shrink-0">
                <ProjectStatusIndicator s={project.status ?? ProjectStatus.IDLE} />
              </div>
            </div>
          ))}
        </div>
      </div>
      <CreateProjectModal
        isOpen={createProjectOpen}
        onClose={() => setCreateProjectOpen(false)}
        title="Create Project"
        loading={loading}
        onSubmit={(name) => createProjectMutate({ name })}
      />
    </LoadingAndError>
  )
}
