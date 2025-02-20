"use client"

import { ReactFlowProvider } from "@xyflow/react"
import PageWithHeader from "@/components/layout/PageWithHeader"
import ProjectList from "@/components/ProjectList"
import useAuth from "@/hooks/useAuth"
import Workbench from "@/components/Workbench"
import LoadingAndError from "@/components/LoadingAndError"
import { SelectedProjectProvider } from "@/hooks/useSelectedProject"
import { SelectedComputeBlockProvider } from "@/hooks/useSelectedComputeBlock"

export default function Dashboard() {
  const { loading } = useAuth()

  return (
    <LoadingAndError loading={loading}>
      <SelectedProjectProvider>
        <SelectedComputeBlockProvider>
          <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
            <div className="flex h-full">
              {/* ProjectList is scrollable and takes 1/4 width */}
              <div className="w-1/4 h-full overflow-y-auto shadow">
                <ProjectList />
              </div>
              {/* Workbench takes the rest of the space */}
              <div className="flex-grow h-full">
                <ReactFlowProvider>
                  <Workbench />
                </ReactFlowProvider>
              </div>
            </div>
          </PageWithHeader>
        </SelectedComputeBlockProvider>
      </SelectedProjectProvider>
    </LoadingAndError>
  )
}
