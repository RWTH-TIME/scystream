import { ReactFlowProvider } from "@xyflow/react"
import { Workbench } from "./Workbench"

export default function Editor() {
  return (
    <div className="flex h-full">
      <div className="flex-grow h-full">
        <ReactFlowProvider>
          <Workbench />
        </ReactFlowProvider>
      </div>
    </div>
  )
}
