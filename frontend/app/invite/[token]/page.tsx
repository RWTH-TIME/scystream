"use client"

import { useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { useAlert } from "@/hooks/useAlert"
import { useAcceptInviteMutation } from "@/mutations/shareMutations"
import LoadingAndError from "@/components/LoadingAndError"
import PageWithHeader from "@/components/layout/PageWithHeader"
import { withAuth } from "@/hooks/useAuth"

function InvitePage() {
  const router = useRouter()
  const params = useParams()
  const token = params.token as string

  const { setAlert } = useAlert()
  const { data: response, mutate: acceptInvite, isSuccess, isPending, isError }= useAcceptInviteMutation(setAlert)

  useEffect(() => {
    if (!token) return

    acceptInvite(token)
  }, [token])

    return (
      <PageWithHeader breadcrumbs={[]}>
        <LoadingAndError loading={isPending} error={isError}>
          <div className="flex items-center justify-center h-full">
            <div className="text-center">

            {isPending && (
              <>
                <h2 className="text-xl font-semibold mb-2">
                  Joining project...
                </h2>
                <p className="text-gray-500">
                  Please wait while we add you.
                </p>
              </>
            )}

            {isSuccess && (
              <>
                <h2 className="text-xl font-semibold text-green-600 mb-2">
                  Successfully joined!
                </h2>

                <div className="flex gap-3 justify-center mt-4">
                  <button
                    onClick={() => router.push(`/project/${response.project_uuid}`)}
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
                  Failed to join project
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

export default withAuth(InvitePage)
