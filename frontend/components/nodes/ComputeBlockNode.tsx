import { Handle, Position } from "@xyflow/react"
import React from "react"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import type { ComputeBlock, InputOutput } from "../CreateComputeBlockModal";
import { InputOutputType } from "../CreateComputeBlockModal"

/*
* The Compute block node is a node for our Workbench Component.
*/
export default function ComputeBlockNode({ data }: { data: ComputeBlock }) {
  const { selectedComputeBlock } = useSelectedComputeBlock()

  const getHandleStyle = (type: InputOutputType) => {
    switch (type) {
      case InputOutputType.FILE:
        return {
          backgroundImage: "url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22white%22><path d=%22M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM13 3.5L18.5 9H14a1 1 0 0 1-1-1V3.5zM7 15h10v2H7v-2zm0-4h10v2H7v-2z%22/></svg>')",
          backgroundColor: "#4FC3F7"
        }
      case InputOutputType.DB:
        return {
          backgroundImage: "url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22white%22><path d=%22M12 2C6.48 2 2 3.57 2 5.5v13c0 1.93 4.48 3.5 10 3.5s10-1.57 10-3.5v-13C22 3.57 17.52 2 12 2zM4 8.48c2.37.95 5.24 1.52 8 1.52s5.63-.57 8-1.52V12c-2.37.95-5.24 1.52-8 1.52s-5.63-.57-8-1.52V8.48zm16 10c-2.37.95-5.24 1.52-8 1.52s-5.63-.57-8-1.52v-2.92c2.37.95 5.24 1.52 8 1.52s5.63-.57 8-1.52v2.92z%22/></svg>')",
          backgroundColor: "#4DB6AC"
        }
      default:
        return {
          backgroundImage: "",
          backgroundColor: "grey"
        }
    }
  }

  const renderHandles = (items: InputOutput[], type: "target" | "source", position: Position) => {
    return items.map((item, index) => (
      <Handle
        key={index}
        type={type}
        position={position}
        id={`${type}-${index}`}
        style={{
          ...getHandleStyle(item.data_type),
          width: "15px",
          height: "15px",
          borderRadius: "50%",
          top: `${(index + 1) * 20}%`,
        }}
      />
    ));
  };

  return (
    <div>
      <div className={`flex flex-col bg-gray-50 border ${selectedComputeBlock?.id === data.id ? "border-blue-400" : "border-gray-300"} rounded shadow-md p-3 space-y-4 text-sm w-64`}>
        <div className="flex place-content-between items-center">
          <div className="text-lg font-bold text-gray-800">{data.name}</div>
        </div>
        <span className="w-full h-[1px] bg-black"></span>
        <div className="flex flex-col space-y-2">
          <div>
            <span className="font-medium text-gray-600">Entrypoint</span><br />
            {data.selected_entrypoint.name}
          </div>
          <div>
            <span className="font-medium text-gray-600">Author</span><br />
            {data.author}
          </div>
          <div>
            <span className="font-medium text-gray-600">Image:</span><br />
            {data.image}
          </div>
        </div>
        {renderHandles(data.selected_entrypoint.inputs, "target", Position.Left)}
        {renderHandles(data.selected_entrypoint.outputs, "target", Position.Right)}
      </div>
    </div>
  )
}
