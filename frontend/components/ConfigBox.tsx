import { type RecordValueType, type InputOutput, ComputeBlockStatus } from "@/components/CreateComputeBlockModal"
import ConfigEnvsInputs from "@/components/inputs/ConfigEnvsInputs"
import Button, { ButtonSentiment } from "./Button"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"

type ConfigBoxProps = {
  config: InputOutput[] | Record<string, RecordValueType>,
  headline: string,
  description: string,
  updateConfig: (key: string, newValue: RecordValueType) => void,
};

export default function ConfigBox({ config, headline, description, updateConfig }: ConfigBoxProps) {
  const { selectedComputeBlock } = useSelectedComputeBlock()

  return (
    <div className="p-4 border rounded relative">
      <h3 className="text-lg font-semibold">{headline}</h3>
      <p className="text-gray-700 mb-4">{description}</p>
      {Array.isArray(config) ? (
        config.map((o: InputOutput) => (
          <div className="p-4 border rounded mt-5 relative" key={o.name}>
            {o.presigned_url && selectedComputeBlock?.status === ComputeBlockStatus.SUCCESS && (
              <div className="absolute top-4 right-4">
                <Button
                  onClick={() => window.open(o.presigned_url, "_blank")}
                  sentiment={ButtonSentiment.POSITIVE}
                >
                  Download
                </Button>
              </div>
            )}
            <h3 className="text-md font-semibold">{o.name}</h3>
            <p className="text-gray-700 mb-4">{o.description}</p>
            <ConfigEnvsInputs pairs={o.config} onUpdate={updateConfig} />
          </div>
        ))
      ) : (
        <ConfigEnvsInputs pairs={config} onUpdate={updateConfig} />
      )}
    </div>
  )
}
