"use client"

import Button from "@/components/Button"
import PageWithHeader from "@/components/layout/PageWithHeader"
import useAuth from "@/hooks/useAuth"

export default function Dashboard() {
  const { signOut } = useAuth()

  return (
    <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
      <div>
        DASHBOARD
        <Button onClick={(e) => {
          e.preventDefault()
          signOut()
        }}>SignOut</Button>
      </div>
    </PageWithHeader>
  )
}
