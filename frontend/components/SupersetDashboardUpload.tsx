import { useRef, useState } from "react"
import Button, { ButtonSentiment } from "./Button"
import LoadingAndError from "./LoadingAndError"
import { SupersetImportStatus, type Project } from "@/utils/types"
import { useUploadDashboardExportMutation } from "@/mutations/projectMutation"
import { useAlert } from "@/hooks/useAlert"

type SupersetDashboardUploadProps = {
  project: Project,
}

export default function SupersetDashboardUpload({ project }: SupersetDashboardUploadProps) {
  const { setAlert } = useAlert()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { mutateAsync, isPending } = useUploadDashboardExportMutation(
    project.uuid,
    setAlert
  )

  const hasExport = project.superset_import_status !== SupersetImportStatus.NONE

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null
    setSelectedFile(file)
  }

  async function handleUpload() {
    if (!selectedFile) {
      fileInputRef.current?.click()
      return
    }

    await mutateAsync(selectedFile)
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  return (
    <div className="border rounded p-4 bg-white">
      <p className="text-lg font-semibold mb-1">Superset Dashboard Export</p>
      <p className="text-sm text-gray-600 mb-4">
        Upload a Superset dashboard export zip. It is stored in S3 and imported
        into Superset after the first successful pipeline run. Upload again to
        replace the existing export.
      </p>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">
            Dashboard export (.zip)
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip,application/zip"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-700 file:mr-3 file:py-2 file:px-3 file:rounded file:border-0 file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
          />
          {selectedFile && (
            <p className="mt-1 text-xs text-gray-500">
              Selected: {selectedFile.name}
            </p>
          )}
          {hasExport && !selectedFile && (
            <p className="mt-1 text-xs text-gray-500">
              A dashboard export is already stored for this project.
            </p>
          )}
        </div>

        <Button
          type="button"
          sentiment={ButtonSentiment.POSITIVE}
          onClick={handleUpload}
          disabled={isPending}
        >
          <LoadingAndError loading={isPending} iconSize={18}>
            {hasExport ? "Update export" : "Upload export"}
          </LoadingAndError>
        </Button>
      </div>
    </div>
  )

}
