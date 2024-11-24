import type { DragEvent } from "react"
import { useState, useCallback, useMemo, useEffect } from "react"
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  type NodeChange,
  type Node as FlowNode,
  useReactFlow
} from "@xyflow/react"
import { PlayArrow, Widgets, Save, Delete } from "@mui/icons-material"
import ComputeBlockNode from "./nodes/ComputeBlockNode"
import "@xyflow/react/dist/style.css"
import LoadingAndError from "./LoadingAndError"
import DeleteProjectModal from "./DeleteProjectModal"
import EditProjectDraggable from "./EditProjectDraggable"
import EditComputeBlockDraggable from "./EditComputeBlockDraggable"
import type { Node } from "@/mutations/projectMutation"
import { useProjectDetailsQuery } from "@/mutations/projectMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"

/**
 * Workbench Component is used to display and edit Directed Acyclic Graphs (DAGs).
 * TODO: Split this Component into multiple smaller ones
 */
export default function Workbench() {
  const nodeTypes = useMemo(() => ({ computeBlock: ComputeBlockNode }), [])
  const { selectedProject } = useSelectedProject()
  const { data: projectDetails, isLoading, isError } = useProjectDetailsQuery(selectedProject?.uuid)
  const { selectedComputeBlock, setSelectedComputeBlock } = useSelectedComputeBlock()
  const { screenToFlowPosition } = useReactFlow()

  const [nodes, setNodes] = useState<FlowNode<Node>[]>([])
  const [deleteApproveOpen, setDeleteApproveOpen] = useState(false)
  const [type, setType] = useState<string | null>(null)

  useEffect(() => {
    if (projectDetails) {
      setNodes(projectDetails as FlowNode<Node>[]) // Ensure projectDetails matches the Node type
    }
  }, [projectDetails])

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  )

  const onDragStart = (event: DragEvent<HTMLButtonElement>, nodeType: string) => {
    setType(nodeType)
    event.dataTransfer.effectAllowed = "move"
  }

  const onDragOver = useCallback((event: DragEvent) => {
    console.log(event)
    event.preventDefault()
    event.dataTransfer.dropEffect = "move"
  }, [])

  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault()

      if (!type) return

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      // TODO: We need some kind of unique identifier in the data before creating in the backend
      // Think about a way
      const newNode: FlowNode<Node> = {
        id: `${type}_${nodes.length + 1}`,
        type: "computeBlock",
        position,
        data: { label: `${type} Node` },
      }

      // TODO: Startup the CreateComputeBlock configuration

      setNodes((nds) => [...nds, newNode])
    },
    [type, nodes, screenToFlowPosition]
  )

  if (!selectedProject) {
    return <div>Select a Project</div>
  }

  return (
    <LoadingAndError loading={isLoading} error={isError}>
      <DeleteProjectModal
        isOpen={deleteApproveOpen}
        onClose={() => setDeleteApproveOpen(false)}
      />
      {selectedComputeBlock ? <EditComputeBlockDraggable /> : <EditProjectDraggable />}
      <div className="flex absolute justify-between flex-row p-5 gap-3 right-0 bg-inherit z-30">
        <div className="justify-self-start h-12 flex flex-col items-start p-1 bg-white rounded-lg shadow-lg space-y-3">
          <button
            onClick={() => console.log("Add Component clicked")}
            className="p-2 bg-gray-100 rounded-md text-gray-800 hover:bg-gray-200 transition-all duration-200"
            onDragStart={(event) => onDragStart(event, "computeBlock")}
            draggable
          >
            <Widgets fontSize="small" />
          </button>
        </div>
        <div className="flex justify-self-end gap-3">
          <button
            onClick={() => console.log("Play clicked")}
            className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full hover:bg-blue-400 transition-all duration-200"
          >
            <PlayArrow />
          </button>
          <button
            onClick={() => console.log("Save clicked")}
            className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full hover:bg-blue-400 transition-all duration-200"
          >
            <Save />
          </button>
          <button
            onClick={() => setDeleteApproveOpen(true)}
            className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full hover:bg-blue-400 transition-all duration-200"
          >
            <Delete />
          </button>
        </div>
      </div>
      <div className="h-full">
        <ReactFlow
          nodeTypes={nodeTypes}
          nodes={nodes}
          onNodesChange={onNodesChange}
          fitView
          onNodeClick={(_, node) => setSelectedComputeBlock(node.data)}
          onPaneClick={() => setSelectedComputeBlock(undefined)}
          onDragOver={onDragOver}
          onDrop={onDrop}
        >
          <Background />
          <Controls position="top-left" />
        </ReactFlow>
      </div>
    </LoadingAndError>
  )
}
