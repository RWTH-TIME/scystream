import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import ConfigBox from "@/components/ConfigBox"
import Input from "@/components/inputs/Input"
import { useState } from "react"
import { useAlert } from "@/hooks/useAlert"
import LoadingAndError from "@/components/LoadingAndError"
import DeleteModal from "../DeleteModal"
import { useDeleteComputeBlockMutation } from "@/mutations/computeBlockMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import type { ComputeBlock, RecordValueType } from "../CreateComputeBlockModal"
import Button, { ButtonSentiment } from "../Button"

type MetadataTab = {
  computeBlock: ComputeBlock,
  updateCustomName: (name: string) => void,
  updateConfig: (key: string, value: RecordValueType) => void,
  handleSave: () => void,
  loading: boolean,
}

export default function MetadataTab({
  computeBlock,
  updateCustomName,
  updateConfig,
  handleSave,
  loading
}: MetadataTab) {
  const { selectedComputeBlock } = useSelectedComputeBlock()
  const { selectedProject } = useSelectedProject()
  const { setAlert } = useAlert();
  const { mutateAsync: deleteMutate, isPending: deleteLoading } = useDeleteComputeBlockMutation(setAlert, selectedProject?.uuid)

  const [deleteApproveOpen, setDeleteApproveOpen] = useState(false)

  function onCBDelete() {
    if (selectedComputeBlock) {
      deleteMutate(selectedComputeBlock.id)
      setDeleteApproveOpen(false)
    }
  }

  return (
    <div>
      <DeleteModal
        isOpen={deleteApproveOpen}
        onClose={() => setDeleteApproveOpen(false)}
        onDelete={onCBDelete}
        loading={deleteLoading}
        header="Delete Compute Block"
        desc={`Are you sure you want to delete the Compute Block: ${selectedComputeBlock?.custom_name}`}
      />
      <h2 className="text-xl font-bold">
        Compute Block <span className="text-blue-600">{selectedComputeBlock?.name}</span> Settings:
      </h2>
      <p className="text-sm text-gray-800">{selectedComputeBlock?.description}</p>

      <Input type="text" value={computeBlock.custom_name} label="Name" onChange={updateCustomName} />

      <div className="my-5">
        <ConfigBox
          headline="Envs"
          description="Edit the Compute Blocks Envs here"
          config={computeBlock.selected_entrypoint.envs}
          updateComputeBlock={updateConfig}
        />
      </div>

      <div className="flex justify-between">
        <Button
          onClick={() => setDeleteApproveOpen(true)}
          sentiment={ButtonSentiment.NEGATIVE}
        >
          <LoadingAndError loading={deleteLoading} iconSize={21}>
            Delete
          </LoadingAndError>
        </Button>


        <Button
          onClick={handleSave}
          sentiment={ButtonSentiment.POSITIVE}
        >
          <LoadingAndError loading={loading} iconSize={21}>
            Save
          </LoadingAndError>
        </Button>
      </div>
    </div>
  )
}
