"use client"

import PageWithHeader from "@/components/layout/PageWithHeader"
import ProjectList from "@/components/ProjectList"
import useAuth from "@/hooks/useAuth"
import Workbench from "@/components/Workbench"
import LoadingAndError from "@/components/LoadingAndError"
import { SelectedProjectProvider } from "@/hooks/useSelectedProject"

export default function Dashboard() {
  const { loading } = useAuth()

  return (
    <LoadingAndError loading={loading}>
      <SelectedProjectProvider >
        <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
          <div className="flex">
            <div className="w-1/4 min-h-screen max-h-fit shadow">
              <ProjectList />
            </div>
            <div className="w-full h-full">
              <Workbench />
            </div>
          </div>
        </PageWithHeader>
      </SelectedProjectProvider>
    </LoadingAndError>
  )
}
