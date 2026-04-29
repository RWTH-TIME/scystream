import { useState } from "react"
import ProjectCBSettingsDraggable from "./ProjectCBSettingsDraggable"
import MetadataTab from "@/components/editComputeBlockTabs/MetadataTab"
import EditInputsOutputsTab from "@/components/editComputeBlockTabs/EditInputsOutputsTab"
import { IOType } from "@/components/CreateComputeBlockModal"
import type { Project } from "@/utils/types"

const TABS = [
  { key: "metadata", label: "Metadata" },
  { key: "inputs", label: "Inputs" },
  { key: "outputs", label: "Outputs" },
]

type EditComputeBlockDraggableProps = {
  project: Project,
}

export default function EditComputeBlockDraggable({ project }: EditComputeBlockDraggableProps) {
  const [activeTab, setActiveTab] = useState<string>("metadata")

  return (
    <ProjectCBSettingsDraggable tabs={TABS} activeTab={activeTab} setActiveTab={setActiveTab}>
      {activeTab === "metadata" && (
        <MetadataTab projectId={project.uuid} />
      )}
      {activeTab === "inputs" && (
        <EditInputsOutputsTab
          type={IOType.INPUT}
          project={project}
        />
      )}
      {activeTab === "outputs" && (
        <EditInputsOutputsTab
          type={IOType.OUTPUT}
          project={project}
        />
      )}
    </ProjectCBSettingsDraggable>
  )
}

