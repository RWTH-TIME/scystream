"use client"

import { useRouter, useParams } from "next/navigation"
import { AlertType, useAlert } from "@/hooks/useAlert"
import { useAcceptInviteQuery } from "@/mutations/shareMutations"
import LoadingAndError from "@/components/LoadingAndError"
import PageWithHeader from "@/components/layout/PageWithHeader"
import { withAuth } from "@/hooks/useAuth"
import { useEffect } from "react"


function InvitePage() {
  const router = useRouter()
  const params = useParams()

  const token = params.token as string

  const { setAlert } = useAlert()

  const { data, isLoading, isError } = useAcceptInviteQuery(token, {})

  useEffect(() => {
    if (!data) return

    if (data.is_already_member === true) {
      setAlert("You have already been a member of the project.", AlertType.DEFAULT)
    } else {
      setAlert("Successfully added you to the project.", AlertType.SUCCESS)
    }

    router.push(`/project/${data.project_uuid}`)
  }, [data])

  return (
    <PageWithHeader
      breadcrumbs={[
        { text: "Dashboard", link: "/" },
        { text: "Invite", link: "/invite" },
      ]}
    >
      <LoadingAndError loading={isLoading} error={isError}>
      </LoadingAndError>
    </PageWithHeader>
  )
}

export default withAuth(InvitePage)
