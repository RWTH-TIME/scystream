"use client"

import PageWithHeader from "@/components/layout/PageWithHeader"
import LoadingAndError from "@/components/LoadingAndError"
import Home from "@/components/Home"
import { useAlert } from "@/hooks/useAlert"
import { useProjectStatusWS } from "@/mutations/workflowMutations"
import { withAuth } from "@/hooks/useAuth"

function Dashboard() {
  const { setAlert } = useAlert()

  useProjectStatusWS(setAlert)

  return (
    <LoadingAndError>
      <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/" }]}>
        <Home />
      </PageWithHeader>
    </LoadingAndError>
  )
}

export default withAuth(Dashboard)

