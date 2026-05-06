import ComputeBlockNode, { type ComputeBlockNodeType } from "./nodes/ComputeBlockNode"
import { ConnectionMode, type Edge, ReactFlow } from "@xyflow/react"
import { useMemo } from "react"


type PreviewWorkbenchProps = {
  compute_blocks: ComputeBlockNodeType[],
  edges: Edge[],
}

export function PreviewWorkbench({
  compute_blocks,
  edges
}: PreviewWorkbenchProps) {
  const nodeTypes = useMemo(() => ({ computeBlock: ComputeBlockNode }), [])

  return (
    <ReactFlow
      nodeTypes={nodeTypes}
      nodes={compute_blocks}
      edges={edges}
      nodesConnectable={true}
      nodesDraggable={false}
      connectionMode={ConnectionMode.Loose}
    />
  )
}
