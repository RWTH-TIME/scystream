import type { PropsWithChildren } from "react"
import type { TopBarProps } from "../TopBar"
import TopBar from "../TopBar"

type PageWithHeaderProps = Partial<TopBarProps>

export default function PageWithHeader({ children, breadcrumbs }: PropsWithChildren<PageWithHeaderProps>) {
  return (
    <div className="flex flex-col h-screen w-screen">
      <TopBar breadcrumbs={breadcrumbs} />
      <div className="flex-1 overflow-y-auto">
        {children}
      </div>
    </div>
  )
}
