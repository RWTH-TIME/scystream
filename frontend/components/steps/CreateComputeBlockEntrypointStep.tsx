import type { PageProps, Entrypoint } from "@/components/CreateComputeBlockModal";
import LoadingAndError from "@/components/LoadingAndError";
import Dropdown from "../inputs/Dropdown";

export default function CreateComputeBlockEntrypointStep({
  onNext,
  setSelectedEntrypoint,
  selectedEntrypoint,
  computeBlock
}: PageProps) {
  const handleSelect = (entrypoint: Entrypoint) => {
    if (setSelectedEntrypoint) {
      setSelectedEntrypoint(entrypoint)
    }
  };

  const renderOption = (entrypoint: Entrypoint) => (
    <div className="flex flex-col">
      <span>{entrypoint.name}</span>
      <span className="text-gray-500 text-sm">{entrypoint.description}</span>
    </div>
  );

  const getValue = (entrypoint: Entrypoint) => entrypoint.name

  return (
    <div className="mt-5">
      <div className="p-4 border rounded bg-gray-100">
        <h3 className="text-lg font-semibold">Compute Block Details</h3>
        <div className="mt-2">
          <p><strong>Name:</strong> {computeBlock?.name || "N/A"}</p>
          <p><strong>Description:</strong> {computeBlock?.description || "N/A"}</p>
          <p><strong>Author:</strong> {computeBlock?.author || "N/A"}</p>
          <p><strong>Image:</strong> {computeBlock?.image || "N/A"}</p>
        </div>
      </div>
      <h3 className="text-lg font-semibold mt-5">Select Entrypoint:</h3>
      <Dropdown
        options={computeBlock?.entrypoints || []}
        selectedValue={selectedEntrypoint?.name}
        onSelect={handleSelect}
        renderOption={renderOption}
        getValue={getValue}
        placeholder="Select an entrypoint"
      />

      <div className="mt-4 flex justify-end">
        <button
          type="button"
          className={`w-[78px] h-[36px] px-4 py-2 rounded ${!selectedEntrypoint ? "bg-gray-200 cursor-not-allowed" : "bg-blue-500 text-white hover:bg-blue-600"}`}
          disabled={!selectedEntrypoint}
          onClick={onNext}
        >
          <LoadingAndError loading={false} iconSize={21}>
            Next
          </LoadingAndError>
        </button>
      </div>
    </div>
  );
}
