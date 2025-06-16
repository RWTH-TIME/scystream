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

export default function ConfigBox({
  config,
  headline,
  description,
  updateConfig,
  updateSelectedFile,
  variant = ConfigBoxVariant.COMPLEX
}: ConfigBoxProps) {
  const [selectedFiles, setSelectedFiles] = useState<{
    [key: string]: { selectedFile: File },
  }>({})

  const { selectedProject } = useSelectedProject()
  const { edges } = useGraphData(selectedProject!.uuid)

  function isInputConnected(id: string) {
    return edges.some(edge => edge.targetHandle === id)
  }

  // File must not be specified using the configs, we can also upload them manually
  // This is the reason why this happens on ConfigBox not ConfigEnvsInput level
  function handleFileChange(name: string, file: File, io_id?: string) {
    setSelectedFiles((prevState) => ({
      ...prevState,
      [name]: {
        ...prevState[name],
        selectedFile: file
      }
    }))
    updateSelectedFile!(name, file, io_id)
  }

  return (
    <div className="p-4 border rounded relative">
      <h3 className="text-lg font-semibold">{headline}</h3>
      <p className="text-gray-700 mb-4">{description}</p>
      {Array.isArray(config) ? (
        config.map((o: InputOutput) => {
          return (
            <div className="p-4 border rounded mt-5" key={o.id}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-md font-semibold flex items-center gap-1">
                    {variant === ConfigBoxVariant.SIMPLE && (
                      <span className="text-gray-600">{o.block_custom_name}</span>
                    )}
                    {variant === ConfigBoxVariant.SIMPLE && <span>|</span>}
                    <span>{o.name}</span>
                  </h3>
                  <p className="text-gray-700">{o.description}</p>
                </div>
                <div className="flex flex-col space-y-2 items-end">
                  {o.type === IOType.INPUT && o.data_type === InputOutputType.FILE && !isInputConnected(o.id!) && (
                    <div className="flex items-center space-x-2">
                      <FileInput
                        id={`file_input_${o.name}`}
                        label="Choose your file"
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                          const file = e.target.files?.[0] || null
                          if (file) handleFileChange(o.name, file, o.id)
                        }}
                      />
                      {selectedFiles[o.name]?.selectedFile && (
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedFiles(prev => {
                              const newState = { ...prev }
                              delete newState[o.name]
                              return newState
                            })
                            updateSelectedFile!(o.name, undefined, o.id)
                            const input = document.getElementById(`file_input_${o.name}`) as HTMLInputElement | null
                            if (input) input.value = ""
                          }}
                          className="text-xs text-red-600 hover:underline"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  )}
                  {o.presigned_url && (
                    <Button
                      onClick={() => window.open(o.presigned_url, "_blank")}
                      sentiment={ButtonSentiment.POSITIVE}
                    >
                      Download
                    </Button>
                  )}
                </div>
              </div>
              {variant === ConfigBoxVariant.COMPLEX || (variant === ConfigBoxVariant.SIMPLE && o.data_type !== InputOutputType.FILE) ? (
                Object.keys(o.config).length > 0 && (
                  <ConfigEnvsInputs
                    pairs={o.config}
                    onUpdate={(key, value) => { updateConfig(key, value, o.id) }}
                    configVariant={variant}
                  />
                )
              ) : null}
            </div>
          )
        })
      ) : (
        <ConfigEnvsInputs
          pairs={config}
          onUpdate={updateConfig}
          configVariant={variant}
        />
      )}
    </div>
  )
}
