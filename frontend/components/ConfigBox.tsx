import type { RecordValueType, InputOutput } from "@/components/CreateComputeBlockModal"
import ConfigEnvsInputs from "@/components/inputs/ConfigEnvsInputs"

type ConfigBoxProps = {
  config: InputOutput[] | Record<string, RecordValueType>,
  headline: string,
  description: string,
  updateConfig: (key: string, newValue: RecordValueType) => void,
}

export default function ConfigBox({
  config,
  headline,
  description,
  updateConfig
}: ConfigBoxProps) {
  return (
    <div className="p-4 border rounded">
      <h3 className="text-lg font-semibold">{headline}</h3>
      <p className="text-gray-700 mb-4">{description}</p>
      {
        Array.isArray(config) ? (
          config.map((o: InputOutput) => (
            <div className="p-4 border rounded mt-5" key={o.name}>
              <h3 className="text-md font-semibold" key={o.name}>{o.name}</h3>
              <p className="text-gray-700 mb-4" key={o.description}>{o.description}</p>
              <ConfigEnvsInputs pairs={o.config} onUpdate={updateConfig} />
            </div>
          ))) : (
          <ConfigEnvsInputs pairs={config} onUpdate={updateConfig} />
        )
      }
    </div>
  )
}
