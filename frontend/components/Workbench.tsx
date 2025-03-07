import type { DragEvent } from "react"
import { useState, useCallback, useMemo, useEffect } from "react"
import type { XYPosition, Edge, Connection } from "@xyflow/react"
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  type NodeChange,
  useReactFlow,
  ConnectionMode
} from "@xyflow/react"
import { PlayArrow, Widgets, Delete } from "@mui/icons-material"
import type { ComputeBlockNodeType } from "./nodes/ComputeBlockNode";
import ComputeBlockNode from "./nodes/ComputeBlockNode"
import "@xyflow/react/dist/style.css"
import LoadingAndError from "./LoadingAndError"
import EditProjectDraggable from "./EditProjectDraggable"
import EditComputeBlockDraggable from "./EditComputeBlockDraggable"
import type { ComputeBlock, InputOutput } from "@/components/CreateComputeBlockModal";
import CreateComputeBlockModal from "./CreateComputeBlockModal"
import { useDeleteProjectMutation } from "@/mutations/projectMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import type { EdgeDTO } from "@/mutations/computeBlockMutation";
import { useComputeBlocksByProjectQuery, useCreateEdgeMutation, useDeleteEdgeMutation, useUpdateComputeBlockMutation } from "@/mutations/computeBlockMutation"
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
  const { screenToFlowPosition, fitView } = useReactFlow()
  const { setAlert } = useAlert()
  const { mutate: updateBlockMutate } = useUpdateComputeBlockMutation(setAlert, selectedProject?.uuid, true)
  const { mutate: deleteMutate, isPending: deleteLoading } = useDeleteProjectMutation(setAlert)
  const { mutate: deleteEdgeMutate } = useDeleteEdgeMutation(setAlert)
  const { mutateAsync: edgeMutate } = useCreateEdgeMutation(setAlert, selectedProject?.uuid)

  const [nodes, setNodes] = useState<ComputeBlockNodeType[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [selectedEdge, setSelectedEdge] = useState<Edge | undefined>(undefined);
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
    setTimeout(() => {
      fitView();
    }, 50);
  }, [fitView, selectedProject])

  useEffect(() => {
    const onDeleteEdge = () => {
      if (selectedEdge) {
        setEdges((prevEdges) => prevEdges.filter((e) => e.id !== selectedEdge.id))
        setSelectedEdge(undefined);
        deleteEdgeMutate(selectedEdge as EdgeDTO)
      }
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Delete" || event.key === "Backspace") {
        if (selectedEdge) {
          onDeleteEdge();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [selectedEdge, deleteEdgeMutate])

  useEffect(() => {
    if (projectDetails) {
      if (selectedComputeBlock?.id) {
        // If the projectDetails have been updated, and the user currently selected a
        // compute block, update the data of this computeBlock
        setSelectedComputeBlock(projectDetails.blocks.find((block: ComputeBlock) => block.id === selectedComputeBlock.id).data)
      }
      setNodes(projectDetails.blocks)
      setEdges(projectDetails.edges)
    }
  }, [projectDetails, selectedComputeBlock, setSelectedComputeBlock])

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setNodes((nds) => applyNodeChanges(changes, nds) as ComputeBlockNodeType[])
    },
    []
  )

  const onNodeDragStop = useCallback(
    (_: React.SyntheticEvent, node: ComputeBlockNodeType) => {
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
        setAlert("This output is already connected to an input.", AlertType.ERROR)
        return;
      }


      // Proceed with adding the connection if it's not already present
      const sourceNode = nodes.find((node) => node.id === connection.source);
      const targetNode = nodes.find((node) => node.id === connection.target);

      if (sourceNode && targetNode) {
        const sourceHandle = sourceNode.data.selected_entrypoint?.outputs?.find(
          (output: InputOutput) => output.id === connection.sourceHandle
        );
        const targetHandle = targetNode.data.selected_entrypoint?.inputs?.find(
          (input: InputOutput) => input.id === connection.targetHandle
        );

        // Check if types are compatible
        if (sourceHandle && targetHandle) {
          const sourceType = sourceHandle.data_type;
          const targetType = targetHandle.data_type;

          if (sourceType === targetType) {
            edgeMutate(connection as EdgeDTO)
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
          onNodeClick={(_, node: ComputeBlockNodeType) => setSelectedComputeBlock(node.data)}
          onPaneClick={() => setSelectedComputeBlock(undefined)}
          onDragOver={onDragOver}
          onNodeDragStop={onNodeDragStop}
          onDrop={onDrop}
          onConnect={onConnect}
          connectionMode={ConnectionMode.Loose}
          nodesConnectable={true}
          onEdgeClick={(_: React.MouseEvent, edge: Edge) => setSelectedEdge(edge)}
        >
          <Background />
          <Controls position="top-left" />
        </ReactFlow>
      </div>
    </LoadingAndError>
  )
}

