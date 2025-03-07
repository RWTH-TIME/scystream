import { useState } from "react";
import Modal, { type ModalProps } from "./Modal";
import { Step, StepLabel, Stepper } from "@mui/material";
import CreateComputeBlockInformationStep from "./steps/CreateComputeBlockInformationStep";
import CreateComputeBlockEntrypointStep from "./steps/CreateComputeBlockEntrypointStep";
import CreateComputeBlockConfigurationStep from "./steps/CreateComputeBlockConfigurationStep";
import { useSelectedProject } from "@/hooks/useSelectedProject";
import type { CreateComputeBlockDTO, InputOutputDTO } from "@/mutations/computeBlockMutation";
import { useCreateComputeBlockMutation } from "@/mutations/computeBlockMutation";
import { useAlert } from "@/hooks/useAlert";
import type { XYPosition } from "@xyflow/react";


type CreateComputeBlockModalProps = Omit<ModalProps, "children"> & {
  dropCoordinates: XYPosition,
};

export enum InputOutputType {
  FILE = "file",
  DB = "pg_table",
  CUSTOM = "custom"
}
export type RecordValueType = string | number | boolean | string[] | number[] | boolean[] | null


export type InputOutput = {
  id?: string,
  type: string,
  name: string,
  data_type: InputOutputType,
  description: string,
  config: Record<string, RecordValueType>,
}


export type Entrypoint = {
  id?: string,
  name: string,
  description: string,
  inputs: InputOutput[],
  outputs: InputOutput[],
  envs: Record<string, RecordValueType>,
}

type BaseComputeBlock = {
  name: string,
  description: string,
  custom_name: string,
  author: string,
  image: string,
  cbc_url: string,
};

export type ComputeBlockDraft = BaseComputeBlock & {
  entrypoints: Entrypoint[],
};

export type ComputeBlock = BaseComputeBlock & {
  id: string,
  selected_entrypoint: Entrypoint,
  x_pos: number,
  y_pos: number,
};

export type PageProps = {
  onNext: () => void,
  onPrev?: () => void,
  computeBlock?: ComputeBlockDraft,
  setComputeBlock?: React.Dispatch<React.SetStateAction<ComputeBlockDraft>>,
  setSelectedEntrypoint?: React.Dispatch<React.SetStateAction<Entrypoint | undefined>>,
  selectedEntrypoint?: Entrypoint,
  loading?: boolean,
}

export default function CreateComputeBlockModal({
  isOpen,
  onClose,
  dropCoordinates
}: CreateComputeBlockModalProps) {
  const [computeBlockDraft, setComputeBlockDraft] = useState<ComputeBlockDraft>({
    name: "",
    description: "",
    custom_name: "",
    author: "",
    image: "",
    entrypoints: [],
    cbc_url: "",
  });
  const [selectedEntrypoint, setSelectedEntrypoint] = useState<Entrypoint | undefined>(undefined)
  const [activeStep, setActiveStep] = useState<number>(0)
  const { selectedProject } = useSelectedProject()
  const { setAlert } = useAlert()
  const { mutateAsync, isPending: loading } = useCreateComputeBlockMutation(setAlert, selectedProject?.uuid)
  const stepsInformation = [
    { label: "CBC" },
    { label: "Entrypoint" },
    { label: "Configuration" },
  ];

  function reset() {
    setComputeBlockDraft({
      name: "",
      description: "",
      custom_name: "",
      author: "",
      image: "",
      entrypoints: [],
      cbc_url: "",
    });
    setSelectedEntrypoint(undefined);
    setActiveStep(0);
  };

  function handleNext() {
    if (activeStep < stepsInformation.length - 1) {
      setActiveStep((prevStep) => prevStep + 1);
    }
  };

  function handleBack() {
    if (activeStep > 0) {
      setActiveStep((prevStep) => prevStep - 1);
    }
  };

  function mapInputOutputToDTO(inputOutput: InputOutput): InputOutputDTO {
    return {
      name: inputOutput.name,
      data_type: inputOutput.data_type,
      description: inputOutput.description,
      config: inputOutput.config,
    }
  }

  function handleModalClose() {
    reset();
    onClose();
  }

  async function handleCreate() {
    if (!selectedProject || !computeBlockDraft || !selectedEntrypoint) return

    const cb_dto: CreateComputeBlockDTO = {
      project_id: selectedProject.uuid,
      cbc_url: computeBlockDraft.cbc_url,
      name: computeBlockDraft.name,
      custom_name: computeBlockDraft.custom_name,
      description: computeBlockDraft.description,
      author: computeBlockDraft.author,
      image: computeBlockDraft.image,
      selected_entrypoint: {
        name: selectedEntrypoint.name,
        description: selectedEntrypoint.description,
        inputs: selectedEntrypoint.inputs.map(mapInputOutputToDTO),
        outputs: selectedEntrypoint.outputs.map(mapInputOutputToDTO),
        envs: selectedEntrypoint.envs
      },
      x_pos: dropCoordinates.x,
      y_pos: dropCoordinates.y,
    }

    await mutateAsync(cb_dto)

    handleModalClose()
  }

  function getStepContent() {
    switch (activeStep) {
      case 0:
        return <CreateComputeBlockInformationStep onNext={handleNext} setComputeBlock={setComputeBlockDraft} />;
      case 1:
        return <CreateComputeBlockEntrypointStep onNext={handleNext} onPrev={handleBack} computeBlock={computeBlockDraft} setSelectedEntrypoint={setSelectedEntrypoint} selectedEntrypoint={selectedEntrypoint} />;
      case 2:
        return <CreateComputeBlockConfigurationStep onNext={handleCreate} onPrev={handleBack} computeBlock={computeBlockDraft} setComputeBlock={setComputeBlockDraft} selectedEntrypoint={selectedEntrypoint} setSelectedEntrypoint={setSelectedEntrypoint} loading={loading} />;
    }
  };




  return (
    <Modal onClose={handleModalClose} isOpen={isOpen}>
      <div className="w-[97%]">
        <Stepper activeStep={activeStep} >
          {stepsInformation.map((step, index) => (
            <Step key={index}>
              <StepLabel>{step.label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </div>
      {getStepContent()}
    </Modal>
  );
}

