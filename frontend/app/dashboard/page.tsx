"use client"

import PageWithHeader from "@/components/layout/PageWithHeader"
import useAuth from "@/hooks/useAuth"
import LoadingAndError from "@/components/LoadingAndError"
import Home from "@/components/Home"
import { useAlert } from "@/hooks/useAlert"
import { useProjectStatusWS } from "@/mutations/workflowMutations"

export default function Dashboard() {
  const { loading } = useAuth()
  const { setAlert } = useAlert()

  useProjectStatusWS(setAlert)

  return (
    <LoadingAndError loading={loading}>
      <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
        <Home />
      </PageWithHeader>
    </LoadingAndError>
  )
}

