import ConfigBox from "@/components/ConfigBox"
import LoadingAndError from "../LoadingAndError"
import { encodeFileToBase64, type InputOutput, type IOType, type RecordValueType } from "../CreateComputeBlockModal"
import Button, { ButtonSentiment } from "../Button"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import type { UpdateInputOutputDTO } from "@/mutations/computeBlockMutation"
import { useComputeBlocksIOsQuery, useUpdateComputeBlocksIOsMutation } from "@/mutations/computeBlockMutation"
import { useEffect, useState } from "react"

type EditInputsOutputsTabProps = {
  type: IOType,
}

export default function EditInputsOutputsTab({ type }: EditInputsOutputsTabProps) {
  const { selectedComputeBlock } = useSelectedComputeBlock()
  const { data: io, isLoading: ioLoading, isError: ioError } = useComputeBlocksIOsQuery(type, selectedComputeBlock?.selected_entrypoint.id)
  const { mutateAsync } = useUpdateComputeBlocksIOsMutation()

  const [ios, setIOS] = useState<InputOutput[]>([])
  const [initialIos, setInitialIos] = useState<InputOutput[]>([])
  const [modifiedFields, setModifiedFields] = useState<Map<string, RecordValueType>>(new Map())

  const isDataChanged = JSON.stringify(ios) !== JSON.stringify(initialIos)

  useEffect(() => {
    setIOS(io ?? [])
    setInitialIos(io ?? [])
  }, [io])

  function handleConfigChange(key: string, value: RecordValueType) {
    setIOS((prev) =>
      prev.map((io) =>
        key in io.config
          ? {
            ...io,
            config: {
              ...io.config,
              [key]: value,
            },
          }
          : io
      )
    )

    setModifiedFields((prev) => {
      const newMap = new Map(prev)
      newMap.set(key, value)
      return newMap
    })
  }

  function handleFileChange(name: string, file?: File) {
    setIOS(prev =>
      prev.map(i =>
        i.name === name
          ? { ...i, selected_file: file ?? undefined } // set or unset
          : i
      )
    )

    setModifiedFields((prev) => {
      const newMap = new Map(prev)
      newMap.set("file", "file")
      return newMap
    })
  }

  async function handleSave() {
    const changedData: UpdateInputOutputDTO[] = []

    for (const io of ios) {
      const updatedConfig = Object.fromEntries(
        Object.entries(io.config).filter(([key]) => modifiedFields.has(key))
      )

      const hasConfigChanges = Object.keys(updatedConfig).length > 0
      const hasFileChange = modifiedFields.has("file") && io.selected_file

      let selected_file_b64: string | undefined
      let selected_file_type: string | undefined

      if (hasFileChange && io.selected_file) {
        selected_file_type = io.selected_file.name.split(".").pop()?.toLowerCase()
        selected_file_b64 = await encodeFileToBase64(io.selected_file)
      }

      if (hasConfigChanges || selected_file_b64) {
        changedData.push({
          id: io.id!,
          type: type,
          config: hasConfigChanges ? updatedConfig : undefined,
          selected_file_b64,
          selected_file_type,
        })
      }
    }

    await mutateAsync(changedData)
    setModifiedFields(new Map())
  }


  return (
    <div>
      <LoadingAndError loading={ioLoading} error={ioError} >
        <ConfigBox
          headline={type.toString()}
          description={`Configure the Compute Blocks ${type.toString().toLowerCase()}s here`}
          config={ios}
          updateConfig={handleConfigChange}
          updateSelectedFile={handleFileChange}
        />
        <div className="flex justify-end py-5">
          <Button
            disabled={!isDataChanged}
            onClick={handleSave}
            sentiment={ButtonSentiment.POSITIVE}
          >
            <LoadingAndError loading={false} iconSize={21}>
              Save
            </LoadingAndError>
          </Button>
        </div>
      </LoadingAndError>
    </div>
  )
}

