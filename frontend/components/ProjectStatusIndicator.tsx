import { ProjectStatus } from "@/utils/types"
import type { JSX } from "@emotion/react/jsx-runtime"
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline"

export function ProjectStatusIndicator({ s }: { s: ProjectStatus }) {
  const statusConfig: Record<ProjectStatus, JSX.Element | null> = {
    [ProjectStatus.RUNNING]: (
      <div className="flex space-x-1 items-center justify-center">
        {[0, 150, 300].map((delay) => (
          <div
            key={delay}
            className="w-1.5 h-1.5 rounded-full bg-green-700 animate-bounce"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
    ),
    [ProjectStatus.FINISHED]: <div className="w-2 h-2 bg-blue-500" />,
    [ProjectStatus.FAILED]: (
      <div className="text-red-500 flex items-center justify-center w-2 h-2">
        <ErrorOutlineIcon fontSize="small" />
      </div>
    ),
    [ProjectStatus.IDLE]: null
  }

  return statusConfig[s] || null
}

