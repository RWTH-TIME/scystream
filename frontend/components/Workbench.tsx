import { useState, useCallback, useMemo } from "react"
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges
} from "@xyflow/react"
import ComputeBlockNode from "./nodes/ComputeBlockNode"
import "@xyflow/react/dist/style.css"

const initialNodes = [
  {
    id: "node-1-cb-uuid",
    position: { x: 0, y: 0 },
    type: "computeBlock",
    data: {
      name: "Crawl Tagesschau",
      selectedEntrypoint: "crawl_tagesschau",
      author: "Jon Doe",
      dockerImage: "ghcr.io/RWTH-TIME/crawler",
      inputs: [
        {
          description: "URLs Files",
          type: "file",
          config: {
            MINIO_ENDPOINT: "localhost:9000",
            MINIO_PORT: 5432,
          },
        },
      ],
      outputs: [
        {
          description: "Processed Data",
          type: "file",
          config: {
            MINIO_ENDPOINT: "localhost:9000",
            MINIO_PORT: 5432,
          },
        },
        {
          description: "Processed Data",
          type: "db_table",
          config: {
            MINIO_ENDPOINT: "localhost:9000",
            MINIO_PORT: 5432,
          },
        },
        {
          description: "Processed Data",
          type: "db_table",
          config: {
            MINIO_ENDPOINT: "localhost:9000",
            MINIO_PORT: 5432,
          },
        },
      ],
    },
  },
  {
    id: "node-2-cb-uuid",
    position: { x: 100, y: 100 },
    type: "computeBlock",
    data: {
      name: "Topic Modelling",
      selectedEntrypoint: "topic_modelling",
      author: "Markus Meilenstein",
      dockerImage: "ghcr.io/RWTH-TIME/nlp",
      inputs: [
        {
          description: "Text Files",
          type: "db_table",
          config: {
            MINIO_ENDPOINT: "localhost:9000",
            MINIO_PORT: 5432,
          },
        },
      ],
      outputs: [
        {
          description: "Topic Model",
          type: "file",
          config: {
            MINIO_ENDPOINT: "localhost:9000",
            MINIO_PORT: 5432,
          },
        },
      ],
    },
  },

]

export default function Workbench() {
  const nodeTypes = useMemo(() => ({ computeBlock: ComputeBlockNode }), [])
  const [nodes, setNodes] = useState(initialNodes)

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  )

  return (
    <div style={{ height: "100%" }}>
      <ReactFlow
        nodeTypes={nodeTypes}
        nodes={nodes}
        onNodesChange={onNodesChange}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  )
}
