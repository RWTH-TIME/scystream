import { AlertType, useAlert } from "@/hooks/useAlert";
import { useGetComputeBlockInfoMutation } from "@/mutations/computeBlockMutation";
import type { PageProps, ComputeBlock, Entrypoint, InputOutput } from "@/components/CreateComputeBlockModal";
import { useState } from "react";
import LoadingAndError from "@/components/LoadingAndError";
import Input from "@/components/inputs/Input";

const mapInputOutput = (data: InputOutput) => ({
  type: data.data_type === "file" ? "file" : "db_table",
  name: data.name,
  data_type: data.data_type,
  description: data.description || "",
  config: data.config || {},
});

export default function CreateComputeBlockInformationStep({
  onNext,
  setComputeBlock
}: PageProps) {
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
          cbc_url: repoURL
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
