import type { PageProps, Entrypoint } from "@/components/CreateComputeBlockModal";
import LoadingAndError from "@/components/LoadingAndError";
import Dropdown from "../inputs/Dropdown";
import Button, { ButtonSentiment } from "../Button";

export default function CreateComputeBlockEntrypointStep({
  onNext,
  setSelectedEntrypoint,
  selectedEntrypoint,
  computeBlock
}: PageProps) {
  function handleSelect(entrypoint: Entrypoint) {
    if (setSelectedEntrypoint) {
      setSelectedEntrypoint(entrypoint)
    }
  };

  function renderOption(entrypoint: Entrypoint) {
    return (
      <div className="flex flex-col">
        <span>{entrypoint.name}</span>
        <span className="text-gray-500 text-sm">{entrypoint.description}</span>
      </div>
    )
  };

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
        selectedValue={selectedEntrypoint}
        onSelect={handleSelect}
        renderOption={renderOption}
        renderSelected={renderOption}
        placeholder="Select an entrypoint"
      />

      <div className="mt-4 flex justify-end">
        <Button
          disabled={!selectedEntrypoint}
          onClick={onNext}
          sentiment={ButtonSentiment.POSITIVE}
        >
          <LoadingAndError loading={false} iconSize={21}>
            Next
          </LoadingAndError>
        </Button>
      </div>
    </div>
  );
}
