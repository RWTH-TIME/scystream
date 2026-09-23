import { useState } from "react"
import Modal from "./Modal"
import Input from "./inputs/Input"
import Button, { ButtonSentiment } from "./Button"
import LoadingAndError from "./LoadingAndError"
import { useAlert } from "@/hooks/useAlert"
import { useCreateSharedTemplateMutation } from "@/mutations/workflowMutations"

type SaveAsTemplateModalProps = {
  projectId: string,
  projectName: string,
  isOpen: boolean,
  onClose: () => void,
}

/**
 * Saves the project as pipeline template for all users. Generated storage
 * locations and secrets are never part of the template.
 */
export default function SaveAsTemplateModal({ projectId, projectName, isOpen, onClose }: SaveAsTemplateModalProps) {
  const { setAlert } = useAlert()
  const [name, setName] = useState(projectName)
  const [description, setDescription] = useState("")
  const [tags, setTags] = useState("")
  const [includeSettings, setIncludeSettings] = useState(true)
  const { mutateAsync, isPending } = useCreateSharedTemplateMutation(setAlert)

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    await mutateAsync({
      project_uuid: projectId,
      name,
      description,
      tags: tags.split(",").map(tag => tag.trim()).filter(Boolean),
      include_settings: includeSettings,
    })
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <h2 className="text-xl font-bold">Save as template</h2>
      <p className="text-sm text-gray-600 mt-1">
        The template is available to all users. It contains the compute blocks,
        their connections and, optionally, their settings. Storage locations and
        settings that look like secrets are never included. The Superset
        visualization of the project is used for projects created from it.
      </p>
      <form onSubmit={onSubmit} className="mt-4 space-y-4 text-sm">
        <Input type="text" value={name} label="Name" onChange={setName} minLength={2} maxLength={100} required />
        <Input type="text" value={description} label="Description" onChange={setDescription} maxLength={1000} />
        <Input type="text" value={tags} label="Tags (comma separated)" onChange={setTags} />
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={includeSettings}
            onChange={e => setIncludeSettings(e.target.checked)}
          />
          Include the configured settings (visible to all users)
        </label>
        <div className="flex justify-between">
          <Button type="button" onClick={onClose} sentiment={ButtonSentiment.NEUTRAL}>Cancel</Button>
          <Button type="submit" sentiment={ButtonSentiment.POSITIVE} disabled={isPending || name.length < 2}>
            <LoadingAndError loading={isPending} iconSize={18}>Save template</LoadingAndError>
          </Button>
        </div>
      </form>
    </Modal>
  )
}
