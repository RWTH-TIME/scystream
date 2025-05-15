import type { PropsWithChildren } from "react"
import { useState } from "react"
import Tabs from "./Tabs"

type ProjectCBSettingsDraggableProps = PropsWithChildren<{
  tabs: { key: string, label: string }[],
  activeTab: string,
  setActiveTab: React.Dispatch<React.SetStateAction<string>>,
}>

export default function ProjectCBSettingsDraggable({ children, tabs, activeTab, setActiveTab }: ProjectCBSettingsDraggableProps) {
  const [height, setHeight] = useState(300)

  const handleResize = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    e.preventDefault()
    const startY = e.clientY
    const startHeight = height

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newHeight = Math.max(200, startHeight + (startY - moveEvent.clientY))
      setHeight(newHeight)
    }

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove)
      document.removeEventListener("mouseup", onMouseUp)
    }

    document.addEventListener("mousemove", onMouseMove)
    document.addEventListener("mouseup", onMouseUp)
  }

  return (
    <div
      className="fixed bottom-0 w-full bg-white rounded-t-2xl shadow-lg border border-gray-200 z-30 overflow-auto"
      style={{ height: `${height}px` }}
    >
      <div
        className="h-4 bg-gray-100 cursor-ns-resize rounded-t-2xl flex justify-center items-center sticky top-0 z-10"
        onMouseDown={handleResize}
      >
        <div className="w-10 h-1 bg-gray-400 rounded-full"></div>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Content Passed from Parent */}
      <div className="p-4">{children}</div>
    </div>
  )
}

