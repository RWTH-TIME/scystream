import PageWithHeader from "@/components/layout/PageWithHeader"

export default function Home() {
  return (
    <PageWithHeader breadcrumbs={[{ text: "Home", link: "/" }]}>
    </PageWithHeader>
  )
}
