"use client"

import Button from "@/components/Button"
import PageWithHeader from "@/components/layout/PageWithHeader"
import useAuth from "@/hooks/useAuth"
import { useTestMutation } from "@/mutations/userMutation"

export default function Dashboard() {
  const { signOut, loading } = useAuth()

  const { mutateAsync } = useTestMutation()

  async function test() {
    try {
      await mutateAsync({ access_token: "abc", refresh_token: "acs" })
    } catch (error) {
      console.error(`Test failed: ${error}`)
    }
  }

  return !loading ? (
    <PageWithHeader breadcrumbs={[{ text: "Dashboard", link: "/dashboard" }]}>
      <div>
        DASHBOARD
        <Button onClick={(e) => {
          e.preventDefault()
          signOut()
        }}>SignOut</Button>
        <Button onClick={(e) => {
          e.preventDefault()
          test()
        }}>Test</Button>
      </div>
    </PageWithHeader>
  ) : (<></>)
}
