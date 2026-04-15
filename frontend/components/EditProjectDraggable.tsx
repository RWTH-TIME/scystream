import { useState } from "react"
import Input from "./inputs/Input"
import LoadingAndError from "./LoadingAndError"
import ProjectCBSettingsDraggable from "./ProjectCBSettingsDraggable"
import { useUpdateProjectMutation } from "@/mutations/projectMutation"
import { AlertType, useAlert } from "@/hooks/useAlert"
import { MIN_LEN_PROJECT_NAME } from "./CreateProjectModal"
import type { Project } from "@/utils/types"

const TABS = [
  { key: "metadata", label: "Metadata" },
]


type EditProjectDraggableProps = {
  project: Project,
}

export default function EditProjectDraggable({ project }: EditProjectDraggableProps) {
  const { setAlert } = useAlert()
  const [projectName, setProjectName] = useState<string>(project.name)
  const [activeTab, setActiveTab] = useState<string>("metadata") // Single tab for now

  const { mutate, isPending: loading } = useUpdateProjectMutation(setAlert)

  function updateProject(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    if (!projectName || projectName.length < MIN_LEN_PROJECT_NAME) {
      setAlert(`Project Name must be at least ${MIN_LEN_PROJECT_NAME} characters long!`, AlertType.ERROR)
      return
    }

    mutate({ project_uuid: project.uuid, new_name: projectName })
    // TODO: update the name then in the page (or invalidate the query)
  }

  return (
    <ProjectCBSettingsDraggable tabs={TABS} activeTab="metadata" setActiveTab={setActiveTab}>
      <div className="p-4">
        {activeTab === "metadata" && (
          <>
            <h2 className="text-xl font-bold">
              Project <span className="text-blue-600">{project.name}</span> Settings:
            </h2>
            <form onSubmit={(e) => updateProject(e)} className="mt-4 space-y-4 text-sm">
              <div>
                <Input
                  type="text"
                  value={projectName}
                  label="Project Name"
                  onChange={setProjectName}
                />
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-blue-500 rounded hover:bg-blue-600"
                  disabled={loading}
                >
                  <LoadingAndError loading={loading} iconSize={21}>
                    Save
                  </LoadingAndError>
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </ProjectCBSettingsDraggable>
  )
}
