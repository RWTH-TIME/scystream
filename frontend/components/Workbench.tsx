import { type DragEvent, useState, useCallback, useMemo, useEffect } from "react"
import type { Edge, Connection } from "@xyflow/react"
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  useReactFlow,
  ConnectionMode
} from "@xyflow/react"
import { PlayArrow, Widgets, Delete, Share, ExitToApp } from "@mui/icons-material"
import type { ComputeBlockNodeType } from "./nodes/ComputeBlockNode"
import ComputeBlockNode from "./nodes/ComputeBlockNode"
import "@xyflow/react/dist/style.css"
import LoadingAndError from "./LoadingAndError"
import EditProjectDraggable from "./EditProjectDraggable"
import EditComputeBlockDraggable from "./EditComputeBlockDraggable"
import type { InputOutput } from "@/components/CreateComputeBlockModal"
import CreateComputeBlockModal from "./CreateComputeBlockModal"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import type { EdgeDTO } from "@/mutations/computeBlockMutation"
import { useComputeBlocksByProjectQuery, useCreateEdgeMutation, useDeleteEdgeMutation, useUpdateComputeBlockMutation } from "@/mutations/computeBlockMutation"
import { AlertType, useAlert } from "@/hooks/useAlert"
import { useComputeBlockStatusWS } from "@/mutations/workflowMutations"
import { CircularProgress } from "@mui/material"
import type { Project } from "@/utils/types"
import ProjectModals from "./ProjectModals"
import { useProjectModals } from "@/hooks/useProjectModals"
import { useExportProjectMutation } from "@/mutations/projectMutation"

