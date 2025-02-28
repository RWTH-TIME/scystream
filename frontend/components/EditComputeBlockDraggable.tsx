import { useEffect, useState } from "react";
import Input from "./inputs/Input";
import LoadingAndError from "./LoadingAndError";
import ProjectCBSettingsDraggable from "./ProjectCBSettingsDraggable";
import { AlertType, useAlert } from "@/hooks/useAlert";
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock";
import EditInputsTab from "./EditInputsTab";
import EditOutputsTab from "./EditOutputsTab";

export default function EditComputeBlockDraggable() {
  const { setAlert } = useAlert();
  const { selectedComputeBlock } = useSelectedComputeBlock();

  const [cbName, setCBName] = useState<string>(selectedComputeBlock?.custom_name ?? "");
  const [activeTab, setActiveTab] = useState<string>("metadata");

  useEffect(() => {
    setCBName(selectedComputeBlock?.custom_name ?? "");
  }, [selectedComputeBlock]);

  function updateProject(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (selectedComputeBlock && cbName && cbName.length > 0) {
      // TODO: mutate
    } else {
      setAlert("Project Name must be set.", AlertType.ERROR);
    }
  }

  const tabs = [
    { key: "metadata", label: "Metadata" },
    { key: "inputs", label: "Inputs" },
    { key: "outputs", label: "Outputs" },
  ];

  return (
    <ProjectCBSettingsDraggable tabs={tabs} activeTab={activeTab} setActiveTab={setActiveTab}>
      {activeTab === "metadata" && (
        <>
          <h2 className="text-xl font-bold">
            Compute Block <span className="text-blue-600">{selectedComputeBlock?.name}</span> Settings:
          </h2>
          <p className="text-sm text-gray-800">{selectedComputeBlock?.description}</p>

          <form onSubmit={updateProject} className="mt-4 space-y-4 text-sm">
            <Input type="text" value={cbName} label="Name" onChange={setCBName} />

            <div className="flex justify-end">
              <button
                type="submit"
                className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-blue-500 rounded hover:bg-blue-600"
              >
                <LoadingAndError loading={false} iconSize={21}>
                  Save
                </LoadingAndError>
              </button>
            </div>
          </form>
        </>
      )}

      {activeTab === "inputs" && <EditInputsTab />}

      {activeTab === "outputs" && <EditOutputsTab />}
    </ProjectCBSettingsDraggable>
  );
}

