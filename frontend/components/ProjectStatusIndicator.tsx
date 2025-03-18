import { ProjectStatus } from "@/utils/types"
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline"

export function ProjectStatusIndicator({ s }: { s: ProjectStatus }) {
  if (s === ProjectStatus.RUNNING) {
    return (
      <div className="flex space-x-1 items-center justify-center">
        <div className="w-1.5 h-1.5 rounded-full bg-green-700 animate-bounce" />
        <div className="w-1.5 h-1.5 rounded-full bg-green-700 animate-bounce delay-150" />
        <div className="w-1.5 h-1.5 rounded-full bg-green-700 animate-bounce delay-300" />
      </div>
    )
  }

  if (s === ProjectStatus.FINISHED) {
    return <div className="w-2 h-2 bg-blue-500" />
  }

  if (s === ProjectStatus.FAILED) {
    return (
      <div className="text-red-500 flex items-center justify-center w-2 h-2">
        <ErrorOutlineIcon fontSize="small" />
      </div>
    )
  }

  return null
}

