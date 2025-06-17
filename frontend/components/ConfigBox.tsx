import {
  type RecordValueType,
  type InputOutput,
  IOType,
  InputOutputType
} from "@/components/CreateComputeBlockModal"
import ConfigEnvsInputs from "@/components/inputs/ConfigEnvsInputs"
import Button, { ButtonSentiment } from "./Button"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import { useGraphData } from "./Workbench"
import { useState } from "react"
import FileInput from "./inputs/FileInput"

export enum ConfigBoxVariant {
  COMPLEX = 0,
  SIMPLE = 1
}

type ConfigBoxProps = {
  config: InputOutput[] | Record<string, RecordValueType>,
  headline: string,
  description: string,
  updateConfig: (key: string, newValue: RecordValueType, io_id?: string) => void,
  updateSelectedFile?: (name: string, file?: File, io_id?: string) => void,
  variant?: ConfigBoxVariant,
};

function FileInputControl({
  io,
  selectedFile,
  onFileChange,
  onFileRemove,
  disabled,
}: {
  io: InputOutput,
  selectedFile?: File,
  onFileChange: (name: string, file: File, io_id?: string) => void,
  onFileRemove: (name: string, io_id?: string) => void,
  disabled: boolean,
}) {
  if (disabled) return null

  return (
    <div className="flex items-center space-x-2">
      <FileInput
        id={`file_input_${io.name}`}
        label="Choose your file"
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
          const file = e.target.files?.[0] || null
          if (file) onFileChange(io.name, file, io.id)
        }}
      />
      {selectedFile && (
        <button
          type="button"
          onClick={() => onFileRemove(io.name, io.id)}
          className="text-xs text-red-600 hover:underline"
        >
          Remove
        </button>
      )}
    </div>
  )
}

function ConfigInputsSection({
  io,
  variant,
  updateConfig,
  disabled,
}: {
  io: InputOutput,
  variant: ConfigBoxVariant,
  updateConfig: (key: string, value: RecordValueType, io_id?: string) => void,
  disabled: boolean,
}) {
  const hasConfig = Object.keys(io.config).length > 0
  const shouldRenderInputs =
    variant === ConfigBoxVariant.COMPLEX ||
    (
      variant === ConfigBoxVariant.SIMPLE &&
      !(io.type === IOType.INPUT && io.data_type === InputOutputType.FILE)
    )

  if (!shouldRenderInputs || !hasConfig) return null

  return (
    <ConfigEnvsInputs
      pairs={io.config}
      onUpdate={(key, value) => updateConfig(key, value, io.id)}
      configVariant={variant}
      disabled={disabled}
    />
  )
}

export default function ConfigBox({
  config,
  headline,
  description,
  updateConfig,
  updateSelectedFile,
  variant = ConfigBoxVariant.COMPLEX
}: ConfigBoxProps) {
  const [selectedFiles, setSelectedFiles] = useState<{ [key: string]: { selectedFile: File } }>({})

  const { selectedProject } = useSelectedProject()
  const { edges } = useGraphData(selectedProject!.uuid)

  function isInputConnected(id: string) {
    return edges.some(edge => edge.targetHandle === id)
  }

  function handleFileChange(name: string, file: File, io_id?: string) {
    setSelectedFiles(prev => ({
      ...prev,
      [name]: { selectedFile: file },
    }))
    updateSelectedFile?.(name, file, io_id)
  }

  function handleFileRemove(name: string, io_id?: string) {
    setSelectedFiles(prev => {
      const newState = { ...prev }
      delete newState[name]
      return newState
    })
    updateSelectedFile?.(name, undefined, io_id)
    const input = document.getElementById(`file_input_${name}`) as HTMLInputElement | null
    if (input) input.value = ""
  }

  if (!Array.isArray(config)) {
    // If config is a simple object, just render ConfigEnvsInputs directly
    return (
      <div className="p-4 border rounded relative">
        <h3 className="text-lg font-semibold">{headline}</h3>
        <p className="text-gray-700 mb-4">{description}</p>
        <ConfigEnvsInputs
          pairs={config}
          onUpdate={updateConfig}
          configVariant={variant}
        />
      </div>
    )
  }

  return (
    <div className="p-4 border rounded relative">
      <h3 className="text-lg font-semibold">{headline}</h3>
      <p className="text-gray-700 mb-4">{description}</p>

      {config.map(io => {
        const connected = isInputConnected(io.id!)
        // File & DB Inputs are disabled if they are connected (we can do autoconfigure)
        const disableInputs =
          (io.data_type === InputOutputType.FILE || io.data_type === InputOutputType.DB) &&
          connected

        // File Inputs are shown for Inputs of type File, if the input is not yet connected.
        // In the SIMPLE variant, we are showing the File Input as soon as one config key
        // might be unset.
        const showFileInput =
          (io.type === IOType.INPUT)
          && !connected


        return (
          <div className="p-4 border rounded mt-5" key={io.id}>
            <div className="flex items-start justify-between mb-2">
              <div>
                <h3 className="text-md font-semibold flex items-center gap-1">
                  { /* Show the Block name if Variant is Simple */}
                  {variant === ConfigBoxVariant.SIMPLE && (
                    <>
                      <span className="text-gray-600">{io.block_custom_name}</span>
                      <span>|</span>
                    </>
                  )}
                  <span>{io.name}</span>
                </h3>
                <p className="text-gray-700">{io.description}</p>
              </div>
              <div className="flex flex-col space-y-2 items-end">
                {showFileInput && (
                  <FileInputControl
                    io={io}
                    selectedFile={selectedFiles[io.name]?.selectedFile}
                    onFileChange={handleFileChange}
                    onFileRemove={handleFileRemove}
                    disabled={false}
                  />
                )}
                {io.presigned_url && (
                  <Button
                    onClick={() => window.open(io.presigned_url, "_blank")}
                    sentiment={ButtonSentiment.POSITIVE}
                  >
                    Download
                  </Button>
                )}
              </div>
            </div>

            <ConfigInputsSection
              io={io}
              variant={variant}
              updateConfig={updateConfig}
              disabled={disableInputs}
            />
          </div>
        )
      })}
    </div>
  )
}

