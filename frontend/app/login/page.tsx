"use client"

import Input from "@/components/inputs/Input";
import PageWithHeader from "@/components/layout/PageWithHeader";
import { useState } from "react";

export default function Login() {
  const [mail, setMail] = useState<string>("")
  const [password, setPassword] = useState<string>("")

  return (
    <PageWithHeader breadcrumbs={[{ text: "LogIn", link: "/login" }]}>
      <div className="w-1/4 bg-slate-100 m-auto p-10 h-1/8 rounded-lg flex flex-col gap-5 drop-shadow">
        <Input type="text" value={mail} label="E-Mail" onChange={setMail} />
        <Input type="text" value={password} label="Password" onChange={setPassword} />
        <Input type="button" value={"LogIn"} />
      </div>
    </PageWithHeader>
  )
}
