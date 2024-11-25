import { useState } from "react"
import LoadingAndError from "./LoadingAndError"
import Modal, { type ModalProps } from "./Modal"
import Input from "./inputs/Input"

type CreateComputeBlockModalProps = Omit<ModalProps, "children">;

export default function CreateComputeBlockModal({
  isOpen,
  onClose,
  className = "",
}: CreateComputeBlockModalProps) {
  const [cbName, setCBName] = useState<string>("")
  const [repoURL, setRepoURL] = useState<string>("")

  // TODO: Api Call

  return (
    <Modal className={className} isOpen={isOpen} onClose={onClose}>
      <h2 className="text-xl font-bold">Create Compute Block:</h2>
      <form onSubmit={() => { }} className="mt-4 space-y-4 text-sm">
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
            label="Repository URL"
            onChange={setCBName}
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
            <LoadingAndError loading={false} iconSize={21}>
              Create
            </LoadingAndError>
          </button>
        </div>
      </form>
    </Modal >

  )
}
