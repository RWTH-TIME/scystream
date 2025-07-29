// FileUploadModal.tsx
import { useState } from "react"
import FileInput from "./inputs/FileInput"
import Button, { ButtonSentiment } from "./Button"
import type { InputOutput } from "./CreateComputeBlockModal"
import Modal from "./Modal"

type FileUploadModalProps = {
  isOpen: boolean,
  onClose: () => void,
  io: InputOutput,
  existingFile?: File,
  onConfirm: (file: File | null) => void,
};

export default function FileUploadModal({
  isOpen,
  onClose,
  io,
  existingFile,
  onConfirm,
}: FileUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(existingFile ?? null)

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <h2 className="text-xl font-bold">{io.name}</h2>
      {io.description}
      <div className="flex flex-col justify-between mt-5">
        <FileInput
          id="modal_file_input"
          label="Select a file to upload"
          onChange={(e) => {
            const file = e.target.files?.[0] || null
            setSelectedFile(file)
          }}
        />

        {selectedFile && (
          <div className="text-sm text-gray-800">
            Selected: <strong>{selectedFile.name}</strong>
            <button
              className="ml-2 text-red-600 text-xs underline"
              onClick={() => setSelectedFile(null)}
            >
              Remove
            </button>
          </div>
        )}

        <div className="flex justify-end space-x-2 pt-4">
          <Button onClick={onClose} sentiment={ButtonSentiment.NEUTRAL}>Cancel</Button>
          <Button
            onClick={() => {
              onConfirm(selectedFile)
              onClose()
            }}
            sentiment={ButtonSentiment.POSITIVE}
          >
            Save
          </Button>
        </div>
      </div>
    </Modal >
  )
}

