import { useRef, useState } from "react"
import { OpenInNew } from "@mui/icons-material"
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
  const isPendingImport =
    project.superset_import_status === SupersetImportStatus.PENDING
    || project.superset_import_status === SupersetImportStatus.IMPORTING
  const isImported =
    project.superset_import_status === SupersetImportStatus.IMPORTED
    && project.superset_dashboard_url
  const isFailed = project.superset_import_status === SupersetImportStatus.FAILED

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
    <div className="p-4 border rounded relative">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="text-lg font-semibold">Superset Dashboard</h3>
          <p className="text-gray-700">
            Upload a Superset dashboard export zip. It is stored in S3 and imported
            into Superset after the first successful pipeline run. Upload again to
            replace the existing export.
          </p>
        </div>
        {isImported && (
          <Button
            type="button"
            sentiment={ButtonSentiment.POSITIVE}
            onClick={() => window.open(project.superset_dashboard_url!, "_blank")}
          >
            <span className="inline-flex items-center gap-1">
              <OpenInNew fontSize="small" />
              Open Dashboard
            </span>
          </Button>
        )}
      </div>

      {isPendingImport && (
        <p className="mb-4 text-sm text-gray-600">
          Dashboard will be available after the first successful run.
        </p>
      )}

      {isFailed && (
        <p className="mb-4 text-sm text-red-600">
          Dashboard import failed
          {project.superset_import_error ? `: ${project.superset_import_error}` : ""}
        </p>
      )}

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
