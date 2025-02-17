"use client"

import { AlertType, useAlert } from "@/hooks/useAlert"

const alertColors: { [key in AlertType]: string } = {
  [AlertType.SUCCESS]: "bg-green-600",
  [AlertType.ERROR]: "bg-red-600",
  [AlertType.DEFAULT]: "bg-gray-900",
}

export default function Alert() {
  const { text, type } = useAlert()
  const alertColor = alertColors[type] || alertColors[AlertType.DEFAULT]

  if (text) {
    return (
      <div className={`${alertColor} z-50 text-white p-4 rounded-md fixed bottom-5 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex justify-between items-center`}>
        {text}
      </div>
    )
  }
}
