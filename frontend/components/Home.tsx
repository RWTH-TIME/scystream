import { useWorkflowTemplatesQuery } from "@/mutations/workflowMutations"
import Button, { ButtonSentiment } from "./Button"
import ProjectList, { ProjectListVariant } from "./ProjectList"
import LoadingAndError from "./LoadingAndError"
import CreateProjectModal from "./CreateProjectModal"
import { useState } from "react"
import { useCreateProjectFromTemplateMutation } from "@/mutations/projectMutation"
import { useAlert } from "@/hooks/useAlert"

export default function Home() {
  const { setAlert } = useAlert()
  const [createProjectOpen, setCreateProjectOpen] = useState<boolean>(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)

  const { data: templates, isLoading, isError } = useWorkflowTemplatesQuery()
  const { mutate: createProjectMutate, isPending: createLoading } = useCreateProjectFromTemplateMutation(setAlert)

  return (
    <div className="flex flex-col h-full  p-6 overflow-hidden">
      <CreateProjectModal
        isOpen={createProjectOpen}
        onClose={() => {
          setCreateProjectOpen(false)
        }}
        title="Create Project from Template"
        loading={createLoading}
        onSubmit={(name) => {
          if (selectedTemplate) {
            createProjectMutate({ name, template_identifier: selectedTemplate })
          }
        }}
      />
      <div className="flex flex-col flex-shrink-0 mb-4">
        <h2 className="text-xl font-semibold mb-2">Pipeline Templates</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <LoadingAndError loading={isLoading} error={isError}>
            {templates?.map((template: { file_identifier: string, name: string, description: string }) => (
              <div
                key={template.file_identifier}
                className="rounded-2xl border border-gray-200 shadow-sm p-4 bg-white flex flex-col justify-between"
              >
                <div>
                  <h3 className="text-lg font-bold">{template.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                </div>
                <Button
                  sentiment={ButtonSentiment.POSITIVE}
                  className="mt-5"
                  onClick={() => {
                    setSelectedTemplate(template.file_identifier)
                    setCreateProjectOpen(true)
                  }}
                >
                  <LoadingAndError loading={createLoading && (template.file_identifier === selectedTemplate)} iconSize={21}>
                    Create from Template
                  </LoadingAndError>
                </Button>
              </div>
            ))}
          </LoadingAndError>
        </div>
      </div>
      <div className="flex flex-col flex-1 overflow-hidden">
        <h2 className="text-xl font-semibold mb-2">Your Projects</h2>
        <ProjectList variant={ProjectListVariant.CARD} />
      </div>
    </div>
  )
}

