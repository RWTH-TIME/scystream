import { useState } from "react"
import Modal, { type ModalProps } from "./Modal"
import { Step, StepLabel, Stepper } from "@mui/material"
import CreateComputeBlockInformationStep from "./steps/CreateComputeBlockInformationStep"
import CreateComputeBlockEntrypointStep from "./steps/CreateComputeBlockEntrypointStep"
import CreateComputeBlockConfigurationStep from "./steps/CreateComputeBlockConfigurationStep"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import type { CreateComputeBlockDTO, InputOutputDTO } from "@/mutations/computeBlockMutation"
import { useCreateComputeBlockMutation } from "@/mutations/computeBlockMutation"
import { useAlert } from "@/hooks/useAlert"
import type { XYPosition } from "@xyflow/react"


type CreateComputeBlockModalProps = Omit<ModalProps, "children"> & {
  dropCoordinates: XYPosition,
};

export enum InputOutputType {
  FILE = "file",
  DB = "pg_table",
  CUSTOM = "custom"
}
export enum IOType {
  INPUT = "Input",
  OUTPUT = "Output"
}
export type RecordValueType = string | number | boolean | string[] | number[] | boolean[] | null


export type InputOutput = {
  id?: string,
  type: IOType,
  name: string,
  data_type: InputOutputType,
  description: string,
  config: Record<string, RecordValueType>,
  presigned_url: string,
  selected_file?: File,
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

export enum ComputeBlockStatus {
  SUCCESS = "SUCCESS",
  RUNNING = "RUNNING",
  FAILED = "FAILED",
  SCHEDULED = "SCHEDULED",
  IDLE = "IDLE",
  VALIDATION_FAILED = "VALIDATION_FAILED"
}

export type ComputeBlock = BaseComputeBlock & {
  id: string,
  selected_entrypoint: Entrypoint,
  x_pos: number,
  y_pos: number,
  status?: ComputeBlockStatus,
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

const emptyComputeBlockDraft: ComputeBlockDraft = {
  name: "",
  description: "",
  custom_name: "",
  author: "",
  image: "",
  entrypoints: [],
  cbc_url: ""
}

const STEPS_INFORMATION = [
  { label: "CBC" },
  { label: "Entrypoint" },
  { label: "Configuration" },
]

export async function encodeFileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => {
      if (typeof reader.result === "string") {
        const base64Data = reader.result.split(",")[1]
        resolve(base64Data)
      } else {
        reject(new Error("Failed to read file as base64"))
      }
    }
    reader.onerror = reject
  })
}

export default function CreateComputeBlockModal({
  isOpen,
  onClose,
  dropCoordinates
}: CreateComputeBlockModalProps) {
  const [computeBlockDraft, setComputeBlockDraft] = useState<ComputeBlockDraft>(emptyComputeBlockDraft)
  const [selectedEntrypoint, setSelectedEntrypoint] = useState<Entrypoint | undefined>(undefined)
  const [activeStep, setActiveStep] = useState<number>(0)
  const { selectedProject } = useSelectedProject()
  const { setAlert } = useAlert()
  const { mutateAsync, isPending: loading } = useCreateComputeBlockMutation(setAlert, selectedProject?.uuid)

  function reset() {
    setComputeBlockDraft(emptyComputeBlockDraft)
    setSelectedEntrypoint(undefined)
    setActiveStep(0)
  };

  function handleNext() {
    if (activeStep < STEPS_INFORMATION.length - 1) {
      setActiveStep((prevStep) => prevStep + 1)
    }
  };

  function handleBack() {
    if (activeStep > 0) {
      setActiveStep((prevStep) => prevStep - 1)
    }
  };

  async function mapInputOutputToDTO(inputOutput: InputOutput): Promise<InputOutputDTO> {
    let encodedFile: string | undefined
    let fileType: string | undefined

    if (inputOutput.selected_file) {
      fileType = inputOutput.selected_file.name.split(".").pop()?.toLowerCase()
      encodedFile = await encodeFileToBase64(inputOutput.selected_file)
    }

    return {
      name: inputOutput.name,
      data_type: inputOutput.data_type,
      description: inputOutput.description,
      config: inputOutput.config,
      selected_file_b64: encodedFile,
      selected_file_type: fileType
    }
  }

  function handleModalClose() {
    reset()
    onClose()
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
        inputs: await Promise.all(selectedEntrypoint.inputs.map(mapInputOutputToDTO)),
        outputs: await Promise.all(selectedEntrypoint.outputs.map(mapInputOutputToDTO)),
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
        return <CreateComputeBlockInformationStep onNext={handleNext} setComputeBlock={setComputeBlockDraft} />
      case 1:
        return <CreateComputeBlockEntrypointStep onNext={handleNext} onPrev={handleBack} computeBlock={computeBlockDraft} setSelectedEntrypoint={setSelectedEntrypoint} selectedEntrypoint={selectedEntrypoint} />
      case 2:
        return <CreateComputeBlockConfigurationStep onNext={handleCreate} onPrev={handleBack} computeBlock={computeBlockDraft} setComputeBlock={setComputeBlockDraft} selectedEntrypoint={selectedEntrypoint} setSelectedEntrypoint={setSelectedEntrypoint} loading={loading} />
    }
  };

  return (
    <Modal onClose={handleModalClose} isOpen={isOpen}>
      <div className="w-[97%]">
        <Stepper activeStep={activeStep} >
          {STEPS_INFORMATION.map((step, index) => (
            <Step key={index}>
              <StepLabel>{step.label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </div>
      {getStepContent()}
    </Modal>
  )
}

