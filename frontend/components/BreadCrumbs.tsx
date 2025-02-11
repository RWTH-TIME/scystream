import Link from "next/link"

export type Crumb = {
  text: string,
  link: string,
}

export type BreadCrumbsProps = {
  breadcrumbs: Crumb[],
}

export default function BreadCrumbs({ breadcrumbs }: BreadCrumbsProps) {
  return (
    <div className="flex flex-row">
      {
        breadcrumbs.map((crumb, index) => (
          <div key={index}>
            <Link href={crumb.link}>
              {crumb.text}
            </Link>
            {index !== breadcrumbs.length - 1 && <span className="px-2">/</span>}
          </div>
        ))
      }
    </div>
  )
}
