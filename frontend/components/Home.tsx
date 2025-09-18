import { useWorkflowTemplatesQuery } from "@/mutations/workflowMutations"
import Button, { ButtonSentiment } from "./Button"
import ProjectList from "./ProjectList"
import LoadingAndError from "./LoadingAndError"
import CreateProjectModal from "./CreateProjectModal"
import { useState } from "react"
import { useCreateProjectFromTemplateMutation } from "@/mutations/projectMutation"
import { useAlert } from "@/hooks/useAlert"

export default function Home() {
  const { setAlert } = useAlert()
  const [createProjectOpen, setCreateProjectOpen] = useState<boolean>(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)

  const { data: templatesByTag, isLoading, isError } = useWorkflowTemplatesQuery()
  const { mutate: createProjectMutate, isPending: createLoading } = useCreateProjectFromTemplateMutation(setAlert)

  return (
    <div className="flex flex-col h-full p-6 overflow-hidden">
      <CreateProjectModal
        isOpen={createProjectOpen}
        onClose={() => setCreateProjectOpen(false)}
        title="Create Project from Template"
        loading={createLoading}
        onSubmit={(name) => {
          if (selectedTemplate) {
            createProjectMutate({ name, template_identifier: selectedTemplate })
          }
        }}
      />
      <div className="flex flex-col flex-shrink-0 mb-6">
        <h2 className="text-xl font-semibold mb-4 pb-2">
          Pipeline Templates
        </h2>

        <LoadingAndError loading={isLoading} error={isError}>
          {templatesByTag && Object.entries(templatesByTag).map(([tag, templates]) => (
            <section
              key={tag}
              className="mb-8 border border-gray-200 rounded-md bg-white shadow-sm"
            >
              <header className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h3 className="text-lg font-semibold capitalize text-gray-800">{tag}</h3>
              </header>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
                {templates.map((template) => (
                  <article
                    key={template.file_identifier}
                    className="flex flex-col justify-between rounded border border-gray-300 p-4 hover:shadow-md transition-shadow"
                  >
                    <div>
                      <h4 className="text-md font-semibold text-gray-900">{template.name}</h4>
                      <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                    </div>
                    <Button
                      sentiment={ButtonSentiment.POSITIVE}
                      className="mt-6 self-start"
                      onClick={() => {
                        setSelectedTemplate(template.file_identifier)
                        setCreateProjectOpen(true)
                      }}
                    >
                      <LoadingAndError
                        loading={createLoading && (template.file_identifier === selectedTemplate)}
                        iconSize={21}
                      >
                        Create from Template
                      </LoadingAndError>
                    </Button>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </LoadingAndError>
      </div>


      <div className="flex flex-col flex-1 overflow-hidden">
        <h2 className="text-lg font-semibold mb-2">Your Projects</h2>
        <ProjectList />
      </div>
    </div>
  )
}
