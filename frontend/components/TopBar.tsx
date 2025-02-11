import Image from "next/image"
import type { BreadCrumbsProps } from "./BreadCrumbs"
import BreadCrumbs from "./BreadCrumbs"

import logo from "@/public/logo.png"

export type TopBarProps = Partial<BreadCrumbsProps>

export default function TopBar({ breadcrumbs }: TopBarProps) {
  return (
    <div className="bg-black items-center text-white w-screen py-5 px-10 flex flex-row text-lg h-[80px]">
      <div className="">
        <BreadCrumbs breadcrumbs={breadcrumbs ? breadcrumbs : []} />
      </div>
      <div className="flex flex-row items-center ml-auto uppercase font-bold italic gap-x-1.5 tracking-wide">
        <Image src={logo} alt="logo" width={40} height={40} />
        scystream
      </div>
    </div>
  )
}
