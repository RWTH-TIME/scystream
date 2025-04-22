"use client"

import Link from "next/link"
import { useState } from "react"
import Button, { ButtonSentiment } from "@/components/Button"
import Input from "@/components/inputs/Input"
import InputAdornment from "@/components/inputs/InputAdornment"
import PageWithHeader from "@/components/layout/PageWithHeader"
import { useRegisterMutation } from "@/mutations/userMutation"
import { AlertType, useAlert } from "@/hooks/useAlert"

const PASSWORD_MIN_LEN = 8
const PASSWORD_VALIDATION = (password: string) => {
  if (password.length < PASSWORD_MIN_LEN) {
    throw new Error("Password must be at least 8 characters long")
  }
  if (!/[0-9]/.test(password)) {
    throw new Error("Password must contain a number")
  }
  if (!/[A-Z]/.test(password)) {
    throw new Error("Password must contain a capital letter")
  }
  if (!/[a-z]/.test(password)) {
    throw new Error("Password must contain a lowercase letter")
  }
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    throw new Error("Password must contain at least one special character")
  }
  return password
}


export default function Register() {
  const { setAlert } = useAlert()
  const [mail, setMail] = useState<string>("")
  const [password, setPassword] = useState<string>("")
  const [passwordRep, setPasswordRep] = useState<string>("")

  const [showPass, setShowPass] = useState<boolean>(false)

  const { mutate } = useRegisterMutation(setAlert)

  function signUp(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (mail.length === 0) {
      setAlert("Enter your E-Mail address", AlertType.ERROR)
      return
    }
    if (password !== passwordRep) {
      setAlert("Passwords must match", AlertType.ERROR)
      return
    }

    try {
      PASSWORD_VALIDATION(password)
    } catch (error: unknown) {
      if (error instanceof Error)
        setAlert(error.message, AlertType.ERROR)
      return
    }

    mutate({ email: mail, password })
  }


  return (
    <PageWithHeader breadcrumbs={[{ text: "Signup", link: "/sign-up" }]}>
      <form onSubmit={(e) => signUp(e)} className="w-1/2 bg-slate-50 m-auto p-10 min-h-96 rounded-lg flex flex-col gap-5 drop-shadow-sm justify-center">
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
        <Button sentiment={ButtonSentiment.POSITIVE} type="submit">Create Account</Button>
        <Link href="login"><u>Already have an account? - Login here</u></Link>
      </form>
    </PageWithHeader>
  )
}
