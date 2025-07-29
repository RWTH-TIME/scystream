"use client"

import PageWithHeader from "@/components/layout/PageWithHeader"
import LoadingAndError from "@/components/LoadingAndError"
import { use, useEffect, useState } from "react"
import Tabs from "@/components/Tabs"
import ProjectDetail from "@/components/ProjectDetail"
import { useDeleteProjectMutation, useProjectQuery } from "@/mutations/projectMutation"
import { useSelectedProject } from "@/hooks/useSelectedProject"
import { useAlert } from "@/hooks/useAlert"
import { useProjectStatusWS, useTriggerWorkflowMutation } from "@/mutations/workflowMutations"
import { ReactFlowProvider } from "@xyflow/react"
import { Workbench } from "@/components/Workbench"
import { useRouter } from "next/navigation"
import { withAuth } from "@/hooks/useAuth"

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

function ProjectPage({ params }: ProjectPageProps) {
  const { projectId } = use(params)
  const { setAlert } = useAlert()
  const router = useRouter()

  // TODO: #166 remove useSelectedProject
  const { selectedProject, setSelectedProject } = useSelectedProject()
  const { data: project, isLoading: projectLoading, isError: projectError } = useProjectQuery(projectId, !selectedProject)

  const { mutate: deleteMutate, isPending: deleteLoading } = useDeleteProjectMutation(setAlert)
  const { mutateAsync: triggerWorkflow, isPending: triggerLoading } = useTriggerWorkflowMutation(setAlert)

  useProjectStatusWS(setAlert)

  function deleteProject(project_id: string) {
    router.push("/")
    deleteMutate(project_id)
  }

  // TODO: #166 Remove setSelectedProject => Use Params Instead
  useEffect(() => {
    if (project) {
      setSelectedProject(project)
    }
  }, [project, setSelectedProject])


  const [activeTab, setActiveTab] = useState<string>("project")

  return (
    <LoadingAndError loading={projectLoading} error={projectError}>
      <PageWithHeader breadcrumbs={[
        { text: "Dashboard", link: "/" },
        { text: "Project", link: "/" },
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

export default withAuth(ProjectPage)
