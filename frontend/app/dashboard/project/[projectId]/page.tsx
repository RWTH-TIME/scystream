"use client"

import PageWithHeader from "@/components/layout/PageWithHeader"
import useAuth from "@/hooks/useAuth"
import LoadingAndError from "@/components/LoadingAndError"
import { use, useEffect, useState } from "react"
import Editor from "@/components/Editor"
import Tabs from "@/components/Tabs"
import ProjectDetail from "@/components/ProjectDetail"
import { useProjectQuery } from "@/mutations/projectMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"

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

  const { selectedProject, setSelectedProject } = useSelectedProject()
  const { data: project, isLoading: projectLoading, isError: projectError } = useProjectQuery(projectId)

  useEffect(() => {
    if (project) {
      setSelectedProject(project)
    }
  }, [project, setSelectedProject])


  const [activeTab, setActiveTab] = useState<string>("project")

  return (
    <LoadingAndError loading={loading || projectLoading} error={projectError}>
      <PageWithHeader breadcrumbs={[
        { text: "Dashboard", link: "/dashboard" },
        { text: "Project", link: "/dashboard" },
        { text: selectedProject?.name ?? "", link: "/project" }
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

