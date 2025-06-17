"use client"

import PageWithHeader from "@/components/layout/PageWithHeader"
import useAuth from "@/hooks/useAuth"
import LoadingAndError from "@/components/LoadingAndError"
import { use, useEffect, useState } from "react"
import Tabs from "@/components/Tabs"
import ProjectDetail from "@/components/ProjectDetail"
import { useDeleteProjectMutation, useProjectQuery } from "@/mutations/projectMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import { useAlert } from "@/hooks/useAlert"
import { useTriggerWorkflowMutation } from "@/mutations/workflowMutations"
import { ReactFlowProvider } from "@xyflow/react"
import { Workbench } from "@/components/Workbench"
import { useRouter } from "next/navigation"

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
  const { setAlert } = useAlert()
  const router = useRouter()

  const { selectedProject, setSelectedProject } = useSelectedProject()
  const { data: project, isLoading: projectLoading, isError: projectError } = useProjectQuery(projectId)

  const { mutate: deleteMutate, isPending: deleteLoading } = useDeleteProjectMutation(setAlert)
  const { mutateAsync: triggerWorkflow, isPending: triggerLoading } = useTriggerWorkflowMutation(setAlert)
  // TODO: Status Websocket

  function deleteProject(project_id: string) {
    router.push("/dashboard")
    deleteMutate(project_id)
  }

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
          {activeTab === "project" && selectedProject !== undefined && (
            <ProjectDetail
              deleteProject={deleteProject}
              isProjectDeleteLoading={deleteLoading}
              triggerWorkflow={triggerWorkflow}
              isTriggerWorkflowLoading={triggerLoading}
            />
          )}
          {activeTab === "editor" && selectedProject != undefined && (
            <div className="flex h-full">
              <div className="flex-grow h-full">
                <ReactFlowProvider>
                  <Workbench
                    deleteProject={deleteProject}
                    isProjectDeleteLoading={deleteLoading}
                    triggerWorkflow={triggerWorkflow}
                    isTriggerWorkflowLoading={triggerLoading}
                  />
                </ReactFlowProvider>
              </div>
            </div>
          )
          }
        </div>
      </PageWithHeader>
    </LoadingAndError>
  )
}

