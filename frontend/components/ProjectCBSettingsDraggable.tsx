import type { PropsWithChildren } from "react"
import { useState } from "react"

type ProjectCBSettingsDraggableProps = PropsWithChildren<{}>

export default function ProjectCBSettingsDraggable({ children }: ProjectCBSettingsDraggableProps) {
  const [height, setHeight] = useState(300) // Initial height in pixels

  const handleResize = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    const startY = e.clientY
    const startHeight = height

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newHeight = Math.max(200, startHeight - (moveEvent.clientY - startY))
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
      className="fixed bottom-0 w-3/4 bg-white rounded-t-2xl shadow-lg border border-gray-200 z-30"
      style={{ height: `${height}px` }}
    >
      <div
        className="h-4 bg-gray-100 cursor-ns-resize rounded-t-2xl flex justify-center items-center"
        onMouseDown={handleResize}
      >
        <div className="w-10 h-1 bg-gray-400 rounded-full"></div>
      </div>
      <div className="p-5">
        {children}
      </div>
    </div>
  )
}
