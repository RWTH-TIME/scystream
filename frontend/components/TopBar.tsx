import type { BreadCrumbsProps } from "./BreadCrumbs"
import BreadCrumbs from "./BreadCrumbs"

import { useEffect, useState } from "react"
import { getUser, logout } from "@/utils/auth/authService"
import { Logout } from "@mui/icons-material"

export type TopBarProps = Partial<BreadCrumbsProps>

export default function TopBar({ breadcrumbs }: TopBarProps) {
  const [user, setUser] = useState<string>("")

  useEffect(() => {
    async function fetchUser() {
      const fetchedUser = await getUser()
      if (fetchedUser?.profile?.name) {
        setUser(fetchedUser.profile.name)
      }
    }
    fetchUser()
  }, [])

  return (
    <div className="bg-black items-center text-white w-screen py-5 px-10 flex flex-row text-lg h-[80px]">
      {/* Breadcrumbs */}
      <div>
        <BreadCrumbs breadcrumbs={breadcrumbs ?? []} />
      </div>

      {/* User section */}
      <div className="flex flex-row items-center ml-auto uppercase tracking-wide">
        <span className="cursor-default">{user}</span>
        <button
          onClick={() => logout()}
          className="ml-4 p-1 text-red-500 hover:text-red-400 transition-colors cursor-pointer"
          title="Logout"
        >
          <Logout fontSize="medium" />
        </button>
      </div>
    </div>
  )
}
