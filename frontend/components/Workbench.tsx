import type { DragEvent } from "react"
import { useState, useCallback, useMemo, useEffect } from "react"
import type { XYPosition, Edge, Connection } from "@xyflow/react"
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  type NodeChange,
  type Node as FlowNode,
  useReactFlow,
  ConnectionMode
} from "@xyflow/react"
import { PlayArrow, Widgets, Delete } from "@mui/icons-material"
import ComputeBlockNode from "./nodes/ComputeBlockNode"
import "@xyflow/react/dist/style.css"
import LoadingAndError from "./LoadingAndError"
import EditProjectDraggable from "./EditProjectDraggable"
import EditComputeBlockDraggable from "./EditComputeBlockDraggable"
import type { ComputeBlock, InputOutputType  } from "@/components/CreateComputeBlockModal"
import CreateComputeBlockModal from "./CreateComputeBlockModal"
import { useDeleteProjectMutation, type Node } from "@/mutations/projectMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import { useComputeBlocksByProjectQuery, useCreateEdgeMutation, useUpdateComputeBlockMutation, useUpdateInputOutputMutation } from "@/mutations/computeBlockMutation"
import { AlertType, useAlert } from "@/hooks/useAlert"
import DeleteModal from "./DeleteModal"

/**
 * Workbench Component is used to display and edit Directed Acyclic Graphs (DAGs).
 * TODO: Split this Component into multiple smaller ones
 */
export default function Workbench() {
  const nodeTypes = useMemo(() => ({ computeBlock: ComputeBlockNode }), [])
  const { selectedProject, setSelectedProject } = useSelectedProject()
  const { data: projectDetails, isLoading, isError } = useComputeBlocksByProjectQuery(selectedProject?.uuid)
  const { selectedComputeBlock, setSelectedComputeBlock } = useSelectedComputeBlock()
  const { screenToFlowPosition } = useReactFlow()
  const { setAlert } = useAlert()
  const { mutate: updateBlockMutate } = useUpdateComputeBlockMutation(setAlert)
  const { mutate: deleteMutate, isPending: deleteLoading } = useDeleteProjectMutation(setAlert)
  const { mutateAsync: edgeMutate } = useCreateEdgeMutation(setAlert)
  const { mutate: updateInputOutputMutate } = useUpdateInputOutputMutation(setAlert, selectedProject?.uuid)

  const [nodes, setNodes] = useState<FlowNode<Node>[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [deleteApproveOpen, setDeleteApproveOpen] = useState(false)
  const [createComputeBlockOpen, setCreateComputeBlockOpen] = useState(false)
  const [dropCoordinates, setDropCoordinates] = useState<XYPosition>({ x: 0, y: 0 })

  function onProjectDelete() {
    if (selectedProject) {
      deleteMutate(selectedProject.uuid)
      setDeleteApproveOpen(false)
      setSelectedProject(undefined)
    }
  }



  useEffect(() => {
    if (projectDetails) {
      setNodes(projectDetails.blocks as unknown as FlowNode<Node>[])
      setEdges(projectDetails.edges)
    }
  }, [projectDetails])

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setNodes((nds) => applyNodeChanges(changes, nds) as FlowNode<Node>[])
    },
    []
  )

  const onNodeDragStop = useCallback(
    (_: React.SyntheticEvent, node: FlowNode<Node>) => {
      updateBlockMutate({
        id: node.id,
        x_pos: node.position.x,
        y_pos: node.position.y
      });
    },
    [updateBlockMutate]
  );

  const onDragStart = (event: DragEvent<HTMLButtonElement>) => {
    event.dataTransfer.effectAllowed = "move"
  }

  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = "move"
  }, [])

  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault()
      setDropCoordinates(screenToFlowPosition({
        x: event.clientX,
        y: event.clientY
      }))
      setCreateComputeBlockOpen(true)
    },
    [screenToFlowPosition]
  )

  const onConnect = useCallback(
    (connection: Connection) => {

      const existingEdge = edges.find(
        (edge) =>
          edge.targetHandle === connection.targetHandle
      );

      // If a connection already exists, do not add it
      if (existingEdge) {
        setAlert("This output is already gt! connected to an input.", AlertType.ERROR)
        return;
      }


      // Proceed with adding the connection if it's not already present
      const sourceNode = nodes.find((node) => node.id === connection.source);
      const targetNode = nodes.find((node) => node.id === connection.target);

      if (sourceNode && targetNode) {
        const sourceHandle = sourceNode.data.selected_entrypoint?.outputs?.find(
          (output) => output.id === connection.sourceHandle
        );
        const targetHandle = targetNode.data.selected_entrypoint?.inputs?.find(
          (input) => input.id === connection.targetHandle
        );

        // Check if types are compatible
        if (sourceHandle && targetHandle) {
          const sourceType = sourceHandle.data_type;
          const targetType = targetHandle.data_type;


          switchPrefixes(sourceHandle, targetHandle, InputOutputType[sourceHandle.data_type])
          if (sourceType === targetType) {
            const dto = {
              source: connection.source,
              sourceHandle: connection.sourceHandle!,
              target: connection.target,
              targetHandle: connection.targetHandle!
            }

            // Overwrite the target's config by the source's configs
            updateInputOutputMutate({

            })

            edgeMutate(dto)
            setEdges((eds) => [
              ...eds,
              {
                id: `${connection.sourceHandle}-${connection.targetHandle}`,
                source: connection.source,
                target: connection.target,
                sourceHandle: connection.sourceHandle,
                targetHandle: connection.targetHandle,
              },
            ]);
          } else {
            // Handle the case where types do not match
            setAlert("Incompatible connection types!", AlertType.ERROR)
          }
        }
      }
    },
    [edges, nodes, setAlert, edgeMutate]
  );


  if (!selectedProject) {
    return <div>Select a Project</div>
  }

  return (
    <LoadingAndError loading={isLoading} error={isError}>
      <DeleteModal
        isOpen={deleteApproveOpen}
        onClose={() => setDeleteApproveOpen(false)}
        onDelete={onProjectDelete}
        loading={deleteLoading}
        header="Delete Project"
        desc={`Are you sure you want to delete the project: ${selectedProject?.name}`}
      />

      <CreateComputeBlockModal
        isOpen={createComputeBlockOpen}
        onClose={() => setCreateComputeBlockOpen(false)}
        dropCoordinates={dropCoordinates}
      />
      {selectedComputeBlock ? <EditComputeBlockDraggable /> : <EditProjectDraggable />}
      <div className="flex absolute justify-between flex-row p-5 gap-3 right-0 bg-inherit z-30">
        <div className="justify-self-start h-12 flex flex-col items-start p-1 bg-white rounded-lg shadow-lg space-y-3">
          <button
            onClick={() => console.log("Add Component clicked")}
            className="p-2 bg-gray-100 rounded-md text-gray-800 hover:bg-gray-200 transition-all duration-200"
            onDragStart={(event) => onDragStart(event)}
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
          edges={edges}
          onNodesChange={onNodesChange}
          fitView
          onNodeClick={(_, node) => setSelectedComputeBlock(node.data as unknown as ComputeBlock)}
          onPaneClick={() => setSelectedComputeBlock(undefined)}
          onDragOver={onDragOver}
          onNodeDragStop={onNodeDragStop}
          onDrop={onDrop}
          onConnect={onConnect}
          connectionMode={ConnectionMode.Loose}
          nodesConnectable={true}
        >
          <Background />
          <Controls position="top-left" />
        </ReactFlow>
      </div>
    </LoadingAndError>
  )
}

