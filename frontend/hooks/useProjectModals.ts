import { useState } from "react"

type UseProjectModalsProps = {
  deleteProject: (project_id: string) => void
  project_uuid: string
}

export function useProjectModals({ deleteProject, project_uuid }: UseProjectModalsProps) {
  const [deleteApproveOpen, setDeleteApproveOpen] = useState(false)
  const [shareModalOpen, setShareModalOpen] = useState(false)

  function onProjectDelete() {
    deleteProject(project_uuid)
    setDeleteApproveOpen(false)
  }

  return {
    deleteApproveOpen,
    setDeleteApproveOpen,
    shareModalOpen,
    setShareModalOpen,
    onProjectDelete,
  }
}

