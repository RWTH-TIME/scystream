import type { RecordValueType } from "../CreateComputeBlockModal"
import Input from "./Input"

type ConfigEnvsInputsProps = {
  pairs: Record<string, RecordValueType>,
}

export default function ConfigEnvsInputs({
  pairs
}: ConfigEnvsInputsProps) {
  return (
    <div>
      {
        Object.entries(pairs).map(([key, value]) => (
          <div key={key}>
            <label className="block text-sm font-medium">{key}</label>
            <Input value={value} />
          </div>
        ))
      }
    </div>
  )
}
