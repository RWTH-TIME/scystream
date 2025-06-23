import { useSelectedProject } from "@/hooks/useSelectedProject"
import { ActionButtons } from "./Workbench"
import DeleteModal from "./DeleteModal"
import { useEffect, useState } from "react"
import type { SimpleUpdateEnvsDTO, SimpleUpdateIOSDTO, UpdateWorkflowConfigurationsDTO } from "@/mutations/workflowMutations"
import { useGetComputeBlocksConfigurationByProjectQuery, useUpdateWorkflowConfigurationsMutation } from "@/mutations/workflowMutations"
import { ProjectStatusIndicator } from "./ProjectStatusIndicator"
import { ProjectStatus } from "@/utils/types"
import ConfigBox, { ConfigBoxVariant } from "./ConfigBox"
import LoadingAndError from "./LoadingAndError"
import { encodeFileToBase64, type InputOutput, type RecordValueType } from "./CreateComputeBlockModal"
import ConfigEnvsInputs from "./inputs/ConfigEnvsInputs"
import { Save } from "@mui/icons-material"
import { useAlert } from "@/hooks/useAlert"
import { CircularProgress } from "@mui/material"

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
  const { setAlert } = useAlert()

  const { data, isLoading, isError } = useGetComputeBlocksConfigurationByProjectQuery(selectedProject?.uuid)
  const { mutateAsync, isPending: loadingUpdateConfigs } = useUpdateWorkflowConfigurationsMutation(setAlert, selectedProject!.uuid)

  const [projectDetailForm, setProjectDetailForm] = useState<ProjectDetailFormType>(emptyProjectDetailForm)
  const [initialProjectDetailForm, setInitialProjectDetailForm] = useState<ProjectDetailFormType>(emptyProjectDetailForm)

  const [modifiedEnvKeys, setModifiedEnvKeys] = useState<Map<string, Set<string>>>(new Map()) // block_uuid -> changed keys
  const [modifiedIOKeys, setModifiedIOKeys] = useState<Map<string, Set<string>>>(new Map()) // io.id -> changed keys
  const [changedIOFiles, setChangedIOFiles] = useState<Set<string>>(new Set()) // io.id with changed files

  const hasChanged = JSON.stringify(projectDetailForm) !== JSON.stringify(initialProjectDetailForm)

  useEffect(() => {
    console.log("SELECTED", selectedProject)
  }, [selectedProject])

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

            setModifiedEnvKeys((prevMap) => {
              const newMap = new Map(prevMap)
              const keys = newMap.get(envItem.block_uuid) ?? new Set()
              keys.add(key)
              newMap.set(envItem.block_uuid, keys)
              return newMap
            })

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

            setModifiedIOKeys((prevMap) => {
              const newMap = new Map(prevMap)
              const keys = newMap.get(ioItem.id!) ?? new Set()
              keys.add(key)
              newMap.set(ioItem.id!, keys)
              return newMap
            })

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

  function handleFileChange(
    field: "workflow_inputs" | "workflow_outputs" | "workflow_intermediates",
    _: string,
    file?: File,
    identifier?: string
  ) {
    setProjectDetailForm((prev) => {
      return {
        ...prev,
        [field]: prev[field].map((item) => {
          const ioItem = item as InputOutput
          if (ioItem.id !== identifier) return ioItem

          setChangedIOFiles((prev) => new Set(prev).add(ioItem.id!))

          return {
            ...ioItem,
            selected_file: file ?? undefined,
          }
        })
      }
    })
  }

  async function getChangedPayload() {
    const payload: UpdateWorkflowConfigurationsDTO = {}

    // 1. Project Name
    if (initialProjectDetailForm.name !== projectDetailForm.name) {
      payload.project_name = projectDetailForm.name
    }

    // 2. Envs
    const envsPayload = Array.from(modifiedEnvKeys.entries()).map(([block_uuid, keys]) => {
      const current = projectDetailForm.envs.find(e => e.block_uuid === block_uuid)
      if (!current) return null

      const changedEnvs: Record<string, RecordValueType> = {}
      keys.forEach(key => {
        changedEnvs[key] = current.envs[key]
      })

      return { block_uuid, envs: changedEnvs }
    }).filter(Boolean) as SimpleUpdateEnvsDTO[]

    // 3. IOs (inputs + outputs + intermediates)
    const allIOs = [
      ...projectDetailForm.workflow_inputs,
      ...projectDetailForm.workflow_outputs,
      ...projectDetailForm.workflow_intermediates,
    ]

    const iosPayload = (await Promise.all(
      allIOs.map(async (io) => {
        const changedKeys = modifiedIOKeys.get(io.id!) ?? new Set()
        const hasFileChanged = changedIOFiles.has(io.id!)

        const config: Record<string, RecordValueType> = {}
        changedKeys.forEach(key => {
          config[key] = io.config[key]
        })

        if (changedKeys.size > 0 || hasFileChanged) {
          return {
            id: io.id,
            config: changedKeys.size > 0 ? config : {},
            selected_file_b64: hasFileChanged && io.selected_file
              ? await encodeFileToBase64(io.selected_file)
              : undefined,
            selected_file_type: hasFileChanged && io.selected_file
              ? io.selected_file.name.split(".").pop()?.toLowerCase()
              : undefined,
          }
        }

        return null
      })
    )).filter(Boolean) as SimpleUpdateIOSDTO[]

    payload.ios = iosPayload
    payload.envs = envsPayload

    return payload
  }


  async function onSave() {
    const payload = await getChangedPayload()
    mutateAsync(payload)
  }


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
          <ProjectStatusIndicator s={selectedProject?.status || ProjectStatus.IDLE} />
        </div>

        <div className="flex justify-between gap-3">
          <button
            disabled={!hasChanged}
            onClick={onSave}
            className={`flex items-center justify-center w-12 h-12 ${hasChanged ? "bg-blue-500 hover:bg-blue-400" : "bg-gray-400"} text-white rounded-full transition-all duration-200 cursor-pointer disabled:cursor-not-allowed`}
          >
            {loadingUpdateConfigs ? <CircularProgress /> : <Save />}
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
                description="Provide the Data for the Workflows Entrypoints"
                config={projectDetailForm.workflow_inputs}
                updateConfig={(key, value, id) => { handleFieldConfigChange("workflow_inputs", key, value, id) }}
                updateSelectedFile={(name, file, id) => { handleFileChange("workflow_inputs", name, file, id) }}
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
                description="Download or Configure the Locations of the Workflows Outputs"
                config={projectDetailForm.workflow_outputs}
                updateConfig={(key, value, id) => { handleFieldConfigChange("workflow_outputs", key, value, id) }}
                updateSelectedFile={(name, file, id) => { handleFileChange("workflow_outputs", name, file, id) }}
                variant={ConfigBoxVariant.SIMPLE}
              />
            </LoadingAndError>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200" />

      {projectDetailForm.workflow_intermediates.length > 0 && (
        <div className="border p-4 bg-gray-50">
          <LoadingAndError loading={isLoading} error={isError}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <h2 className="text-lg font-semibold">Intermediate I/Os</h2>
                <p className="text-sm text-gray-600">
                  These are configurations for block I/Os that are neither workflow inputs nor final outputs.
                </p>
              </div>
              <button
                onClick={() => setIntermediatesExpanded(prev => !prev)}
                className="text-sm px-3 py-1 rounded border border-gray-300 bg-white hover:bg-gray-100 transition"
              >
                {intermediatesExpanded ? "Collapse" : "Expand"}
              </button>
            </div>

            {intermediatesExpanded && (
              <ConfigBox
                headline="Intermediates"
                description="Configure intermediate I/O parameters used within your workflow."
                config={projectDetailForm.workflow_intermediates}
                updateConfig={(key, value, id) => {
                  handleFieldConfigChange("workflow_intermediates", key, value, id)
                }}
                updateSelectedFile={(name, file, id) => {
                  handleFileChange("workflow_intermediates", name, file, id)
                }}
                variant={ConfigBoxVariant.SIMPLE}
              />
            )}
          </LoadingAndError>
        </div>
      )}
    </div>
  )
}

