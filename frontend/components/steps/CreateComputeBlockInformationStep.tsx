import { AlertType, useAlert } from "@/hooks/useAlert"
import { useGetComputeBlockInfoMutation } from "@/mutations/computeBlockMutation"
import { IOType } from "@/components/CreateComputeBlockModal"
import { type PageProps, type Entrypoint, type InputOutput, type ComputeBlockDraft } from "@/components/CreateComputeBlockModal"
import { useState } from "react"
import LoadingAndError from "@/components/LoadingAndError"
import Input from "@/components/inputs/Input"
import Button, { ButtonSentiment } from "../Button"

const mapInputOutput = (data: InputOutput, type: IOType) => ({
  type: type,
  name: data.name,
  data_type: data.data_type,
  description: data.description || "",
  config: data.config || {},
})

export default function CreateComputeBlockInformationStep({
  onNext,
  setComputeBlock
}: PageProps) {
  const [repoURL, setRepoURL] = useState<string>("")

  const { setAlert } = useAlert()
  const { mutateAsync, isPending: loading } = useGetComputeBlockInfoMutation(setAlert)

  async function createComputeBlock(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    if (repoURL.length > 0) {
      const cb = await mutateAsync({
        cbc_url: repoURL,
      })

      if (setComputeBlock) {
        const mappedComputeBlock: ComputeBlockDraft = {
          name: cb.name,
          description: cb.description,
          custom_name: "",
          author: cb.author,
          image: cb.image,
          entrypoints: cb.entrypoints.map((entrypoint: Entrypoint) => ({
            name: entrypoint.name,
            description: entrypoint.description,
            inputs: entrypoint.inputs.map(i => mapInputOutput(i, IOType.INPUT)),
            outputs: entrypoint.outputs.map(o => mapInputOutput(o, IOType.OUTPUT)),
            envs: entrypoint.envs || {},
          })),
          cbc_url: repoURL
        }

        setComputeBlock(mappedComputeBlock)
      }

      onNext()
    } else {
      setAlert("Compute Block Name and Repo URL must be set.", AlertType.ERROR)
    }
  }

  return (
    <form onSubmit={createComputeBlock} className="mt-4 space-y-4 text-sm">
      <Input type="text" value={repoURL} onChange={setRepoURL} label="Compute Block Config URL" />
      <div className="flex justify-end">
        <Button
          type="submit"
          sentiment={ButtonSentiment.POSITIVE}
          disabled={repoURL.length === 0}
        >
          <LoadingAndError loading={loading} iconSize={21}>
            Next
          </LoadingAndError>
        </Button>
      </div>
    </form>
  )

}
