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
import FileUploadModal from "./ConfigureFileModal"

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
  hasIOChanged?: (id: string) => boolean,
};

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
  variant = ConfigBoxVariant.COMPLEX,
  hasIOChanged,
}: ConfigBoxProps) {
  const [selectedFiles, setSelectedFiles] = useState<{ [key: string]: { selectedFile: File } }>({})

  // TODO: #166 dont use useSelectedProject anymore
  const { selectedProject } = useSelectedProject()
  const { edges } = useGraphData(selectedProject!.uuid)
  const [modalIO, setModalIO] = useState<InputOutput | null>(null)

  function setModalOpenFor(io: InputOutput) {
    setModalIO(io)
  }


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
      {modalIO && (
        <FileUploadModal
          isOpen={!!modalIO}
          onClose={() => setModalIO(null)}
          io={modalIO}
          existingFile={selectedFiles[modalIO.name]?.selectedFile}
          onConfirm={(file) => {
            handleFileChange(modalIO.name, file!, modalIO.id)
          }}
        />
      )}
      <h3 className="text-lg font-semibold">{headline}</h3>
      <p className="text-gray-700 mb-4">{description}</p>

      {config.map(io => {
        const connected = isInputConnected(io.id!)
        const hasChanges = !!hasIOChanged?.(io.id!)

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
                  {variant === ConfigBoxVariant.SIMPLE && (
                    <>
                      <span className="text-gray-600">{io.block_custom_name}</span>
                      <span>|</span>
                    </>
                  )}
                  <span>{io.name}</span>
                  {hasChanges && (
                    <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded-full border border-yellow-300">
                      Unsaved
                    </span>
                  )}
                </h3>
                <p className="text-gray-700">{io.description}</p>
              </div>
              <div className="flex flex-row items-end space-x-2">
                {showFileInput && (
                  <Button
                    onClick={() => setModalOpenFor(io)}
                    sentiment={ButtonSentiment.NEUTRAL}
                  >
                    Configure File
                  </Button>
                )}
                {io.presigned_url && (
                  <Button
                    onClick={() => window.open(io.presigned_url, "_blank")}
                    sentiment={ButtonSentiment.POSITIVE}
                  >
                    Download Current
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

