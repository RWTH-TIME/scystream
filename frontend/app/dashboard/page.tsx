"use client"

import { useState } from "react"
import Button from "@/components/Button"
import PageWithHeader from "@/components/layout/PageWithHeader"
import ProjectList from "@/components/ProjectList"
import useAuth from "@/hooks/useAuth"
import { useTestMutation } from "@/mutations/userMutation"
import type { Project } from "@/utils/types"
import { useAlert } from "@/hooks/useAlert"

export default function Dashboard() {
  const { setAlert } = useAlert()
  const [selectedProject, setSelectedProject] = useState<Project | undefined>(undefined)
  const { signOut, loading } = useAuth()

  const { mutate } = useTestMutation(setAlert)

  function test() {
    mutate({ old_access_token: "abc", refresh_token: "acs" })
  }

  return !loading ? (
    <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
      <div className="flex">
        <div className="w-1/6 h-screen shadow-sm h-full">
          <ProjectList selectedProject={selectedProject} setSelectedProject={setSelectedProject} />
        </div>
        <div>
          Selected Project: {selectedProject?.name}
          <Button onClick={(e) => {
            e.preventDefault()
            signOut()
          }}>SignOut</Button>
          <Button onClick={(e) => {
            e.preventDefault()
            test()
          }}>Test</Button>
        </div>
      </div>
    </PageWithHeader>
  ) : (<></>)
}
