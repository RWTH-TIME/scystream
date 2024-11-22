import { useState, useCallback, useMemo, useEffect } from "react"
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges
} from "@xyflow/react"
import ComputeBlockNode from "./nodes/ComputeBlockNode"
import "@xyflow/react/dist/style.css"
import LoadingAndError from "./LoadingAndError"
import type { Project } from "@/utils/types"
import type { Node } from "@/mutations/projectMutation"
import { useProjectDetailsQuery } from "@/mutations/projectMutation"

export type WorkbenchProps = {
  selectedProject: Project
}

/*
* The Workbench Component is used to display & edit the DAGs.
*/
export default function Workbench({ selectedProject }: WorkbenchProps) {
  const nodeTypes = useMemo(() => ({ computeBlock: ComputeBlockNode }), [])

  const { data: projectDetails, isLoading, isError } = useProjectDetailsQuery(selectedProject.uuid)

  const [nodes, setNodes] = useState<Node[]>([])

  useEffect(() => {
    if (projectDetails) {
      setNodes(projectDetails)
    }
  }, [projectDetails])

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  )

  return (
    <LoadingAndError loading={isLoading} error={isError}>
      <div style={{ height: "100%" }}>
        <ReactFlow
          nodeTypes={nodeTypes}
          nodes={nodes}
          onNodesChange={onNodesChange}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </LoadingAndError>
  )
}
