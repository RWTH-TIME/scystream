import { useState } from "react";
import Modal, { type ModalProps } from "./Modal";
import { Step, StepLabel, Stepper } from "@mui/material";
import CreateComputeBlockInformationStep from "./steps/CreateComputeBlockInformationStep";
import CreateComputeBlockEntrypointStep from "./steps/CreateComputeBlockEntrypointStep";
import CreateComputeBlockConfigurationStep from "./steps/CreateComputeBlockConfigurationStep";


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

export type PageProps = {
  onNext: () => void,
  onPrev?: () => void,
  computeBlock?: ComputeBlock,
  setComputeBlock?: React.Dispatch<React.SetStateAction<ComputeBlock>>,
  setSelectedEntrypoint?: React.Dispatch<React.SetStateAction<Entrypoint | undefined>>,
  selectedEntrypoint?: Entrypoint,
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

  const getStepContent = () => {
    switch (activeStep) {
      case 0:
        return <CreateComputeBlockInformationStep onNext={handleNext} setComputeBlock={setComputeBlockDraft} />;
      case 1:
        return <CreateComputeBlockEntrypointStep onNext={handleNext} onPrev={handleBack} computeBlock={computeBlockDraft} setSelectedEntrypoint={setSelectedEntrypoint} selectedEntrypoint={selectedEntrypoint} />;
      case 2:
        return <CreateComputeBlockConfigurationStep onNext={handleNext} onPrev={handleBack} computeBlock={computeBlockDraft} selectedEntrypoint={selectedEntrypoint} />;
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

