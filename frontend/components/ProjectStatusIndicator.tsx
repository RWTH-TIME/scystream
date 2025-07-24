import { ProjectStatus } from "@/utils/types"
import type { JSX } from "@emotion/react/jsx-runtime"
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline"

export function ProjectStatusIndicator({ s }: { s: ProjectStatus }) {
  const baseClasses =
    "px-6 py-2.5 rounded-full text-xs font-semibold flex items-center space-x-1 w-fit"

  const statusConfig: Record<ProjectStatus, JSX.Element | null> = {
    [ProjectStatus.RUNNING]: (
      <div className={`${baseClasses} bg-green-100 text-green-700 animate-pulse`}>
        <span className="w-2 h-2 bg-green-700 rounded-full" />
        <span>Running</span>
      </div>
    ),
    [ProjectStatus.FINISHED]: (
      <div className={`${baseClasses} bg-blue-100 text-blue-700`}>
        <span className="w-2 h-2 bg-blue-500 rounded-full" />
        <span>Finished</span>
      </div>
    ),
    [ProjectStatus.FAILED]: (
      <div className={`${baseClasses} bg-red-100 text-red-700`}>
        <ErrorOutlineIcon fontSize="small" />
        <span>Failed</span>
      </div>
    ),
    [ProjectStatus.IDLE]: (
      <div className={`${baseClasses} bg-gray-200 text-gray-600`}>
        <span className="w-2 h-2 bg-gray-600 rounded-full" />
        <span>Idle</span>
      </div>
    ),
  }

  return statusConfig[s]
}

