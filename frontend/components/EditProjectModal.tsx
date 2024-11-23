import { useState } from "react"
import Input from "./inputs/Input"
import Modal, { type ModalProps } from "./Modal"
import LoadingAndError from "./LoadingAndError"
import { useUpdateProjectMutation } from "@/mutations/projectMutation"
import { AlertType, useAlert } from "@/hooks/useAlert"
import { useSelectedProject } from "@/hooks/useSelectedProject"

type EditProjectModalProps = Omit<ModalProps, "children">;

export default function EditProjectModal({
  isOpen,
  onClose,
  className = "",
}: EditProjectModalProps) {
  const { setAlert } = useAlert()
  const { selectedProject } = useSelectedProject()
  const [projectName, setProjectName] = useState<string>(selectedProject?.name ?? "")

  const { mutate, isPending: loading } = useUpdateProjectMutation(setAlert)

  function updateProject(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    // TODO: Currently this validation is fine, as we are only using one field.
    // However, think about a better way to validate the fields
    if (selectedProject && projectName && projectName.length > 0) {
      mutate({ project_uuid: selectedProject.uuid, new_name: projectName })
      onClose()
    } else {
      setAlert("Project Name must be set.", AlertType.ERROR)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} className={className}>
      <h2 className="text-xl font-bold">Update Project</h2>
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
            type="button"
            onClick={onClose}
            className="w-[78px] h-[36px] px-4 py-2 mr-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-blue-500 rounded hover:bg-blue-600"
            disabled={loading}
          >
            <LoadingAndError loading={loading} iconSize={21}>
              Edit
            </LoadingAndError>
          </button>
        </div>
      </form>
    </Modal>
  )
}
