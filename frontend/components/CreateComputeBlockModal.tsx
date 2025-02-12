import { useState } from "react"
import LoadingAndError from "./LoadingAndError"
import Modal, { type ModalProps } from "./Modal"
import Input from "./inputs/Input"
import { useCreateComputeBlockMutation } from "@/mutations/computeBlockMutation";
import { AlertType, useAlert } from "@/hooks/useAlert";

type CreateComputeBlockModalProps = Omit<ModalProps, "children">;

export default function CreateComputeBlockModal({
  isOpen,
  onClose,
  className = "",
}: CreateComputeBlockModalProps) {
  const { setAlert } = useAlert()
  const [cbName, setCBName] = useState<string>("")
  const [repoURL, setRepoURL] = useState<string>("")

  const { mutate, isPending: loading } = useCreateComputeBlockMutation(setAlert)

  function createComputeBlock(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    // TODO: Validation
    if (cbName.length > 0 && repoURL.length > 0) {
      mutate({ compute_block_title: cbName, cbc_url: repoURL })
      onClose()
    } else {
      setAlert("Compute Block Name and Repo URL must be set.", AlertType.ERROR)
    }
  }

  return (
    <Modal className={className} isOpen={isOpen} onClose={onClose}>
      <h2 className="text-xl font-bold">Create Compute Block:</h2>
      <form onSubmit={(e) => { createComputeBlock(e) }} className="mt-4 space-y-4 text-sm">
        <div>
          <Input
            type="text"
            value={cbName}
            label="Compute Block Title"
            onChange={setCBName}
          />
          <Input
            type="text"
            value={repoURL}
            label="Compute Block Config URL"
            onChange={setRepoURL}
          />
        </div>
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="w-[78px] h-[36px] px-4 py-2 mr-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-blue-500 rounded hover:bg-blue-600"
            disabled={false}
          >
            <LoadingAndError loading={loading} iconSize={21}>
              Create
            </LoadingAndError>
          </button>
        </div>
      </form>
    </Modal >

  )
}
