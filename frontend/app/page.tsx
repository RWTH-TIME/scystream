"use client"

import { ReactFlowProvider } from "@xyflow/react"
import PageWithHeader from "@/components/layout/PageWithHeader"
import ProjectList from "@/components/ProjectList"
import { SelectedProjectProvider } from "@/hooks/useSelectedProject"
import { SelectedComputeBlockProvider } from "@/hooks/useSelectedComputeBlock"
import { Workbench } from "@/components/Workbench"
import { withAuth } from "@/hooks/useAuth"

function Dashboard() {


  return (
    <SelectedProjectProvider>
      <SelectedComputeBlockProvider>
        <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/" }]}>
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
  )
}


export default withAuth(Dashboard)
