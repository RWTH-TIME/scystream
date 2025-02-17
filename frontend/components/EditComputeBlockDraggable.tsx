import { useEffect, useState } from "react"
import Input from "./inputs/Input"
import LoadingAndError from "./LoadingAndError"
import ProjectCBSettingsDraggable from "./ProjectCBSettingsDraggable"
import { AlertType, useAlert } from "@/hooks/useAlert"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"

export default function EditComputeBlockDraggable() {
  const { setAlert } = useAlert()
  const { selectedComputeBlock } = useSelectedComputeBlock()

  const [cbName, setCBName] = useState<string>(selectedComputeBlock?.name ?? "")
  const [activeTab, setActiveTab] = useState<"metadata" | "inputs" | "outputs">("metadata") // Track the active tab

  useEffect(() => {
    setCBName(selectedComputeBlock?.name ?? "")
  }, [selectedComputeBlock])

  function updateProject(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    if (selectedComputeBlock && cbName && cbName.length > 0) {
      // TODO: mutate
    } else {
      setAlert("Project Name must be set.", AlertType.ERROR)
    }
  }

  return (
    <ProjectCBSettingsDraggable>
      {/* Tab Navigation */}
      <div className="flex items-center border-b-2">
        {["Metadata", "Inputs", "Outputs"].map((tab) => (
          <button
            key={tab}
            className={`px-4 py-2 font-medium text-sm ${activeTab.toLowerCase() === tab.toLowerCase()
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-gray-600 hover:text-blue-600"
              }`}
            onClick={() => setActiveTab(tab.toLowerCase() as "metadata" | "inputs" | "outputs")}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {activeTab === "metadata" && (
          <>
            <h2 className="text-xl font-bold">
              Compute Block <span className="text-blue-600">{selectedComputeBlock?.name}</span> Settings:
            </h2>
            <form onSubmit={(e) => updateProject(e)} className="mt-4 space-y-4 text-sm">
              <div>
                <Input
                  type="text"
                  value={cbName}
                  label="Compute Block Name"
                  onChange={setCBName}
                />
              </div>
              <div>
                <label htmlFor="entrypoint" className="block text-gray-700 font-medium">
                  Entry Point
                </label>
                <select
                  id="entrypoint"
                  name="entrypoint"
                  className="w-full mt-1 p-2 border border-gray-300 rounded-md"
                >
                  {/* Replace these options with dynamic data if needed */}
                  <option value="main">Main</option>
                  <option value="secondary">Secondary</option>
                </select>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  className="flex flex-col w-[78px] h-[36px] px-4 py-2 text-white bg-blue-500 rounded hover:bg-blue-600"
                  disabled={false}
                >
                  <LoadingAndError loading={false} iconSize={21}>
                    Save
                  </LoadingAndError>
                </button>
              </div>
            </form>
          </>
        )}

        {activeTab === "inputs" && (
          <div>
            <h2 className="text-xl font-bold">Inputs</h2>
            <p className="mt-2 text-sm text-gray-600">Define inputs for the compute block here.</p>
            {/* Add your input-related content */}
            <div className="mt-4">
              <Input type="text" label="Input Name" value="" onChange={() => { }} />
              <button className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                Add Input
              </button>
            </div>
          </div>
        )}

        {activeTab === "outputs" && (
          <div>
            <h2 className="text-xl font-bold">Outputs</h2>
            <p className="mt-2 text-sm text-gray-600">Define outputs for the compute block here.</p>
            {/* Add your output-related content */}
            <div className="mt-4">
              <Input type="text" label="Output Name" value="" onChange={() => { }} />
              <button className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                Add Output
              </button>
            </div>
          </div>
        )}
      </div>
    </ProjectCBSettingsDraggable>
  )
}
