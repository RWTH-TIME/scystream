import type { PageProps, RecordValueType } from "@/components/CreateComputeBlockModal";
import LoadingAndError from "@/components/LoadingAndError";
import ConfigBox from "../ConfigBox";
import { useState } from "react";

export default function CreateComputeBlockConfigurationStep({
  onNext,
  onPrev,
  selectedEntrypoint,
  computeBlock
}: PageProps) {
  const [customName, setCustomName] = useState(computeBlock?.custom_name || "");
  const [envs, setEnvs] = useState<Record<string, RecordValueType> | undefined>(selectedEntrypoint?.envs);

  return (
    <div className="mt-4 space-y-6 text-sm">
      <div className="p-4 border rounded">
        <label className="block text-gray-700 font-bold mb-1">Custom Name</label>
        <input
          type="text"
          value={customName}
          onChange={(e) => setCustomName(e.target.value)}
          placeholder="Enter a custom name"
          className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {envs && (
        <ConfigBox
          headline="Environment Variables"
          description="Configure the Compute Blocks environment here"
          config={envs}
        />
      )}

      {selectedEntrypoint?.inputs && (
        <ConfigBox
          headline="Inputs"
          description="Configure the Compute Blocks inputs here"
          config={selectedEntrypoint?.inputs}
        />
      )}

      {selectedEntrypoint?.inputs && (
        <ConfigBox
          headline="Outputs"
          description="Configure the Compute Blocks outputs here"
          config={selectedEntrypoint?.outputs}
        />
      )}

      <div className="flex justify-between">
        <button
          type="button"
          className="w-[78px] h-[36px] px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600"
          onClick={onPrev}
        >
          <LoadingAndError loading={false} iconSize={21}>
            Prev
          </LoadingAndError>
        </button>

        <button
          type="button"
          className={`w-[78px] h-[36px] px-4 py-2 rounded ${!computeBlock ? "bg-gray-200 cursor-not-allowed" : "bg-blue-500 text-white hover:bg-blue-600"}`}
          disabled={false}
          onClick={onNext}
        >
          <LoadingAndError loading={false} iconSize={21}>
            Create
          </LoadingAndError>
        </button>
      </div>
    </div>
  )
}
