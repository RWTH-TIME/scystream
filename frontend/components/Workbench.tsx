import { useState, useCallback, useMemo, useEffect } from "react"
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges
} from "@xyflow/react"
import { PlayArrow, Widgets, Save, Delete } from "@mui/icons-material"
import ComputeBlockNode from "./nodes/ComputeBlockNode"
import "@xyflow/react/dist/style.css"
import LoadingAndError from "./LoadingAndError"
import Modal from "./Modal"
import type { Node } from "@/mutations/projectMutation"
import { useProjectDetailsQuery, useDeleteProjectMutation } from "@/mutations/projectMutation"
import { useAlert } from "@/hooks/useAlert"
import { useSelectedProject } from "@/hooks/useSelectedProject"

/*
* The Workbench Component is used to display & edit the DAGs.
*/
export default function Workbench() {
  const nodeTypes = useMemo(() => ({ computeBlock: ComputeBlockNode }), [])
  const { setAlert } = useAlert()
  const { selectedProject, setSelectedProject } = useSelectedProject()
  const { data: projectDetails, isLoading, isError } = useProjectDetailsQuery(selectedProject?.uuid)
  const { mutate: deleteMutate, isPending: deleteLoading } = useDeleteProjectMutation(setAlert)

  const [nodes, setNodes] = useState<Node[]>([])
  const [deleteApproveOpen, setDeleteApproveOpen] = useState<boolean>(false)

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

  function onDelete() {
    if (selectedProject) {
      deleteMutate(selectedProject.uuid)
      setDeleteApproveOpen(false)
      setSelectedProject(undefined)
    }
  }

  function onClose() {
    setDeleteApproveOpen(false)
  }

  if (!selectedProject) {
    return (<div>Select a Project</div>)
  }

  return (
    <LoadingAndError loading={isLoading} error={isError}>
      <Modal className="test" isOpen={deleteApproveOpen} onClose={onClose}>
        <h2 className="text-xl font-bold">Delete Project</h2>
        Are you sure that you want to delete the project: <span className="text-blue-600"><b>{selectedProject.name}</b></span>
        <div className="flex justify-end mt-5">
          <button
            type="button"
            onClick={onClose}
            className="w-[78px] h-[36px] px-4 py-2 mr-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-red-500 rounded hover:bg-red-600"
            disabled={deleteLoading}
            onClick={onDelete}
          >
            <LoadingAndError loading={deleteLoading} iconSize={21}>
              Delete
            </LoadingAndError>
          </button>
        </div>

      </Modal>
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
