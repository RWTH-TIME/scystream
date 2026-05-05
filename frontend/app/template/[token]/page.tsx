"use client"

import { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { AlertType, useAlert } from "@/hooks/useAlert"
import { useAcceptTemplateMutation } from "@/mutations/shareMutations"
import LoadingAndError from "@/components/LoadingAndError"
import PageWithHeader from "@/components/layout/PageWithHeader"
import { withAuth } from "@/hooks/useAuth"

function TemplatePage() {
  const router = useRouter()
  const params = useParams()
  const token = params.token as string

  const { setAlert } = useAlert()

  const [projectName, setProjectName] = useState("")

  const {
    data: response,
    mutate: acceptInvite,
    isSuccess,
    isPending,
    isError,
  } = useAcceptTemplateMutation(setAlert)

  const handleAccept = () => {
    if (!projectName.trim()) {
      setAlert("Please enter a project name", AlertType.ERROR)
      return
    }

    acceptInvite({
      token,
      project_name: projectName,
    })
  }

  return (
    <PageWithHeader breadcrumbs={[]}>
      <LoadingAndError loading={isPending} error={isError}>
        <div className="flex items-center justify-center h-full">
          <div className="text-center w-full max-w-md">

            {!isSuccess && (
              <>
                <h2 className="text-xl font-semibold mb-4">
                  Create Project from Template
                </h2>

                <input
                  type="text"
                  placeholder="Enter project name"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="w-full px-3 py-2 border rounded mb-4"
                />

                <button
                  onClick={handleAccept}
                  disabled={isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded w-full"
                >
                  {isPending ? "Creating..." : "Create Project"}
                </button>
              </>
            )}

            {isSuccess && (
              <>
                <h2 className="text-xl font-semibold text-green-600 mb-2">
                  Project created!
                </h2>

                <div className="flex gap-3 justify-center mt-4">
                  <button
                    onClick={() =>
                      router.push(`/project/${response.project_uuid}`)
                    }
                    className="px-4 py-2 bg-blue-600 text-white rounded"
                  >
                    Go To Project
                  </button>

                  <button
                    onClick={() => router.push("/")}
                    className="px-4 py-2 bg-gray-200 rounded"
                  >
                    Back to Projects
                  </button>
                </div>
              </>
            )}

            {isError && (
              <>
                <h2 className="text-xl font-semibold text-red-600">
                  Failed to create project
                </h2>

                <button
                  onClick={() => router.push("/")}
                  className="mt-4 px-4 py-2 bg-gray-200 rounded"
                >
                  Go back
                </button>
              </>
            )}

          </div>
        </div>
      </LoadingAndError>
    </PageWithHeader>
  )
}

export default withAuth(TemplatePage)
