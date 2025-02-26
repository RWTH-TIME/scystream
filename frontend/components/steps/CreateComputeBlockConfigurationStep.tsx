import type { InputOutput, PageProps, RecordValueType } from "@/components/CreateComputeBlockModal";
import LoadingAndError from "@/components/LoadingAndError";
import ConfigBox from "../ConfigBox";
import { useEffect, useState } from "react";

function isValid(value: RecordValueType) {
  if (value === null || value === undefined) return false;
  if (Array.isArray(value) && value.length === 0) return false;
  if (typeof value === "number" && isNaN(value)) return false;
  return true;
}

function validateSection(
  section: Record<string, RecordValueType> | InputOutput[],
  sectionType: "envs" | "inputs" | "outputs"
) {
  if (sectionType === "envs") {
    return Object.values(section as Record<string, RecordValueType>).every(isValid);
  } else {
    return (section as InputOutput[]).every((item) =>
      Object.values(item.config).every(isValid)
    );
  }
}


export default function CreateComputeBlockConfigurationStep({
  onNext,
  onPrev,
  selectedEntrypoint,
  computeBlock,
  setComputeBlock,
  setSelectedEntrypoint,
  loading
}: PageProps) {
  const [formValid, setFormValid] = useState<boolean>(false)

  function updateConfig(section: "envs" | "inputs" | "outputs", key: string, value: RecordValueType) {
    if (!selectedEntrypoint || !setSelectedEntrypoint) return;

    setSelectedEntrypoint((prevEntrypoint) => {
      if (!prevEntrypoint) return prevEntrypoint;

      const updatedEntrypoint = { ...prevEntrypoint };

      if (section === "envs") {
        updatedEntrypoint.envs = {
          ...updatedEntrypoint.envs,
          [key]: value
        };
      } else {
        // This assumes, that keys are unique across inputs/outputs, which makes sense as
        // env variable names must be unique. (See SDK docs)
        updatedEntrypoint[section] = updatedEntrypoint[section].map((io) => {
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
      return updatedEntrypoint;
    });
  }

  function handleCustomNameChange(value: string) {
    if (!setComputeBlock) return

    setComputeBlock((prev) => ({ ...prev, custom_name: value }))
  }

  useEffect(() => {
    function validateForm() {
      if (!computeBlock?.custom_name.trim()) {
        setFormValid(false);
        return;
      }

      const isEnvsValid = selectedEntrypoint?.envs ? validateSection(selectedEntrypoint.envs, "envs") : true;
      const isInputsValid = selectedEntrypoint?.inputs ? validateSection(selectedEntrypoint.inputs, "inputs") : true;
      const isOutputsValid = selectedEntrypoint?.outputs ? validateSection(selectedEntrypoint.outputs, "outputs") : true;

      setFormValid(isEnvsValid && isInputsValid && isOutputsValid);
    }
    validateForm();
  }, [computeBlock?.custom_name, selectedEntrypoint])


  return (
    <div className="mt-4 space-y-6 text-sm">
      <div className="p-4 border rounded">
        <label className="block text-gray-700 font-bold mb-1">Custom Name</label>
        <input
          type="text"
          value={computeBlock?.custom_name || ""}
          onChange={(e) => handleCustomNameChange(e.target.value)}
          placeholder="Enter a custom name"
          className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {selectedEntrypoint?.envs && (
        <ConfigBox
          headline="Environment Variables"
          description="Configure the Compute Blocks environment here"
          config={selectedEntrypoint?.envs}
          updateComputeBlock={(key, value) => updateConfig("envs", key, value)}
        />
      )}

      {selectedEntrypoint?.inputs && (
        <ConfigBox
          headline="Inputs"
          description="Configure the Compute Blocks inputs here"
          config={selectedEntrypoint?.inputs}
          updateComputeBlock={(key, value) => updateConfig("inputs", key, value)}
        />
      )}

      {selectedEntrypoint?.inputs && (
        <ConfigBox
          headline="Outputs"
          description="Configure the Compute Blocks outputs here"
          config={selectedEntrypoint?.outputs}
          updateComputeBlock={(key, value) => updateConfig("outputs", key, value)}
        />
      )}

      <div className="flex justify-between">
        <button
          type="button"
          className="w-[78px] h-[36px] px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600"
          onClick={onPrev}
        >
          Prev
        </button>

        <button
          type="button"
          className={`w-[78px] h-[36px] px-4 py-2 rounded ${!formValid ? "bg-gray-200 cursor-not-allowed" : "bg-blue-500 text-white hover:bg-blue-600"}`}
          disabled={!formValid}
          onClick={onNext}
        >
          <LoadingAndError loading={loading} iconSize={21}>
            Create
          </LoadingAndError>
        </button>

      </div>
    </div>
  )
}
