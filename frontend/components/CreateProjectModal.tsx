import { useState } from "react"
import Input from "./inputs/Input"
import Modal, { type ModalProps } from "./Modal"
import LoadingAndError from "./LoadingAndError"
import { AlertType, useAlert } from "@/hooks/useAlert"
import Button, { ButtonSentiment } from "./Button"

type CreateProjectModalProps = Omit<ModalProps, "children"> & {
  onSubmit: (name: string) => void,
  title?: string,
  loading?: boolean,
}

export const MIN_LEN_PROJECT_NAME = 2

export default function CreateProjectModal({
  isOpen,
  onClose,
  className = "",
  onSubmit,
  title = "Project",
  loading = false,
}: CreateProjectModalProps) {
  const { setAlert } = useAlert()
  const [projectName, setProjectName] = useState<string>("")

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    if (projectName.length >= MIN_LEN_PROJECT_NAME) {
      onSubmit(projectName)
      onClose()
    } else {
      setAlert("Project Name must be set.", AlertType.ERROR)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} className={className}>
      <h2 className="text-xl font-bold">{title}</h2>
      <form onSubmit={handleSubmit} className="mt-4 space-y-4 text-sm">
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
