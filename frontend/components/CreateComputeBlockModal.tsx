import { useEffect, useState } from "react";
import LoadingAndError from "./LoadingAndError";
import Modal, { type ModalProps } from "./Modal";
import Input from "./inputs/Input";
import { useGetComputeBlockInfoMutation } from "@/mutations/computeBlockMutation";
import { AlertType, useAlert } from "@/hooks/useAlert";
import { Step, StepLabel, Stepper } from "@mui/material";
import Dropdown from "./inputs/Dropdown";
import ConfigEnvsInputs from "./inputs/ConfigEnvsInputs";
import ConfigBox from "./ConfigBox";

// TODO: Split this component into multiple files?

type CreateComputeBlockModalProps = Omit<ModalProps, "children">;

type InputOutputType = "file" | "db_table";
export type RecordValueType = string | number | boolean | string[] | number[] | boolean[] | null

export type InputOutput = {
  type: InputOutputType,
  name: string,
  data_type: string,
  description: string,
  config: Record<string, RecordValueType>,
}


export type Entrypoint = {
  name: string,
  description: string,
  inputs: InputOutput[],
  outputs: InputOutput[],
  envs: Record<string, RecordValueType>,
}

export type ComputeBlock = {
  name: string,
  description: string,
  custom_name: string,
  author: string,
  image: string,
  entrypoints: Entrypoint[],
}

type PageProps = {
  onNext: () => void,
  onPrev: () => void,
  computeBlock?: ComputeBlock,
  setComputeBlock?: React.Dispatch<React.SetStateAction<ComputeBlock>>,
  setSelectedEntrypoint?: React.Dispatch<React.SetStateAction<Entrypoint | undefined>>,
  selectedEntrypoint?: Entrypoint,
}

const mapInputOutput = (data: InputOutput) => ({
  type: data.data_type === "file" ? "file" : "db_table",
  name: data.name,
  data_type: data.data_type,
  description: data.description || "",
  config: data.config || {},
});



function StepOne({ onNext, setComputeBlock }: PageProps) {
  const [repoURL, setRepoURL] = useState<string>("");

  const { setAlert } = useAlert();
  const { mutateAsync, isPending: loading } = useGetComputeBlockInfoMutation(setAlert);

  async function createComputeBlock(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (repoURL.length > 0) {
      const cb = await mutateAsync({
        cbc_url: repoURL,
      });

      if (setComputeBlock) {
        const mappedComputeBlock: ComputeBlock = {
          name: cb.name,
          description: cb.description,
          custom_name: "",
          author: cb.author,
          image: cb.image,
          entrypoints: cb.entrypoints.map((entrypoint: Entrypoint) => ({
            name: entrypoint.name,
            description: entrypoint.description,
            inputs: entrypoint.inputs.map(mapInputOutput),
            outputs: entrypoint.outputs.map(mapInputOutput),
            envs: entrypoint.envs || {},
          })),
        };

        setComputeBlock(mappedComputeBlock);
      }

      onNext();
    } else {
      setAlert("Compute Block Name and Repo URL must be set.", AlertType.ERROR);
    }
  }

  return (
    <form onSubmit={createComputeBlock} className="mt-4 space-y-4 text-sm">
      <Input type="text" value={repoURL} onChange={setRepoURL} label="Compute Block Config URL" />
      <div className="flex justify-end">
        <button
          type="submit"
          className={`w-[78px] h-[36px] px-4 py-2 rounded ${repoURL.length === 0 ? "bg-gray-200 cursor-not-allowed" : "text-white bg-blue-500 hover:bg-blue-600"}`}
          disabled={repoURL.length === 0}
        >
          <LoadingAndError loading={loading} iconSize={21}>
            Next
          </LoadingAndError>
        </button>
      </div>
    </form>
  )
}

function StepTwo({ onNext, computeBlock, selectedEntrypoint, setSelectedEntrypoint }: PageProps) {
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

function StepThree({ onPrev, onNext, computeBlock, selectedEntrypoint }: PageProps) {
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


export default function CreateComputeBlockModal({
  isOpen,
  onClose,
}: CreateComputeBlockModalProps) {
  const [computeBlockDraft, setComputeBlockDraft] = useState<ComputeBlock>({
    name: "",
    description: "",
    custom_name: "",
    author: "",
    image: "",
    entrypoints: [],
  });
  const [selectedEntrypoint, setSelectedEntrypoint] = useState<Entrypoint | undefined>(undefined)
  const [activeStep, setActiveStep] = useState<number>(0);

  const stepsInformation = [
    { label: "CBC" },
    { label: "Entrypoint" },
    { label: "Configuration" },
  ];

  const handleNext = () => {
    if (activeStep < stepsInformation.length - 1) {
      setActiveStep((prevStep) => prevStep + 1);
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep((prevStep) => prevStep - 1);
    }
  };

  const getStepContent = () => {
    switch (activeStep) {
      case 0:
        return <StepOne onNext={handleNext} onPrev={handleBack} setComputeBlock={setComputeBlockDraft} />;
      case 1:
        return <StepTwo onNext={handleNext} onPrev={handleBack} computeBlock={computeBlockDraft} setSelectedEntrypoint={setSelectedEntrypoint} selectedEntrypoint={selectedEntrypoint} />;
      case 2:
        return <StepThree onNext={handleNext} onPrev={handleBack} computeBlock={computeBlockDraft} selectedEntrypoint={selectedEntrypoint} />;
    }
  };

  return (
    <Modal onClose={onClose} isOpen={isOpen}>
      <Stepper activeStep={activeStep} >
        {stepsInformation.map((step, index) => (
          <Step key={index}>
            <StepLabel>{step.label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      {getStepContent()}
    </Modal>
  );
}

