import type { XYPosition } from "@xyflow/react"
import { Handle, Position } from "@xyflow/react"
import React from "react"
import { useSelectedComputeBlock } from "@/hooks/useSelectedComputeBlock"
import type { ComputeBlock, InputOutput } from "../CreateComputeBlockModal"
import { InputOutputType } from "../CreateComputeBlockModal"

export interface ComputeBlockNodeType extends Node {
  id: string,
  position: XYPosition,
  type: string,
  data: ComputeBlock,
}

/*
* The Compute block node is a node for our Workbench Component.
*/
export default function ComputeBlockNode({ data }: { data: ComputeBlock }) {
  const { selectedComputeBlock } = useSelectedComputeBlock()

  const handleStyles = {
    [InputOutputType.FILE]: {
      backgroundImage: "url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22white%22><path d=%22M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM13 3.5L18.5 9H14a1 1 0 0 1-1-1V3.5zM7 15h10v2H7v-2zm0-4h10v2H7v-2z%22/></svg>')",
      backgroundColor: "#4FC3F7",
    },
    [InputOutputType.DB]: {
      backgroundImage: "url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22white%22><path d=%22M12 2C6.48 2 2 3.57 2 5.5v13c0 1.93 4.48 3.5 10 3.5s10-1.57 10-3.5v-13C22 3.57 17.52 2 12 2zM4 8.48c2.37.95 5.24 1.52 8 1.52s5.63-.57 8-1.52V12c-2.37.95-5.24 1.52-8 1.52s-5.63-.57-8-1.52V8.48zm16 10c-2.37.95-5.24 1.52-8 1.52s-5.63-.57-8-1.52v-2.92c2.37.95 5.24 1.52 8 1.52s5.63-.57 8-1.52v2.92z%22/></svg>')",
      backgroundColor: "#4DB6AC",
    },
    [InputOutputType.CUSTOM]: {
      backgroundImage: "url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22white%22><path d=%22M12 2L2 7l10 5 10-5-10-5zm0 8.75L4 7l8-4 8 4-8 3.75zm-6 4.25v4.5L12 22l6-3.5v-4.5L12 19l-6-4z%22/></svg>')",
      backgroundColor: "#FFB74D",
    },
  }


  const renderHandles = (items: InputOutput[], type: "target" | "source", position: Position) => {
    return items.map((item, index) => {
      return (
        <Handle
          key={index}
          type={type}
          position={position}
          id={item.id}
          style={{
            ...handleStyles[item.data_type] || {
              backgroundImage: "",
              backgroundColor: "grey",
            },
            width: "15px",
            height: "15px",
            borderRadius: "50%",
            top: `${(index + 1) * 20}%`,
          }}
        />
      )
    })
  }

  return (
    <div className="flex justify-center items-center p-4">
      <div
        className={`w-full max-w-sm bg-white border rounded-lg shadow-lg p-6 ${selectedComputeBlock?.id === data.id ? "border-blue-400" : "border-gray-300"
          } transition duration-150 ease-in-out hover:bg-gray-50 hover:shadow-xl`}
      >
        <div className="flex justify-between items-center">
          <h3 className="text-xl font-semibold text-gray-800">{data.custom_name}</h3>
        </div>
        <div className="flex items-center">
          <h3 className="text-sm text-gray-600">{data.name}</h3>
        </div>

        <hr className="border-t border-gray-200 my-3" />

        <div className="space-y-2">
          <div>
            <span className="block text-sm font-medium text-gray-600">Description</span>
            <p className="text-sm text-gray-800">{data.description}</p>
          </div>
          <div>
            <span className="block text-sm font-medium text-gray-600">Entrypoint: {data.selected_entrypoint.name}</span>
            <p className="text-sm text-gray-800">{data.selected_entrypoint.description}</p>
          </div>

          <div>
            <span className="block text-sm font-medium text-gray-600">Author</span>
            <p className="text-sm text-gray-800">{data.author}</p>
          </div>

          <div>
            <span className="block text-sm font-medium text-gray-600">Image</span>
            <p className="text-sm text-gray-800">{data.image}</p>
          </div>
        </div>

        <div className="space-y-2">
          {renderHandles(data.selected_entrypoint.inputs, "target", Position.Left)}
          {renderHandles(data.selected_entrypoint.outputs, "source", Position.Right)}
        </div>
      </div>
    </div>
  )

}
