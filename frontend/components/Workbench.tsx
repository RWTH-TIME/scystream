import { useState, useCallback, useMemo, useEffect } from "react"
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges
} from "@xyflow/react"
import { PlayArrow, Widgets, Save, Delete, Edit } from "@mui/icons-material"
import ComputeBlockNode from "./nodes/ComputeBlockNode"
import "@xyflow/react/dist/style.css"
import LoadingAndError from "./LoadingAndError"
import DeleteProjectModal from "./DeleteProjectModal"
import EditProjectModal from "./EditProjectModal"
import type { Node } from "@/mutations/projectMutation"
import { useProjectDetailsQuery } from "@/mutations/projectMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"

/*
* The Workbench Component is used to display & edit the DAGs.
*/
export default function Workbench() {
  const nodeTypes = useMemo(() => ({ computeBlock: ComputeBlockNode }), [])
  const { selectedProject } = useSelectedProject()
  const { data: projectDetails, isLoading, isError } = useProjectDetailsQuery(selectedProject?.uuid)

  const [nodes, setNodes] = useState<Node[]>([])
  const [deleteApproveOpen, setDeleteApproveOpen] = useState<boolean>(false)
  const [editProjectOpen, setEditProjectOpen] = useState<boolean>(false)

  useEffect(() => {
    if (projectDetails) {
      setNodes(projectDetails)
    }
  }, [projectDetails])

  // TODO:
  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  )

  if (!selectedProject) {
    return (<div>Select a Project</div>)
  }

  return (
    <LoadingAndError loading={isLoading} error={isError}>
      <DeleteProjectModal isOpen={deleteApproveOpen} onClose={() => setDeleteApproveOpen(false)} />
      <EditProjectModal isOpen={editProjectOpen} onClose={() => setEditProjectOpen(false)} />
      <div className="flex absolute justify-between justify-between flex-row p-5 gap-3 right-0 bg-inherit z-30">
        <div className="justify-self-start h-12 flex flex-col items-start p-1 bg-white rounded-lg shadow-lg space-y-3">
          <button
            onClick={() => console.log("Add Component clicked")}
            className="p-2 bg-gray-100 rounded-md text-gray-800 hover:bg-gray-200 transition-all duration-200"
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
          <button
            onClick={() => setEditProjectOpen(true)}
            className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full hover:bg-blue-400 transition-all duration-200"
          >
            <Edit />
          </button>
        </div>
      </div>
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
