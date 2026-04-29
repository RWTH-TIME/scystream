import type { InputOutput, PageProps, RecordValueType } from "@/components/CreateComputeBlockModal"
import LoadingAndError from "@/components/LoadingAndError"
import ConfigBox from "../ConfigBox"
import { useEffect, useState } from "react"
import Button, { ButtonSentiment } from "../Button"

function isValid(value: RecordValueType) {
  if (Array.isArray(value) && value.length === 0) return false
  return true
}

function validateSection(
  section: Record<string, RecordValueType> | InputOutput[],
  sectionType: "envs" | "inputs" | "outputs"
) {
  if (sectionType === "envs") {
    return Object.values(section as Record<string, RecordValueType>).every(isValid)
  } else {
    return (section as InputOutput[]).every((item) =>
      Object.values(item.config).every(isValid))
  }
}


export default function CreateComputeBlockConfigurationStep({
  onNext,
  onPrev,
  selectedEntrypoint,
  computeBlock,
  setSelectedEntrypoint,
  loading,
  project
}: PageProps) {
  const [formValid, setFormValid] = useState<boolean>(false)

  function updateConfig(section: "envs" | "inputs" | "outputs", key: string, value: RecordValueType) {
    if (!selectedEntrypoint || !setSelectedEntrypoint) return

    setSelectedEntrypoint((prevEntrypoint) => {
      if (!prevEntrypoint) return prevEntrypoint

      const updatedEntrypoint = { ...prevEntrypoint }

      if (section === "envs") {
        updatedEntrypoint.envs = {
          ...updatedEntrypoint.envs,
          [key]: value
        }
      } else {
        // This assumes, that keys are unique across inputs/outputs, which makes sense as
        // env variable names must be unique. (See SDK docs)
        updatedEntrypoint[section] = updatedEntrypoint[section].map((io) => {
          if (key in io.config) {
            return {
              ...io,
              config: {
                ...io.config,
                [key]: value,
              },
            }
          }
          return io
        })
      }
      return updatedEntrypoint
    })
  }

  function updateSelectedFile(name: string, file?: File) {
    // Set/Unset the selected File
    if (!selectedEntrypoint || !setSelectedEntrypoint) return

    setSelectedEntrypoint(prev => {
      if (!prev) return prev

      return {
        ...prev,
        inputs: prev.inputs.map(input =>
          input.name === name
            ? { ...input, selected_file: file }
            : input),
      }
    })
  }

  useEffect(() => {
    function validateForm() {
      if (!computeBlock?.custom_name.trim()) {
        setFormValid(false)
        return
      }

      const isEnvsValid = selectedEntrypoint?.envs ? validateSection(selectedEntrypoint.envs, "envs") : true
      const isInputsValid = selectedEntrypoint?.inputs ? validateSection(selectedEntrypoint.inputs, "inputs") : true
      const isOutputsValid = selectedEntrypoint?.outputs ? validateSection(selectedEntrypoint.outputs, "outputs") : true

      setFormValid(isEnvsValid && isInputsValid && isOutputsValid)
    }
    validateForm()
  }, [computeBlock?.custom_name, selectedEntrypoint])


  return (
    <div className="mt-4 space-y-6 text-sm">
      {selectedEntrypoint?.envs && (
        <ConfigBox
          headline="Environment Variables"
          description="Configure the Compute Blocks environment here"
          config={selectedEntrypoint?.envs}
          updateConfig={(key, value) => updateConfig("envs", key, value)}
          projectId={project.uuid}
        />
      )}

      {selectedEntrypoint?.inputs && (
        <ConfigBox
          headline="Inputs"
          description="Configure the Compute Blocks inputs here"
          config={selectedEntrypoint?.inputs}
          updateConfig={(key, value) => updateConfig("inputs", key, value)}
          updateSelectedFile={updateSelectedFile}
          projectId={project.uuid}
        />
      )}

      {selectedEntrypoint?.outputs && (
        <ConfigBox
          headline="Outputs"
          description="Configure the Compute Blocks outputs here"
          config={selectedEntrypoint?.outputs}
          updateConfig={(key, value) => updateConfig("outputs", key, value)}
          projectId={project.uuid}
        />
      )}

      <div className="flex justify-between">
        <Button
          sentiment={ButtonSentiment.NEUTRAL}
          onClick={onPrev}
        >
          Prev
        </Button>

        <Button
          sentiment={ButtonSentiment.POSITIVE}
          disabled={!formValid}
          onClick={onNext}
        >
          <LoadingAndError loading={loading} iconSize={21}>
            Create
          </LoadingAndError>
        </Button>
      </div>
    </div>
  )
}
