"use client"

import { useState } from "react"
import PageWithHeader from "@/components/layout/PageWithHeader"
import ProjectList from "@/components/ProjectList"
import useAuth from "@/hooks/useAuth"
import type { Project } from "@/utils/types"
import Workbench from "@/components/Workbench"
import LoadingAndError from "@/components/LoadingAndError"

export default function Dashboard() {
  const { loading } = useAuth()

  const [selectedProject, setSelectedProject] = useState<Project | undefined>(undefined)

  return (
    <LoadingAndError loading={loading}>
      <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
        <div className="flex">
          <div className="w-1/4 min-h-screen max-h-fit shadow">
            <ProjectList selectedProject={selectedProject} setSelectedProject={setSelectedProject} />
          </div>
          <div className="w-full h-full">
            {selectedProject ? <Workbench selectedProject={selectedProject} /> : <>Select a Project...</>}
          </div>
        </div>
      </PageWithHeader>
    </LoadingAndError>
  )
}
