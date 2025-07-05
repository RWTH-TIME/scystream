import type { BreadCrumbsProps } from "./BreadCrumbs"
import BreadCrumbs from "./BreadCrumbs"

import { useEffect, useState } from "react"
import { getUser, logout } from "@/utils/auth/authService"

export type TopBarProps = Partial<BreadCrumbsProps>

export default function TopBar({ breadcrumbs }: TopBarProps) {
  const [user, setUser] = useState<string>("")

  useEffect(() => {
    async function fetchUser() {
      const fetchedUser = await getUser()

      if (fetchedUser != undefined && fetchedUser.profile && fetchedUser.profile.name) {
        setUser(fetchedUser.profile.name)
      }
    }

    fetchUser()
  }, [])

  return (
    <div className="bg-black items-center text-white w-screen py-5 px-10 flex flex-row text-lg h-[80px]">
      <div className="">
        <BreadCrumbs breadcrumbs={breadcrumbs ? breadcrumbs : []} />
      </div>
      <div className="flex flex-row items-center ml-auto uppercase gap-x-1.5 tracking-wide cursor-pointer">
        <a onClick={() => logout()}>
          {user}
        </a>
      </div>
    </div>
  )
}
