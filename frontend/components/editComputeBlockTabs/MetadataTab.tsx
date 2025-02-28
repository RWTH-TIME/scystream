import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import ConfigBox from "@/components/ConfigBox"
import Input from "@/components/inputs/Input"
import { useEffect, useState } from "react"
import { AlertType, useAlert } from "@/hooks/useAlert"
import LoadingAndError from "@/components/LoadingAndError"
import DeleteModal from "../DeleteModal"
import { useDeleteComputeBlockMutation } from "@/mutations/computeBlockMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"

export default function MetadataTab() {
  const { selectedComputeBlock } = useSelectedComputeBlock()
  const { selectedProject } = useSelectedProject()
  const { setAlert } = useAlert();
  const { mutateAsync: deleteMutate, isPending: deleteLoading } = useDeleteComputeBlockMutation(setAlert, selectedProject?.uuid)

  const [cbName, setCBName] = useState<string>(selectedComputeBlock?.custom_name ?? "");
  const [deleteApproveOpen, setDeleteApproveOpen] = useState(false)

  useEffect(() => {
    setCBName(selectedComputeBlock?.custom_name ?? "");
  }, [selectedComputeBlock]);

  function updateProject(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (selectedComputeBlock && cbName && cbName.length > 0) {
      // TODO: mutate
    } else {
      setAlert("Project Name must be set.", AlertType.ERROR);
    }
  }

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

      <form onSubmit={updateProject} className="mt-4 space-y-4 text-sm">
        <Input type="text" value={cbName} label="Name" onChange={setCBName} />

        <div className="flex justify-between">
          <button
            onClick={() => setDeleteApproveOpen(true)}
            type="submit"
            className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-red-500 rounded hover:bg-red-600"
          >
            <LoadingAndError loading={false} iconSize={21}>
              Delete
            </LoadingAndError>
          </button>


          <button
            type="submit"
            className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-blue-500 rounded hover:bg-blue-600"
          >
            <LoadingAndError loading={false} iconSize={21}>
              Save
            </LoadingAndError>
          </button>
        </div>
      </form>
    </div>
  )
}
