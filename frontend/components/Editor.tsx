import { ReactFlowProvider } from "@xyflow/react"
import ProjectList, { ProjectListVariant } from "./ProjectList"
import { Workbench } from "./Workbench"

export default function Editor() {
  return (
    <div className="flex h-full">
      <div className="w-1/4 h-full overflow-y-auto shadow">
        <ProjectList variant={ProjectListVariant.LIST} />
      </div>
      <div className="flex-grow h-full">
        <ReactFlowProvider>
          <Workbench />
        </ReactFlowProvider>
      </div>
    </div>
  )
}
