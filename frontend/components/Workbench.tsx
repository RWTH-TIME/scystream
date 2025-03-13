import type { DragEvent } from "react"
import { useState, useCallback, useMemo, useEffect } from "react"
import type { Edge, Connection } from "@xyflow/react"
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
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
import { useComputeBlocksByProjectQuery, useCreateEdgeMutation, useDeleteEdgeMutation, useUpdateComputeBlockCoords } from "@/mutations/computeBlockMutation"
import { AlertType, useAlert } from "@/hooks/useAlert"
import DeleteModal from "./DeleteModal"


function useGraphData(selectedProjectUUID: string | undefined) {
  const { data: projectDetails, isLoading, isError } = useComputeBlocksByProjectQuery(selectedProjectUUID)
  const [nodes, setNodes] = useState<ComputeBlockNodeType[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [selectedEdge, setSelectedEdge] = useState<Edge | undefined>(undefined)
  const { selectedComputeBlock, setSelectedComputeBlock } = useSelectedComputeBlock()
  const { setAlert } = useAlert();

  useEffect(() => {
    if (projectDetails) {
      setNodes(projectDetails.blocks)
      setEdges(projectDetails.edges)
      if (selectedComputeBlock?.id) {
        // If the projectDetails have been updated, and the user currently selected a
        // compute Block, update the data of the selectedCompute block. It might have changed
        setSelectedComputeBlock(projectDetails.blocks.find((block: ComputeBlock) => block.id === selectedComputeBlock.id).data)
      }

    }
  }, [projectDetails, selectedComputeBlock, setSelectedComputeBlock])

  return {
    nodes,
    edges,
    selectedEdge,
    selectedComputeBlock,
    setSelectedComputeBlock,
    isLoading,
    isError,
    setNodes,
    setEdges,
    setSelectedEdge,
    setAlert
  }
}

type NodeControlProps = {
  onDragStart: React.DragEventHandler<HTMLButtonElement>,
}

function NodeControls({ onDragStart }: NodeControlProps) {
  return (
    <div className="justify-self-start h-12 flex flex-col items-start p-1 bg-white rounded-lg shadow-lg space-y-3">
      <button
        onClick={() => console.log("Add Component clicked")}
        className="p-2 bg-gray-100 rounded-md text-gray-800 hover:bg-gray-200 transition-all duration-200"
        onDragStart={onDragStart}
        draggable
      >
        <Widgets fontSize="small" />
      </button>
    </div>
  )
}

type ActionButtonsProps = {
  onPlayClick: () => void,
  onDeleteClick: () => void,
}

function ActionButtons({ onPlayClick, onDeleteClick }: ActionButtonsProps) {
  return (
    <div className="flex justify-self-end gap-3">
      <button
        onClick={onPlayClick}
        className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full hover:bg-blue-400 transition-all duration-200"
      >
        <PlayArrow />
      </button>
      <button
        onClick={onDeleteClick}
        className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full hover:bg-blue-400 transition-all duration-200"
      >
        <Delete />
      </button>
    </div>
  )
}

export function Workbench() {
  const nodeTypes = useMemo(() => ({ computeBlock: ComputeBlockNode }), [])
  const { selectedProject, setSelectedProject } = useSelectedProject()
  const { selectedComputeBlock, setSelectedComputeBlock } = useSelectedComputeBlock()

  const { nodes, edges, selectedEdge, setSelectedEdge, isLoading, isError, setNodes, setAlert } = useGraphData(selectedProject?.uuid)

  const { screenToFlowPosition, fitView } = useReactFlow()

  const { mutate: deleteMutate, isPending: deleteLoading } = useDeleteProjectMutation(setAlert)
  const { mutate: deleteEdgeMutate } = useDeleteEdgeMutation(setAlert, selectedProject?.uuid)
  const { mutateAsync: edgeMutate } = useCreateEdgeMutation(setAlert, selectedProject?.uuid)
  const { mutate: updateBlockMutate } = useUpdateComputeBlockCoords(setAlert, selectedProject?.uuid)

  const [deleteApproveOpen, setDeleteApproveOpen] = useState(false);
  const [createComputeBlockOpen, setCreateComputeBlockOpen] = useState(false);
  const [dropCoordinates, setDropCoordinates] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setTimeout(() => {
      fitView();
    }, 50);
  }, [fitView, selectedProject])

  useEffect(() => {
    const onDeleteEdge = () => {
      if (selectedEdge) {
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
  }, [selectedEdge, deleteEdgeMutate, setSelectedEdge])


  function onProjectDelete() {
    if (selectedProject) {
      deleteMutate(selectedProject.uuid)
      setDeleteApproveOpen(false)
      setSelectedProject(undefined)
    }
  }

  const onDragStart = (event: React.DragEvent<HTMLButtonElement>) => {
    event.dataTransfer.effectAllowed = "move";
  };

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
    return <div>Select a Project!</div>
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
        <NodeControls onDragStart={onDragStart} />
        <ActionButtons onPlayClick={() => console.log("Play clicked")} onDeleteClick={() => setDeleteApproveOpen(true)} />
      </div>

      <div className="h-full">
        <ReactFlow
          nodeTypes={nodeTypes}
          nodes={nodes}
          edges={edges}
          onNodesChange={(changes) => setNodes((nds) => applyNodeChanges(changes, nds))}
          onNodeClick={(_, node) => setSelectedComputeBlock(node.data)}
          onPaneClick={() => setSelectedComputeBlock(undefined)}
          onDragOver={onDragOver}
          onNodeDragStop={onNodeDragStop}
          onEdgeClick={(_, edge) => setSelectedEdge(edge)}
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
