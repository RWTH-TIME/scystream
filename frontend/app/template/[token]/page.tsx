"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { AlertType, useAlert } from "@/hooks/useAlert"
import { useAcceptTemplateMutation, useTemplatePreviewQuery } from "@/mutations/shareMutations"
import LoadingAndError from "@/components/LoadingAndError"
import PageWithHeader from "@/components/layout/PageWithHeader"
import { withAuth } from "@/hooks/useAuth"
import { type Edge, ReactFlowProvider } from "@xyflow/react"
import { PreviewWorkbench } from "@/components/PreviewWorkbench"
import type { ComputeBlockNodeType } from "@/components/nodes/ComputeBlockNode"

function TemplatePage() {
  const router = useRouter()
  const params = useParams()

  const token = params.token as string

  const { setAlert } = useAlert()

  const [projectName, setProjectName] = useState("")
  const [blocks, setBlocks] = useState<ComputeBlockNodeType[]>([])
  const [edges, setEdges] = useState<Edge[]>([])

  const { data: previewres, isLoading, isError } = useTemplatePreviewQuery(token)

  useEffect(() => {
    if (previewres) {
      setBlocks(previewres.blocks ?? [])
      setEdges(previewres.edges ?? [])
    }
  }, [previewres])

  const {
    mutate: acceptTemplate,
    isPending: isAccepting,
  } = useAcceptTemplateMutation(setAlert, {
  onSuccess: (data) => {
    const projectId = data?.project_uuid
    console.log(projectId)

    if (!projectId) return

    router.push(`/project/${projectId}`)
  },
})

  const handleAccept = () => {
    if (!projectName.trim()) {
      setAlert("Please enter a project name", AlertType.ERROR)
      return
    }

    acceptTemplate({
      token,
      project_name: projectName,
    })
  }

  return (
    <PageWithHeader
      breadcrumbs={[
        { text: "Dashboard", link: "/" },
        { text: "Share Template", link: "/template" },
      ]}
    >
      {/* Preview Banner */}
      <div className="bg-yellow-100 border border-yellow-300 text-yellow-900 px-4 py-3 rounded-xl mb-4">
        <strong>Preview Mode:</strong> You are viewing a shared template.
        You can explore the workflow, but editing is disabled until you accept it.
      </div>

      <LoadingAndError loading={isLoading} error={isError}>
        <div className="flex flex-col h-[calc(100vh-200px)]">
          <ReactFlowProvider>
            <PreviewWorkbench
              compute_blocks={blocks}
              edges={edges}
            />
          </ReactFlowProvider>
        </div>
      </LoadingAndError>

      <div className="fixed bottom-0 left-0 right-0 bg-white border-t px-6 py-4 flex items-center justify-between shadow-md">
        <div className="flex flex-col max-w-md w-full mr-4">
          <label className="text-sm font-medium text-gray-700">
            Create project from template
          </label>
          <input
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Enter project name"
            className="border rounded-lg px-3 py-2 mt-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-xs text-gray-500 mt-1">
            You’ll be able to edit all blocks after accepting the template.
          </span>
        </div>

        <button
          onClick={handleAccept}
          disabled={isAccepting}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-xl font-medium disabled:opacity-50"
        >
          {isAccepting ? "Accepting..." : "Accept Template"}
        </button>
      </div>
    </PageWithHeader>
  )
}

export default withAuth(TemplatePage)
