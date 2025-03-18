import ConfigBox from "@/components/ConfigBox"
import LoadingAndError from "../LoadingAndError"
import type { InputOutput, IOType, RecordValueType } from "../CreateComputeBlockModal"
import Button, { ButtonSentiment } from "../Button"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import { useComputeBlocksIOsQuery } from "@/mutations/computeBlockMutation"
import { useEffect, useState } from "react"

type EditInputsOutputsTabProps = {
  type: IOType,
}

export default function EditInputsOutputsTab({ type }: EditInputsOutputsTabProps) {
  const { selectedComputeBlock } = useSelectedComputeBlock()

  const { data: io, isLoading: ioLoading, isError: ioError } = useComputeBlocksIOsQuery(selectedComputeBlock?.selected_entrypoint.id, type)
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


  function handleSave() {
    const changedData = ios.map((io) => {
      const updatedConfig = Object.fromEntries(
        Object.entries(io.config).filter(([key]) => modifiedFields.has(key))
      )
      return { id: io.id, config: updatedConfig }
    })

    console.log("Saving changes:", changedData)

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

