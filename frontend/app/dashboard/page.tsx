"use client"

import PageWithHeader from "@/components/layout/PageWithHeader"
import useAuth from "@/hooks/useAuth"
import LoadingAndError from "@/components/LoadingAndError"
import { SelectedProjectProvider } from "@/hooks/useSelectedProject"
import { SelectedComputeBlockProvider } from "@/hooks/useSelectedComputeBlock"
import Editor from "@/components/Editor"
import { useState } from "react"
import Home from "@/components/Home"
import { useAlert } from "@/hooks/useAlert"
import { useProjectStatusWS } from "@/mutations/workflowMutations"

const TABS = [
  { key: "home", label: "Home" },
  { key: "editor", label: "Editor" }
]

export default function Dashboard() {
  const { loading } = useAuth()
  const { setAlert } = useAlert()

  const [activeTab, setActiveTab] = useState<string>("home")

  useProjectStatusWS(setAlert)

  return (
    <LoadingAndError loading={loading}>
      <SelectedProjectProvider>
        <SelectedComputeBlockProvider>
          <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
            <div className="flex flex-col h-full">
              <div>
                {TABS.map(({ key, label }) => (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key)}
                    className={`
                    relative
                    p-4
                    font-semibold
                    text-sm
                    transition-colors
                    focus:outline-none
                    ${activeTab === key ? "text-indigo-600" : "text-gray-500 hover:text-indigo-500"}
                  `}
                  >
                    {label}
                    {activeTab === key && (
                      <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 rounded-t"></span>
                    )}
                  </button>
                ))}
              </div>
              {activeTab === "home" && <Home />}
              {activeTab === "editor" && <Editor />}
            </div>
          </PageWithHeader>
        </SelectedComputeBlockProvider>
      </SelectedProjectProvider>
    </LoadingAndError>
  )
}

