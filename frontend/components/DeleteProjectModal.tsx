import LoadingAndError from "./LoadingAndError"
import Modal, { type ModalProps } from "./Modal"
import { useDeleteProjectMutation } from "@/mutations/projectMutation"
import { useAlert } from "@/hooks/useAlert"
import { useSelectedProject } from "@/hooks/useSelectedProject"

type DeleteProjectModalProps = Omit<ModalProps, "children">;

export default function DeleteProjectModal({
  isOpen,
  onClose,
  className = "",
}: DeleteProjectModalProps) {
  const { setAlert } = useAlert()
  const { selectedProject, setSelectedProject } = useSelectedProject()

  const { mutate: deleteMutate, isPending: deleteLoading } = useDeleteProjectMutation(setAlert)

  function onDelete() {
    if (selectedProject) {
      deleteMutate(selectedProject.uuid)
      onClose()
      setSelectedProject(undefined)
    }
  }

  return (
    <Modal className={className} isOpen={isOpen} onClose={onClose}>
      <h2 className="text-xl font-bold">Delete Project</h2>
      Are you sure that you want to delete the project: <span className="text-blue-600"><b>{selectedProject?.name}</b></span>
      <div className="flex justify-end mt-5">
        <button
          type="button"
          onClick={onClose}
          className="w-[78px] h-[36px] px-4 py-2 mr-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
        >
          Cancel
        </button>
        <button
          className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-red-500 rounded hover:bg-red-600"
          disabled={deleteLoading}
          onClick={() => onDelete()}
        >
          <LoadingAndError loading={deleteLoading} iconSize={21}>
            Delete
          </LoadingAndError>
        </button>
      </div>

    </Modal>

  )
}
