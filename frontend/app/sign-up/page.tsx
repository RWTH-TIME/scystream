"use client"

import Link from "next/link"
import { useState } from "react"
import Button from "@/components/Button"
import Input from "@/components/inputs/Input"
import InputAdornment from "@/components/inputs/InputAdornment"
import PageWithHeader from "@/components/layout/PageWithHeader"

export default function Register() {
  // TODO: form-validation

  const [mail, setMail] = useState<string>("")
  const [password, setPassword] = useState<string>("")
  const [passwordRep, setPasswordRep] = useState<string>("")

  const [showPass, setShowPass] = useState<boolean>(false)

  return (
    <PageWithHeader breadcrumbs={[{ text: "Signup", link: "/sign-up" }]}>
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
        <Input
          type="password"
          value={passwordRep}
          label="Repeat password"
          onChange={setPasswordRep}
          leftAdornment={<InputAdornment type="password" />}
        />
        <Button>Create Account</Button>
        <Link href="login"><u>Already have an account? - Login here</u></Link>
      </div>
    </PageWithHeader>
  )
}
