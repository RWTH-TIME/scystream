"use client"

import withProtectedRoute from "@/components/ProtectedRoute"
import PageWithHeader from "@/components/layout/PageWithHeader"

function Dashboard() {
  return (
    <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
      <div>
        DASHBOARD
      </div>
    </PageWithHeader>
  )
}

export default withProtectedRoute(Dashboard)