export function useGraphData(selectedProjectUUID: string) {
  const { data: projectDetails, isLoading, isError } = useComputeBlocksByProjectQuery(selectedProjectUUID)
  const [nodes, setNodes] = useState<ComputeBlockNodeType[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [selectedEdge, setSelectedEdge] = useState<Edge | undefined>(undefined)
  const { selectedComputeBlock, setSelectedComputeBlock } = useSelectedComputeBlock()
  const { setAlert } = useAlert()

  useEffect(() => {
    if (projectDetails) {
      setNodes(projectDetails.blocks)
      setEdges(projectDetails.edges)
    }
  }, [projectDetails])

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
    setAlert,
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
  onShareClick: () => void,
  onExportClick: () => void,
  isTriggerLoading: boolean,
  allWorkflowInputsConfigured: boolean,
}

export function ActionButtons({
  onPlayClick,
  onDeleteClick,
  onShareClick,
  onExportClick,
  isTriggerLoading,
  allWorkflowInputsConfigured,
}: ActionButtonsProps) {
  return (
    <div className="flex justify-self-end gap-3">
      <button
        onClick={onExportClick}
        className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full hover:bg-blue-400 transition-all duration-200 cursor-pointer"
      >
        <ExitToApp />
      </button>
      <button
        onClick={onShareClick}
        className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full hover:bg-blue-400 transition-all duration-200 cursor-pointer"
      >
        <Share />
      </button>
      <button
        disabled={isTriggerLoading || !allWorkflowInputsConfigured}
        onClick={onPlayClick}
        className={`flex items-center justify-center w-12 h-12 ${allWorkflowInputsConfigured && !isTriggerLoading
          ? "bg-blue-500 hover:bg-blue-400"
          : "bg-gray-400"
          } text-white rounded-full transition-all duration-200 cursor-pointer disabled:cursor-not-allowed`}
      >
        {isTriggerLoading ? <CircularProgress /> : <PlayArrow />}
      </button>
      <button
        onClick={onDeleteClick}
        className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full hover:bg-blue-400 transition-all duration-200 cursor-pointer"
      >
        <Delete />
      </button>
    </div>
  )
}

type WorkbenchProps = {
  deleteProject: (project_id: string) => void,
  isProjectDeleteLoading: boolean,
  triggerWorkflow: (project_id: string) => void,
  isTriggerWorkflowLoading: boolean,
  project: Project,
}

export function Workbench({
  deleteProject,
  isProjectDeleteLoading,
  triggerWorkflow,
  isTriggerWorkflowLoading,
  project
}: WorkbenchProps) {
  const nodeTypes = useMemo(() => ({ computeBlock: ComputeBlockNode }), [])
  const { setSelectedComputeBlock } = useSelectedComputeBlock()
  const { nodes, edges, selectedEdge, setSelectedEdge, isLoading, isError, setNodes, setAlert } = useGraphData(project.uuid)
  const { screenToFlowPosition, fitView } = useReactFlow()
  const { mutate: deleteEdgeMutate } = useDeleteEdgeMutation(setAlert, project.uuid)
  const { mutateAsync: edgeMutate } = useCreateEdgeMutation(setAlert, project.uuid)
  const { mutate: updateBlockMutate } = useUpdateComputeBlockMutation(setAlert, project.uuid)
  const { mutate: exportProject } = useExportProjectMutation()

  const {
    deleteApproveOpen,
    setDeleteApproveOpen,
    shareModalOpen,
    setShareModalOpen,
    onProjectDelete,
  } = useProjectModals({ deleteProject, project_uuid: project.uuid })

  const [createComputeBlockOpen, setCreateComputeBlockOpen] = useState(false)
  const [dropCoordinates, setDropCoordinates] = useState({ x: 0, y: 0 })

  useComputeBlockStatusWS(setAlert, project.uuid)

  useEffect(() => {
    setTimeout(() => {
      fitView()
    }, 50)
  }, [fitView, project.uuid])

  useEffect(() => {
    const onDeleteEdge = () => {
      if (selectedEdge) {
        setSelectedEdge(undefined)
        deleteEdgeMutate(selectedEdge as EdgeDTO)
      }
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Delete" || event.key === "Backspace") {
        if (selectedEdge) {
          onDeleteEdge()
        }
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [selectedEdge, deleteEdgeMutate, setSelectedEdge])

  const onDragStart = (event: React.DragEvent<HTMLButtonElement>) => {
    event.dataTransfer.effectAllowed = "move"
  }

  const onNodeDragStop = useCallback(
    (_: React.SyntheticEvent, node: ComputeBlockNodeType) => {
      if (!node.position) return
      updateBlockMutate({
        id: node.id,
        x_pos: node.position.x,
        y_pos: node.position.y
      })
    },
    [updateBlockMutate]
  )

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
        (edge) => edge.targetHandle === connection.targetHandle
      )
      if (existingEdge) {
        setAlert("This output is already connected to an input.", AlertType.ERROR)
        return
      }
      const sourceNode = nodes.find((node) => node.id === connection.source)
      const targetNode = nodes.find((node) => node.id === connection.target)
      if (sourceNode && targetNode) {
        const sourceHandle = sourceNode.data.selected_entrypoint?.outputs?.find(
          (output: InputOutput) => output.id === connection.sourceHandle
        )
        const targetHandle = targetNode.data.selected_entrypoint?.inputs?.find(
          (input: InputOutput) => input.id === connection.targetHandle
        )
        if (sourceHandle && targetHandle) {
          const sourceType = sourceHandle.data_type
          const targetType = targetHandle.data_type
          if (sourceType === targetType) {
            edgeMutate(connection as EdgeDTO)
          } else {
            setAlert("Incompatible connection types!", AlertType.ERROR)
          }
        }
      }
    },
    [edges, nodes, setAlert, edgeMutate]
  )

  function onPlayClicked() {
    triggerWorkflow(project.uuid)
  }

  return (
    <LoadingAndError loading={isLoading} error={isError}>
      <ProjectModals
        project={project}
        deleteApproveOpen={deleteApproveOpen}
        setDeleteApproveOpen={setDeleteApproveOpen}
        shareModalOpen={shareModalOpen}
        setShareModalOpen={setShareModalOpen}
        onProjectDelete={onProjectDelete}
        isProjectDeleteLoading={isProjectDeleteLoading}
      />
      <CreateComputeBlockModal
        isOpen={createComputeBlockOpen}
        onClose={() => setCreateComputeBlockOpen(false)}
        dropCoordinates={dropCoordinates}
        project={project}
      />
      {project ? <EditComputeBlockDraggable project={project} /> : <EditProjectDraggable project={project} />}
      <div className="flex absolute justify-between flex-row p-5 gap-3 right-0 bg-inherit z-30">
        <NodeControls onDragStart={onDragStart} />
        <ActionButtons
          onPlayClick={onPlayClicked}
          onExportClick={() => exportProject(project.uuid)}
          onDeleteClick={() => setDeleteApproveOpen(true)}
          onShareClick={() => setShareModalOpen(true)}
          isTriggerLoading={isTriggerWorkflowLoading}
          allWorkflowInputsConfigured={true}
        />
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
