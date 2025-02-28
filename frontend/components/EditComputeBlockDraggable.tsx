import { useState } from "react";
import ProjectCBSettingsDraggable from "./ProjectCBSettingsDraggable";
import EditInputsTab from "@/components/editComputeBlockTabs/EditInputsTab";
import EditOutputsTab from "@/components/editComputeBlockTabs/EditOutputsTab";
import MetadataTab from "./editComputeBlockTabs/MetadataTab";

export default function EditComputeBlockDraggable() {
  const [activeTab, setActiveTab] = useState<string>("metadata");

  const tabs = [
    { key: "metadata", label: "Metadata" },
    { key: "inputs", label: "Inputs" },
    { key: "outputs", label: "Outputs" },
  ];

  return (
    <ProjectCBSettingsDraggable tabs={tabs} activeTab={activeTab} setActiveTab={setActiveTab}>
      {activeTab === "metadata" && <MetadataTab />}
      {activeTab === "inputs" && <EditInputsTab />}
      {activeTab === "outputs" && <EditOutputsTab />}
    </ProjectCBSettingsDraggable>
  );
}

