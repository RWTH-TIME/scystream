import { useState } from "react"
import Input from "./inputs/Input"
import Modal, { type ModalProps } from "./Modal"
import LoadingAndError from "./LoadingAndError"
import { useCreateProjectMutation } from "@/mutations/projectMutation"
import { AlertType, useAlert } from "@/hooks/useAlert"
import Button, { ButtonSentiment } from "./Button"

type CreateProjectModalProps = Omit<ModalProps, "children">;

export default function CreateProjectModal({
  isOpen,
  onClose,
  className = "",
}: CreateProjectModalProps) {
  const { setAlert } = useAlert()
  const [projectName, setProjectName] = useState<string>("")

  const { mutate, isPending: loading } = useCreateProjectMutation(setAlert)

  function createProject(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    // TODO: Currently this validation is fine, as we are only using one field.
    // However, think about a better way to validate the fields
    if (projectName.length > 0) {
      mutate({ name: projectName })
      onClose()
    } else {
      setAlert("Project Name must be set.", AlertType.ERROR)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} className={className}>
      <h2 className="text-xl font-bold">Project</h2>
      <form onSubmit={(e) => createProject(e)} className="mt-4 space-y-4 text-sm">
        <div>
          <Input
            type="text"
            value={projectName}
            label="Project Name"
            onChange={setProjectName}
          />
        </div>
        <div className="flex justify-between">
          <Button
            type="button"
            onClick={onClose}
            sentiment={ButtonSentiment.NEUTRAL}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={loading}
            sentiment={ButtonSentiment.POSITIVE}
          >
            <LoadingAndError loading={loading} iconSize={21}>
              Create
            </LoadingAndError>
          </Button>
        </div>
      </form>
    </Modal>
  )
}
