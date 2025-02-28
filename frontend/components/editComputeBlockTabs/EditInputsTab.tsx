import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import ConfigBox from "@/components/ConfigBox"

export default function EditInputsTab() {
  const { selectedComputeBlock } = useSelectedComputeBlock()

  return (
    <div>
      <ConfigBox
        headline="Inputs"
        description="Configure the Compute Blocks inputs here"
        config={selectedComputeBlock?.selected_entrypoint.inputs || []}
        updateComputeBlock={(key, value) => updateConfig("inputs", key, value)}
      />
    </div>
  )
}
