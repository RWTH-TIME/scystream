"use client"

import "./globals.css"

import PageWithHeader from "@/components/layout/PageWithHeader";
import { useState } from "react";

export default function Home() {
  const [value, setValue] = useState("")

  return (
    <PageWithHeader breadcrumbs={[{ text: "Home", link: "/" }]}>
      Hi
    </PageWithHeader>
  );
}
