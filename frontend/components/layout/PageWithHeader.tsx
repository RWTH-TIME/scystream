import { PropsWithChildren } from "react"
import TopBar, { TopBarProps } from "../TopBar"

type PageWithHeaderProps = Partial<TopBarProps>

export default function PageWithHeader({ children, breadcrumbs }: PropsWithChildren<PageWithHeaderProps>) {
  return (
    <div className="w-screen h-screen flex flex-col">
      <TopBar breadcrumbs={breadcrumbs} />
      {children}
    </div>
  )
}
