import ConfigBox from "@/components/ConfigBox"
import LoadingAndError from "../LoadingAndError"
import type { InputOutput, RecordValueType } from "../CreateComputeBlockModal"
import Button, { ButtonSentiment } from "../Button"

type EditInputsOutputsTabProps = {
  inputoutputs: InputOutput[],
  updateConfig: (key: string, value: RecordValueType) => void,
  handleSave: () => void,
  loading: boolean,
}

export default function EditInputsOutputsTab({ inputoutputs, updateConfig, handleSave, loading }: EditInputsOutputsTabProps) {

  return (
    <div>
      <ConfigBox
        headline="Inputs"
        description="Configure the Compute Blocks inputs here"
        config={inputoutputs}
        updateComputeBlock={updateConfig}
      />

      <div className="flex justify-end py-5">
        <Button
          onClick={handleSave}
          sentiment={ButtonSentiment.POSITIVE}
        >
          <LoadingAndError loading={loading} iconSize={21}>
            Save
          </LoadingAndError>
        </Button>
      </div>
    </div>
  )
}

