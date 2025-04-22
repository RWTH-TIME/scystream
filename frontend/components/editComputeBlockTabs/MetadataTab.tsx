import { useEffect, useState } from "react"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import { useComputeBlockEnvsQuery, useDeleteComputeBlockMutation, useUpdateComputeBlockMutation } from "@/mutations/computeBlockMutation"
import { useAlert } from "@/hooks/useAlert"

import ConfigBox from "@/components/ConfigBox"
import Input from "@/components/inputs/Input"
import LoadingAndError from "@/components/LoadingAndError"
import DeleteModal from "../DeleteModal"
import Button, { ButtonSentiment } from "../Button"

import type { RecordValueType } from "../CreateComputeBlockModal"

type MetadataFormType = {
  custom_name: string,
  envs: Record<string, RecordValueType>,
}

const emptyMetadataForm: MetadataFormType = {
  custom_name: "",
  envs: {},
}

export default function MetadataTab() {
  const { selectedComputeBlock, setSelectedComputeBlock } = useSelectedComputeBlock()
  const { selectedProject } = useSelectedProject()
  const { setAlert } = useAlert()

  const { mutateAsync: deleteMutate, isPending: deleteLoading } = useDeleteComputeBlockMutation(setAlert, selectedProject?.uuid)
  const { mutateAsync: updateMutate, isPending: updateLoading } = useUpdateComputeBlockMutation(setAlert, selectedProject?.uuid)
  const { data: envs, isLoading: envsLoading, isError: envsError } = useComputeBlockEnvsQuery(selectedComputeBlock?.selected_entrypoint.id)

  const [deleteApproveOpen, setDeleteApproveOpen] = useState(false)
  const [metadataForm, setMetadataForm] = useState<MetadataFormType>(emptyMetadataForm)
  const [initialMetadataForm, setInitialMetadataForm] = useState<MetadataFormType>(emptyMetadataForm)

  const isDataChanged = JSON.stringify(metadataForm) !== JSON.stringify(initialMetadataForm)

  useEffect(() => {
    if (selectedComputeBlock) {
      const newForm = {
        custom_name: selectedComputeBlock.custom_name,
        envs: envs || {},
      }
      setMetadataForm(newForm)
      setInitialMetadataForm(newForm)
    }
  }, [envs, selectedComputeBlock])

  function onCBDelete() {
    if (selectedComputeBlock) {
      setSelectedComputeBlock(undefined)
      deleteMutate(selectedComputeBlock.id)
      setDeleteApproveOpen(false)
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setMetadataForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function handleEnvChange(key: string, value: RecordValueType) {
    setMetadataForm((prev) => ({
      ...prev,
      envs: { ...prev.envs, [key]: value },
    }))
  }

  function handleSave() {
    const changedFields: Partial<MetadataFormType> = {}

    if (metadataForm.custom_name !== initialMetadataForm.custom_name) {
      changedFields.custom_name = metadataForm.custom_name
    }

    const changedEnvs = Object.entries(metadataForm.envs).reduce((acc, [key, value]) => {
      if (value !== initialMetadataForm.envs[key]) {
        acc[key] = value
      }
      return acc
    }, {} as Record<string, RecordValueType>)

    if (Object.keys(changedEnvs).length > 0) {
      changedFields.envs = changedEnvs
    }

    updateMutate(
      {
        id: selectedComputeBlock!.id,
        ...changedFields
      }
    )
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
      <LoadingAndError loading={envsLoading} error={envsError} >
        <h2 className="text-xl font-bold">
          Compute Block <span className="text-blue-600">{selectedComputeBlock?.name}</span> Settings:
        </h2>
        <p className="text-sm text-gray-800">{selectedComputeBlock?.description}</p>

        <Input type="text" name="custom_name" value={metadataForm.custom_name} label="Name" onChangeEvent={handleChange} />

        <div className="my-5">
          <ConfigBox
            headline="Envs"
            description="Edit the Compute Blocks Envs here"
            config={metadataForm.envs}
            updateConfig={handleEnvChange}
          />
        </div>

        <div className="flex justify-between">
          <Button onClick={() => setDeleteApproveOpen(true)} sentiment={ButtonSentiment.NEGATIVE}>
            <LoadingAndError loading={deleteLoading} iconSize={21}>
              Delete
            </LoadingAndError>
          </Button>

          <Button
            onClick={handleSave}
            sentiment={ButtonSentiment.POSITIVE}
            disabled={!isDataChanged}
          >
            <LoadingAndError loading={updateLoading} iconSize={21}>
              Save
            </LoadingAndError>
          </Button>
        </div>
      </LoadingAndError>
    </div>
  )
}
