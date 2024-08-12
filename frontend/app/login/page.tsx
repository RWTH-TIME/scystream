"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import Button from "@/components/Button"
import Input from "@/components/inputs/Input"
import InputAdornment from "@/components/inputs/InputAdornment"
import PageWithHeader from "@/components/layout/PageWithHeader"
import { getConfig } from "@/utils/config"

export default function Login() {
  const config = getConfig()

  const [mail, setMail] = useState<string>("")
  const [password, setPassword] = useState<string>("")

  const [showPass, setShowPass] = useState<boolean>(false)

  useEffect(() => {
    console.log(config)
  }, [config])

  return (
    <PageWithHeader breadcrumbs={[{ text: "Login", link: "/login" }]}>
      <div className="w-1/4 bg-slate-50 m-auto p-10 min-h-96 rounded-lg flex flex-col gap-5 drop-shadow justify-center">
        <Input
          type="text"
          value={mail}
          label="E-Mail"
          onChange={setMail}
          leftAdornment={<InputAdornment type="email" />}
        />
        <Input
          type={showPass ? "text" : "password"}
          value={password}
          label="Password"
          onChange={setPassword}
          leftAdornment={<InputAdornment type="password" />}
          rightAdornment={<InputAdornment type={showPass ? "visibility" : "visibilityOff"} onClick={() => setShowPass(!showPass)} />}
        />
        <Button>LogIn</Button>
        <Link href="sign-up"><u>{"Don't have an account? - Sign up here"}</u></Link>
      </div>
    </PageWithHeader>
  )
}
