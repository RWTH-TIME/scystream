"use client"

import Link from "next/link"
import { useState } from "react"
import { useRouter } from "next/navigation"
import Button from "@/components/Button"
import Input from "@/components/inputs/Input"
import InputAdornment from "@/components/inputs/InputAdornment"
import PageWithHeader from "@/components/layout/PageWithHeader"
import { useLoginMutation } from "@/mutations/userMutation"

export default function Login() {
  const [mail, setMail] = useState<string>("")
  const [password, setPassword] = useState<string>("")
  const [showPass, setShowPass] = useState<boolean>(false)

  const { mutateAsync } = useLoginMutation()

  const router = useRouter()

  async function logIn(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    try {
      await mutateAsync({ email: mail, password })
      router.push("/dashboard")
    } catch (error) {
      console.error("Login failed")
    }
  }

  return (
    <PageWithHeader breadcrumbs={[{ text: "Login", link: "/login" }]}>
      <form onSubmit={(e) => logIn(e)} className="w-1/4 bg-slate-50 m-auto p-10 min-h-96 rounded-lg flex flex-col gap-5 drop-shadow justify-center">
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
      </form>
    </PageWithHeader>
  )
}
