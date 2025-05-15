"use client"

import PageWithHeader from "@/components/layout/PageWithHeader"
import useAuth from "@/hooks/useAuth"
import LoadingAndError from "@/components/LoadingAndError"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import { use, useState } from "react"
import Editor from "@/components/Editor"
import Tabs from "@/components/Tabs"
import ProjectDetail from "@/components/ProjectDetail"

type ProjectPageParams = {
  projectId: string,
}

type ProjectPageProps = {
  params: Promise<ProjectPageParams>,
}

const TABS = [
  { key: "project", label: "Project" },
  { key: "editor", label: "Editor" }
]

export default function ProjectPage({ params }: ProjectPageProps) {
  const { projectId } = use(params)

  const { loading } = useAuth()
  const { selectedProject } = useSelectedProject()
  // const { data: projectDetails, isLoading, isError } = useComputeBlocksByProjectQuery(projectId)
  console.log(projectId)

  const [activeTab, setActiveTab] = useState<string>("project")

  return (
    <LoadingAndError loading={loading}>
      <PageWithHeader breadcrumbs={[
        { text: "Dashboard", link: "/dashboard" },
        { text: "Project", link: "/dashboard" },
        { text: selectedProject?.name ?? "", link: "/dashboard/project/" }
      ]}>
        <div className="flex flex-col h-full">
          <Tabs activeTab={activeTab} setActiveTab={setActiveTab} tabs={TABS} />
          {activeTab === "project" && <ProjectDetail />}
          {activeTab === "editor" && <Editor />}
        </div>
      </PageWithHeader>
    </LoadingAndError>
  )
}

