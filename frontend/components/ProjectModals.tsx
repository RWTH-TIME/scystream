import { useAlert } from "@/hooks/useAlert"
import DeleteModal from "./DeleteModal"
import ShareModal from "./ShareModal"
import type { Project } from "@/utils/types"

import { useGenerateInviteLinkMutation } from "@/mutations/shareMutations"

type ProjectModalsProps = {
  project: Project
  deleteApproveOpen: boolean
  setDeleteApproveOpen: (open: boolean) => void
  shareModalOpen: boolean
  setShareModalOpen: (open: boolean) => void
  onProjectDelete: () => void
  isProjectDeleteLoading: boolean
}

export default function ProjectModals({
  project,
  deleteApproveOpen,
  setDeleteApproveOpen,
  shareModalOpen,
  setShareModalOpen,
  onProjectDelete,
  isProjectDeleteLoading,
}: ProjectModalsProps) {
  const { setAlert } = useAlert()

  const generateInviteMutation = useGenerateInviteLinkMutation(setAlert)

  return (
    <>
      <ShareModal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        onGenerateTemplateLink={() => new Promise((resolve) => resolve("test"))}
        onGenerateInviteLink={async () => {
          return await generateInviteMutation.mutateAsync(project.uuid)
        }}
      />
      <DeleteModal
        isOpen={deleteApproveOpen}
        onClose={() => setDeleteApproveOpen(false)}
        onDelete={onProjectDelete}
        loading={isProjectDeleteLoading}
        header="Delete Project"
        desc={`Are you sure you want to delete the project: ${project.name}?`}
      />
    </>
  )
}
