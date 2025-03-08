import { useEffect, useState } from "react";
import ProjectCBSettingsDraggable from "./ProjectCBSettingsDraggable";
import MetadataTab from "@/components/editComputeBlockTabs/MetadataTab";
import EditInputsOutputsTab from "@/components/editComputeBlockTabs/EditInputsOutputsTab";
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock";
import type { ComputeBlock, RecordValueType } from "@/components/CreateComputeBlockModal";
import { useUpdateComputeBlockMutation, type UpdateComputeBlockDTO, type UpdateEntrypointDTO, type UpdateInputOutputDTO } from "@/mutations/computeBlockMutation";
import { useAlert } from "@/hooks/useAlert";
import { useSelectedProject } from "@/hooks/useSelectedProject";

export default function EditComputeBlockDraggable() {
  const { selectedComputeBlock } = useSelectedComputeBlock();
  const { selectedProject } = useSelectedProject();
  const { setAlert } = useAlert();
  const { mutateAsync, isPending } = useUpdateComputeBlockMutation(setAlert, selectedProject?.uuid);

  // We need to make a deep copy of the compute block to compare the values later on
  const [editCB, setEditCB] = useState<ComputeBlock>(JSON.parse(JSON.stringify(selectedComputeBlock!)));
  const [activeTab, setActiveTab] = useState<string>("metadata");

  useEffect(() => {
    setEditCB(JSON.parse(JSON.stringify(selectedComputeBlock)))
  }, [selectedComputeBlock])

  function updateConfig(section: "inputs" | "outputs" | "envs", key: string, value: RecordValueType) {
    setEditCB((prevCB) => {
      if (!prevCB) return prevCB;

      const updatedCB = { ...prevCB };

      if (section === "envs") {
        updatedCB.selected_entrypoint.envs = {
          ...updatedCB.selected_entrypoint.envs,
          [key]: value
        }
      } else {
        updatedCB.selected_entrypoint[section] = updatedCB.selected_entrypoint[section].map((io) => {
          if (key in io.config) {
            return {
              ...io,
              config: {
                ...io.config,
                [key]: value,
              },
            };
          }
          return io;
        });
      }
      return updatedCB;
    });
  }

  function updateCustomName(newName: string) {
    setEditCB((prevCB) => {
      return { ...prevCB, custom_name: newName };
    });
  }

  function buildUpdateDTO(): Partial<UpdateComputeBlockDTO> {
    if (!selectedComputeBlock) return {};

    const updateDTO: UpdateComputeBlockDTO = { id: editCB.id };

    if (editCB.custom_name !== selectedComputeBlock.custom_name) {
      updateDTO.custom_name = editCB.custom_name;
    }

    const updatedEntrypoint: UpdateEntrypointDTO = {
      id: editCB.selected_entrypoint.id!,
    };

    const updatedInputs = editCB.selected_entrypoint.inputs
      .filter((input) => {
        const originalInput = selectedComputeBlock.selected_entrypoint.inputs.find(i => i.id === input.id);
        return !originalInput || JSON.stringify(input.config) !== JSON.stringify(originalInput.config);
      })
      .map((input) => ({
        id: input.id,
        config: input.config,
      } as UpdateInputOutputDTO));

    if (updatedInputs.length > 0) {
      updatedEntrypoint.inputs = updatedInputs;
    }

    const updatedOutputs = editCB.selected_entrypoint.outputs
      .filter((output) => {
        const originalOutput = selectedComputeBlock.selected_entrypoint.outputs.find(o => o.id === output.id);
        return !originalOutput || JSON.stringify(output.config) !== JSON.stringify(originalOutput.config);
      })
      .map((output) => ({
        id: output.id,
        config: output.config,
      } as UpdateInputOutputDTO));

    if (updatedOutputs.length > 0) {
      updatedEntrypoint.outputs = updatedOutputs;
    }

    const updatedEnvs: Record<string, RecordValueType> = {};
    Object.keys(editCB.selected_entrypoint.envs).forEach((key) => {
      if (editCB.selected_entrypoint.envs[key] !== selectedComputeBlock.selected_entrypoint.envs[key]) {
        updatedEnvs[key] = editCB.selected_entrypoint.envs[key];
      }
    });

    if (Object.keys(updatedEnvs).length > 0) {
      updatedEntrypoint.envs = updatedEnvs;
    }

    if (Object.keys(updatedEntrypoint).length > 1) {
      updateDTO.selected_entrypoint = updatedEntrypoint;
    }

    return updateDTO;
  }

  async function handleSave() {
    const dto = buildUpdateDTO();
    await mutateAsync(dto);
  }

  const tabs = [
    { key: "metadata", label: "Metadata" },
    { key: "inputs", label: "Inputs" },
    { key: "outputs", label: "Outputs" },
  ];

  return (
    <ProjectCBSettingsDraggable tabs={tabs} activeTab={activeTab} setActiveTab={setActiveTab}>
      {activeTab === "metadata" && (
        <MetadataTab
          computeBlock={editCB}
          updateCustomName={updateCustomName}
          updateConfig={(key, value) => updateConfig("envs", key, value)}
          handleSave={handleSave}
          loading={isPending}
        />
      )}
      {activeTab === "inputs" && (
        <EditInputsOutputsTab
          inputoutputs={editCB.selected_entrypoint.inputs}
          updateConfig={(key, value) => updateConfig("inputs", key, value)}
          handleSave={handleSave}
          loading={isPending}
          type="Input"
        />
      )}
      {activeTab === "outputs" && (
        <EditInputsOutputsTab
          inputoutputs={editCB.selected_entrypoint.outputs}
          updateConfig={(key, value) => updateConfig("outputs", key, value)}
          handleSave={handleSave}
          loading={isPending}
          type="Output"
        />
      )}
    </ProjectCBSettingsDraggable>
  );
}

