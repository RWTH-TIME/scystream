"use client"

import { useState } from "react"
import Button from "@/components/Button"
import PageWithHeader from "@/components/layout/PageWithHeader"
import ProjectList from "@/components/ProjectList"
import useAuth from "@/hooks/useAuth"
import { useTestMutation } from "@/mutations/userMutation"
import { v4 as uuidv4 } from "uuid"

const projects = [
  {
    uuid: uuidv4(),
    name: "Projekt 1",
    created_at: Date.now()
  },
  {
    uuid: uuidv4(),
    name: "Projekt 2",
    created_at: Date.now()
  },
  {
    uuid: uuidv4(),
    name: "Projekt 3",
    created_at: Date.now()
  },
]

export default function Dashboard() {
  const [ selectedProject, setSelectedProject ] = useState<Project | undefined>(null);
  const { signOut, loading } = useAuth()

  const { mutateAsync } = useTestMutation()

  async function test() {
    await mutateAsync({ old_access_token: "abc", refresh_token: "acs" })
  }

  return !loading ? (
    <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
      <div className="flex">
        <div className="w-1/6 h-screen">
          <ProjectList selectedProject={selectedProject} setSelectedProject={setSelectedProject} />
        </div>
        <div>
          Selected Project: { selectedProject?.name }
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
