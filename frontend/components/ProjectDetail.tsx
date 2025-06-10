import { useSelectedProject } from "@/hooks/useSelectedProject"
import { ActionButtons } from "./Workbench"
import DeleteModal from "./DeleteModal"
import { useEffect, useState } from "react"
import { useGetComputeBlocksConfigurationByProjectQuery } from "@/mutations/workflowMutations"
import { ProjectStatusIndicator } from "./ProjectStatusIndicator"
import { ProjectStatus } from "@/utils/types"
import ConfigBox, { ConfigBoxVariant } from "./ConfigBox"
import LoadingAndError from "./LoadingAndError"
import type { InputOutput, RecordValueType } from "./CreateComputeBlockModal"
import ConfigEnvsInputs from "./inputs/ConfigEnvsInputs"
import { Save } from "@mui/icons-material"

type ProjectDetailProps = {
  deleteProject: (project_id: string) => void,
  isProjectDeleteLoading: boolean,
  triggerWorkflow: (project_id: string) => void,
  isTriggerWorkflowLoading: boolean,
}

type WorkflowEnvType = {
  block_uuid: string,
  block_custom_name: string,
  envs: Record<string, RecordValueType>,
}
type ProjectDetailFormType = {
  name: string,
  envs: WorkflowEnvType[],
  workflow_inputs: InputOutput[],
  workflow_outputs: InputOutput[],
  workflow_intermediates: InputOutput[],
}

const emptyProjectDetailForm: ProjectDetailFormType = {
  name: "",
  envs: [],
  workflow_inputs: [],
  workflow_outputs: [],
  workflow_intermediates: []
}

