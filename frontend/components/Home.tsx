import Button, { ButtonSentiment } from "./Button"
import ProjectList, { ProjectListVariant } from "./ProjectList"

const mockTemplates = [
  { id: "a", name: "ETL Template", description: "Extract, Transform, Load basic pipeline" },
  { id: "b", name: "ML Training", description: "Template for training machine learning models" }
]

export default function Home() {
  return (
    <div className="flex flex-col h-full  p-6 overflow-hidden">
      <div className="flex flex-col flex-shrink-0 mb-4">
        <h2 className="text-xl font-semibold mb-2">Pipeline Templates</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mockTemplates.map((template) => (
            <div
              key={template.id}
              className="rounded-2xl border border-gray-200 shadow-sm p-4 bg-white flex flex-col justify-between"
            >
              <div>
                <h3 className="text-lg font-bold">{template.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{template.description}</p>
              </div>
              <Button sentiment={ButtonSentiment.POSITIVE} className="mt-5">Create from Template</Button>
            </div>
          ))}
        </div>
      </div>
      <div className="flex flex-col flex-1 overflow-hidden">
        <h2 className="text-xl font-semibold mb-2">Your Projects</h2>
        <ProjectList variant={ProjectListVariant.CARD} />
      </div>
    </div>
  )
}

