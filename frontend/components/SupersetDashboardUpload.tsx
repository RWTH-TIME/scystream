import { useRef, useState } from "react"
import { Download, OpenInNew, Sync } from "@mui/icons-material"
import Button, { ButtonSentiment } from "./Button"
import LoadingAndError from "./LoadingAndError"
import { SupersetImportStatus, type Project } from "@/utils/types"
import {
  useDownloadSupersetTemplateMutation,
  useOpenSupersetDashboardMutation,
  useSyncSupersetMutation,
  useUploadDashboardExportMutation
} from "@/mutations/projectMutation"
import { useAlert } from "@/hooks/useAlert"

type SupersetDashboardUploadProps = {
  project: Project,
}

/**
 * The Superset visualization of a project: after each successful run all
 * tables the workflow wrote are available as datasets in Superset and shown
 * on the project dashboard. The dashboard is built from the uploaded
 * visualization template (a Superset dashboard export) or, without one, a
 * standard dashboard with a table per dataset.
 */
export default function SupersetDashboardUpload({ project }: SupersetDashboardUploadProps) {
  const { setAlert } = useAlert()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const upload = useUploadDashboardExportMutation(project.uuid, setAlert)
  const openDashboard = useOpenSupersetDashboardMutation(project.uuid, setAlert)
  const sync = useSyncSupersetMutation(project.uuid, setAlert)
  const downloadTemplate = useDownloadSupersetTemplateMutation(project.uuid, setAlert)

  const status = project.superset_import_status
  const hasTemplate = !!project.has_superset_template
  const isWaiting = status === SupersetImportStatus.PENDING
  const isSyncing = status === SupersetImportStatus.IMPORTING
  const hasDashboard = !!project.superset_dashboard_url
  const isFailed = status === SupersetImportStatus.FAILED

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null)
  }

  async function handleUpload() {
    if (!selectedFile) {
      fileInputRef.current?.click()
      return
    }

    await upload.mutateAsync(selectedFile)
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  return (
    <div className="p-4 border rounded relative">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="text-lg font-semibold">Superset visualization</h3>
          <p className="text-gray-700">
            After every successful run, all tables the workflow wrote are available
            in Superset and shown on the project dashboard. Upload a Superset
            dashboard export to use it as visualization template, otherwise a
            standard dashboard with a table per dataset is created.
          </p>
        </div>
        <div className="flex flex-col gap-2 shrink-0">
          <Button
            type="button"
            sentiment={ButtonSentiment.POSITIVE}
            onClick={() => openDashboard.mutate()}
            disabled={!hasDashboard || openDashboard.isPending}
            title={hasDashboard ? "Opens the dashboard, shared with your account" : "Available after the first successful run"}
          >
            <LoadingAndError loading={openDashboard.isPending} iconSize={18}>
              <span className="inline-flex items-center gap-1">
                <OpenInNew fontSize="small" />
                Open dashboard
              </span>
            </LoadingAndError>
          </Button>
          <Button
            type="button"
            sentiment={ButtonSentiment.NEUTRAL}
            onClick={() => sync.mutate()}
            disabled={sync.isPending || isSyncing}
            title="Update the Superset datasets and dashboard with the current data"
          >
            <LoadingAndError loading={sync.isPending || isSyncing} iconSize={18}>
              <span className="inline-flex items-center gap-1">
                <Sync fontSize="small" />
                Sync now
              </span>
            </LoadingAndError>
          </Button>
          <Button
            type="button"
            sentiment={ButtonSentiment.NEUTRAL}
            onClick={() => downloadTemplate.mutate()}
            disabled={(!hasDashboard && !hasTemplate) || downloadTemplate.isPending}
            title="Download the dashboard as template for other projects"
          >
            <LoadingAndError loading={downloadTemplate.isPending} iconSize={18}>
              <span className="inline-flex items-center gap-1">
                <Download fontSize="small" />
                Download template
              </span>
            </LoadingAndError>
          </Button>
        </div>
      </div>

      {isWaiting && (
        <p className="mb-4 text-sm text-gray-600">
          The visualization template is applied after the next successful run.
        </p>
      )}

      {isFailed && (
        <p className="mb-4 text-sm text-red-600">
          Syncing with Superset failed
          {project.superset_import_error ? `: ${project.superset_import_error}` : ""}
        </p>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">
            Visualization template (Superset dashboard export, .zip or .tar.gz)
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip,.tar.gz,.tgz,application/zip,application/gzip"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-700 file:mr-3 file:py-2 file:px-3 file:rounded file:border-0 file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
          />
          {selectedFile && (
            <p className="mt-1 text-xs text-gray-500">
              Selected: {selectedFile.name}
            </p>
          )}
          {hasTemplate && !selectedFile && (
            <p className="mt-1 text-xs text-gray-500">
              This project uses a visualization template.
            </p>
          )}
        </div>

        <Button
          type="button"
          sentiment={ButtonSentiment.POSITIVE}
          onClick={handleUpload}
          disabled={upload.isPending}
        >
          <LoadingAndError loading={upload.isPending} iconSize={18}>
            {hasTemplate ? "Replace template" : "Upload template"}
          </LoadingAndError>
        </Button>
      </div>
    </div>
  )
}