export default function ProjectDetail({
  deleteProject,
  isProjectDeleteLoading,
  triggerWorkflow,
  isTriggerWorkflowLoading
}: ProjectDetailProps) {
  const { selectedProject, setSelectedProject } = useSelectedProject()
  const [deleteApproveOpen, setDeleteApproveOpen] = useState(false)
  const [intermediatesExpanded, setIntermediatesExpanded] = useState(false)

  const { data, isLoading, isError } = useGetComputeBlocksConfigurationByProjectQuery(selectedProject?.uuid)

  const [projectDetailForm, setProjectDetailForm] = useState<ProjectDetailFormType>(emptyProjectDetailForm)
  const [initialProjectDetailForm, setInitialProjectDetailForm] = useState<ProjectDetailFormType>(emptyProjectDetailForm)

  const hasChanged = JSON.stringify(projectDetailForm) !== JSON.stringify(initialProjectDetailForm)

  function handleFieldConfigChange(
    field: "envs" | "workflow_inputs" | "workflow_outputs" | "workflow_intermediates",
    key: string,
    value: RecordValueType,
    identifier?: string
  ) {
    setProjectDetailForm((prev) => {
      return {
        ...prev,
        [field]: prev[field].map((item) => {
          if (field === "envs") {
            // Handle Envs
            const envItem = item as WorkflowEnvType
            if (envItem.block_uuid !== identifier) return envItem

            return {
              ...envItem,
              envs: {
                ...envItem.envs,
                [key]: value,
              },
            }
          } else {
            // Handle InputOutputs
            const ioItem = item as InputOutput
            if (ioItem.id !== identifier) return ioItem

            return {
              ...ioItem,
              config: {
                ...ioItem.config,
                [key]: value,
              },
            }
          }
        }),
      }
    })
  }

  // TODO:
  // Take care of File Changes aswell
  // Implement Endpoint for mutation
  // Fix Intermediate UI (Show configs/Uploads/Downloads)
  // Fix Upload/Download File UI
  // Display Block Name In front of io


  useEffect(() => {
    if (data && selectedProject) {
      const newForm: ProjectDetailFormType = {
        name: selectedProject.name,
        envs: data.envs,
        workflow_inputs: data.workflow_inputs,
        workflow_outputs: data.workflow_outputs,
        workflow_intermediates: data.workflow_intermediates
      }

      setProjectDetailForm(newForm)
      setInitialProjectDetailForm(newForm)
    }
  }, [data, selectedProject])

  function onProjectDelete() {
    deleteProject(selectedProject!.uuid)
    setDeleteApproveOpen(false)
    setSelectedProject(undefined)
  }

  return (
    <div className="flex flex-col h-full px-4 py-4 space-y-4">
      <DeleteModal
        isOpen={deleteApproveOpen}
        onClose={() => setDeleteApproveOpen(false)}
        onDelete={onProjectDelete}
        loading={isProjectDeleteLoading}
        header="Delete Project"
        desc={`Are you sure you want to delete the project: ${selectedProject?.name}?`}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-lg font-semibold">Project:</span>
          <span className="text-lg font-semibold text-blue-500">{selectedProject?.name}</span>
        </div>

        <div className="flex items-center space-x-2">
          <ProjectStatusIndicator s={selectedProject?.status ?? ProjectStatus.IDLE} />
        </div>

        <div className="flex justify-between gap-3">
          <button
            disabled={!hasChanged}
            onClick={() => { }}
            className={`flex items-center justify-center w-12 h-12 ${hasChanged ? "bg-blue-500 hover:bg-blue-400" : "bg-gray-400"} text-white rounded-full transition-all duration-200 cursor-pointer disabled:cursor-not-allowed`}
          >
            {<Save />}
          </button>
          <ActionButtons
            onPlayClick={() => triggerWorkflow(selectedProject!.uuid)}
            onDeleteClick={() => setDeleteApproveOpen(true)}
            isTriggerLoading={isTriggerWorkflowLoading}
          />
        </div>
      </div>

      <div className="border-t border-gray-200" />

      {/* Configs */}
      <div className="border rounded p-4 bg-white">
        <p className="text-lg font-semibold mb-4">Workflow Configurations</p>
        <LoadingAndError loading={isLoading} error={isError}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projectDetailForm.envs.map((item: WorkflowEnvType) => (
              <div
                key={item.block_uuid}
                className="border p-4"
              >
                <p className="text-md font-semibold">
                  Block: <span className="font-semibold">{item.block_custom_name}</span>
                </p>
                <ConfigEnvsInputs
                  pairs={item.envs}
                  onUpdate={(key, value) => handleFieldConfigChange("envs", key, value, item.block_uuid)}
                  configVariant={ConfigBoxVariant.SIMPLE}
                  borderEnabled={false}
                />
              </div>
            ))}
          </div>
        </LoadingAndError>
      </div>


      <div className="border-t border-gray-200" />

      {/* Inputs + Outputs */}
      <div className="flex gap-4">
        <div className="w-1/2">
          <div className="border p-4">
            <LoadingAndError loading={isLoading} error={isError}>
              <ConfigBox
                headline="Workflow Inputs"
                description="Upload files or configure the required Inputs"
                config={projectDetailForm.workflow_inputs}
                updateConfig={(key, value, id) => { handleFieldConfigChange("workflow_inputs", key, value, id) }}
                updateSelectedFile={() => { }}
                variant={ConfigBoxVariant.SIMPLE}
              />
            </LoadingAndError>
          </div>
        </div>
        <div className="w-1/2">
          <div className="border p-4">
            <LoadingAndError loading={isLoading} error={isError}>
              <ConfigBox
                headline="Workflow Outputs"
                description="Outputs of the workflow, download the workflow outputs here"
                config={projectDetailForm.workflow_outputs}
                updateConfig={(key, value, id) => { handleFieldConfigChange("workflow_outputs", key, value, id) }}
                updateSelectedFile={() => { }}
                variant={ConfigBoxVariant.SIMPLE}
              />
            </LoadingAndError>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200" />

      <div className="border">
        <LoadingAndError loading={isLoading} error={isError}>
          <div className="p-2">
            <button
              onClick={() => setIntermediatesExpanded(prev => !prev)}
              className="mb-2 px-4 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              {intermediatesExpanded ? "Collapse" : "Expand"} Intermediates
            </button>

            {intermediatesExpanded && (
              <ConfigBox
                headline="Intermediates"
                description="I/O Configs of Intermediates"
                config={projectDetailForm.workflow_intermediates}
                updateConfig={(key, value, id) => { handleFieldConfigChange("workflow_intermediates", key, value, id) }}
                updateSelectedFile={() => { }}
                // TODO: In simple mode, when type File, if one config key is unconfigured, the File *Input* must be shown
                // TODO: In simple mode, show unconfigured Fields for File Outputs aswell
                variant={ConfigBoxVariant.COMPLEX}
              />
            )}
          </div>
        </LoadingAndError>
      </div>
    </div>
  )
}

