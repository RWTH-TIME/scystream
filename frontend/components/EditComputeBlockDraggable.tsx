import { useState } from "react"
import ProjectCBSettingsDraggable from "./ProjectCBSettingsDraggable"
import MetadataTab from "@/components/editComputeBlockTabs/MetadataTab"
import EditInputsOutputsTab from "@/components/editComputeBlockTabs/EditInputsOutputsTab"
import { IOType } from "@/components/CreateComputeBlockModal"

export default function EditComputeBlockDraggable() {
  const [activeTab, setActiveTab] = useState<string>("metadata")

  const tabs = [
    { key: "metadata", label: "Metadata" },
    { key: "inputs", label: "Inputs" },
    { key: "outputs", label: "Outputs" },
  ]

  return (
    <ProjectCBSettingsDraggable tabs={tabs} activeTab={activeTab} setActiveTab={setActiveTab}>
      {activeTab === "metadata" && (
        <MetadataTab />
      )}
      {activeTab === "inputs" && (
        <EditInputsOutputsTab
          type={IOType.INPUT}
        />
      )}
      {activeTab === "outputs" && (
        <EditInputsOutputsTab
          type={IOType.OUTPUT}
        />
      )}
    </ProjectCBSettingsDraggable>
  )
}

