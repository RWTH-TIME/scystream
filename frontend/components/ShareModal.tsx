import { useState } from "react"
import Button, { ButtonSentiment } from "./Button"
import LoadingAndError from "./LoadingAndError"
import Modal, { type ModalProps } from "./Modal"

type ShareMode = "template" | "collaborate"

type ShareModalProps = Omit<ModalProps, "children"> & {
  onGenerateTemplateLink: () => Promise<string>,
  onGenerateInviteLink: () => Promise<string>,
}

export default function ShareModal({
  isOpen,
  onClose,
  className = "",
  onGenerateTemplateLink,
  onGenerateInviteLink
}: ShareModalProps) {

  const [mode, setMode] = useState<ShareMode>("template")
  const [loading, setLoading] = useState(false)
  const [link, setLink] = useState<string | null>(null)

  const handleGenerate = async () => {
    setLoading(true)
    try {
      const generatedLink =
        mode === "template"
          ? await onGenerateTemplateLink()
          : await onGenerateInviteLink()

      setLink(generatedLink)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    if (link) {
      await navigator.clipboard.writeText(link)
    }
  }

  return (
    <Modal className={className} isOpen={isOpen} onClose={onClose}>

      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold">Share Workflow</h2>
        <p className="text-sm text-gray-500 mt-1">
          Choose how you want to share this workflow.
        </p>
      </div>

      {/* Mode Selection (Cards) */}
      <div className="flex flex-col gap-3 mb-6">

        {/* Template */}
        <button
          onClick={() => {
            setMode("template")
            setLink(null)
          }}
          className={`text-left border rounded-lg p-4 transition ${
            mode === "template"
              ? "border-blue-500 bg-blue-50"
              : "border-gray-200 hover:border-gray-300"
          }`}
        >
          <div className="flex justify-between items-center mb-1">
            <span className="font-medium">Share as Template</span>
            {mode === "template" && (
              <span className="text-sm text-blue-600">Selected</span>
            )}
          </div>
          <div className="text-sm text-gray-600">
            Others can create their own independent copy of this workflow.
          </div>
        </button>

        {/* Collaborate */}
        <button
          onClick={() => {
            setMode("collaborate")
            setLink(null)
          }}
          className={`text-left border rounded-lg p-4 transition ${
            mode === "collaborate"
              ? "border-blue-500 bg-blue-50"
              : "border-gray-200 hover:border-gray-300"
          }`}
        >
          <div className="flex justify-between items-center mb-1">
            <span className="font-medium">Invite Collaborators</span>
            {mode === "collaborate" && (
              <span className="text-sm text-blue-600">Selected</span>
            )}
          </div>

          <div className="text-sm text-gray-600">
            Others can join this project and edit it.
          </div>

          {mode === "collaborate" && (
            <div className="mt-3 text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-md p-2">
              This grants full edit access to the project.
            </div>
          )}
        </button>

      </div>

      {/* Link Output */}
      {link && (
        <div className="mb-6 border rounded-md p-3 bg-gray-50">
          <div className="text-xs text-gray-500 mb-1">
            Shareable link
          </div>
          <div className="flex items-center gap-2">
            <input
              readOnly
              value={link}
              className="flex-1 text-sm bg-white border rounded px-2 py-1"
            />
            <Button onClick={handleCopy} sentiment={ButtonSentiment.NEUTRAL}>
              Copy
            </Button>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between items-center mt-6">
        <Button
          type="button"
          onClick={onClose}
          sentiment={ButtonSentiment.NEUTRAL}
        >
          Close
        </Button>

        <Button
          disabled={loading}
          onClick={handleGenerate}
          sentiment={ButtonSentiment.POSITIVE}
        >
          <LoadingAndError loading={loading} iconSize={21}>
            {link ? "Regenerate Link" : "Generate Link"}
          </LoadingAndError>
        </Button>
      </div>
    </Modal>
  )
}
