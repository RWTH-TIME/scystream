import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import ConfigBox from "@/components/ConfigBox"

export default function EditOutputsTab() {
  const { selectedComputeBlock } = useSelectedComputeBlock()

  return (
    <div>
      <ConfigBox
        headline="Outputs"
        description="Configure the Compute Blocks outputs here"
        config={selectedComputeBlock?.selected_entrypoint.outputs || []}
        updateComputeBlock={(key, value) => updateConfig("inputs", key, value)}
      />
    </div>
  )
}
