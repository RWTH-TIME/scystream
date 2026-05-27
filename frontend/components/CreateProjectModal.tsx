import { useState } from "react"
import Input from "./inputs/Input"
import Modal, { type ModalProps } from "./Modal"
import LoadingAndError from "./LoadingAndError"
import { AlertType, useAlert } from "@/hooks/useAlert"
import Button, { ButtonSentiment } from "./Button"

type CreateProjectModalProps = Omit<ModalProps, "children"> & {
  onSubmit: (name: string, dashboardExport?: File | null) => void,
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
  const [dashboardExport, setDashboardExport] = useState<File | null>(null)

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    if (projectName.length >= MIN_LEN_PROJECT_NAME) {
      onSubmit(projectName, dashboardExport)
      setProjectName("")
      setDashboardExport(null)
      onClose()
    } else {
      setAlert("Project Name must be set.", AlertType.ERROR)
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null
    if (file && !file.name.toLowerCase().endsWith(".zip")) {
      setAlert("Dashboard export must be a .zip file.", AlertType.ERROR)
      e.target.value = ""
      setDashboardExport(null)
      return
    }
    setDashboardExport(file)
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} className={className}>
      <h2 className="text-xl font-bold">{title}</h2>
      <form onSubmit={handleSubmit} className="mt-4 space-y-4 text-sm">
        <div>
          <Input
            type="text"
            value={projectName}
            label="Project Name (max 30 chars)"
            onChange={setProjectName}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">
            Superset dashboard export (.zip, optional)
          </label>
          <input
            type="file"
            accept=".zip,application/zip"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-700 file:mr-3 file:py-2 file:px-3 file:rounded file:border-0 file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
          />
          {dashboardExport && (
            <p className="mt-1 text-xs text-gray-500">{dashboardExport.name}</p>
          )}
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
