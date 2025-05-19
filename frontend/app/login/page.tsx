"use client"

import Link from "next/link"
import { useState } from "react"
import Button, { ButtonSentiment } from "@/components/Button"
import Input from "@/components/inputs/Input"
import InputAdornment from "@/components/inputs/InputAdornment"
import PageWithHeader from "@/components/layout/PageWithHeader"
import { useLoginMutation } from "@/mutations/userMutation"
import { useAlert } from "@/hooks/useAlert"

export default function Login() {
  const { setAlert } = useAlert()
  const [mail, setMail] = useState<string>("")
  const [password, setPassword] = useState<string>("")
  const [showPass, setShowPass] = useState<boolean>(false)

  const { mutate } = useLoginMutation(setAlert)

  function logIn(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    mutate({ email: mail, password })
  }

  return (
    <PageWithHeader breadcrumbs={[{ text: "Login", link: "/login" }]}>
      <div className="flex items-center justify-center h-full">
        <form
          onSubmit={logIn}
          className="w-1/2 bg-slate-50 p-10 min-h-96 rounded-lg flex flex-col gap-5 drop-shadow-sm justify-center"
        >
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
            rightAdornment={(
              <InputAdornment
                type={showPass ? "visibility" : "visibilityOff"}
                onClick={() => setShowPass(!showPass)}
              />
            )}
          />
          <Button sentiment={ButtonSentiment.POSITIVE}>LogIn</Button>
          <Link href="sign-up">
            <u>{"Don't have an account? - Sign up here"}</u>
          </Link>
        </form>
      </div>
    </PageWithHeader>
  )
}
