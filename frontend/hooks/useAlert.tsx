"use client"

import type { PropsWithChildren } from "react"
import { createContext, useContext, useState } from "react"

// in ms
const ALERT_TIME = 5000

export enum AlertType {
  SUCCESS = 1,
  ERROR = 2,
  DEFAULT = 3
}

export type SetAlertType = (text: string, type: AlertType) => void

type AlertContextValues = {
  text: string,
  type: AlertType,
  setAlert: SetAlertType,
}

const initialState: AlertContextValues = {
  text: "",
  type: AlertType.DEFAULT,
  setAlert: () => { console.log("empty setAlert") }
}

const AlertContext = createContext<AlertContextValues>({
  ...initialState
})

export const useAlert = () => useContext(AlertContext)

export function AlertProvider({ children }: PropsWithChildren) {
  const [text, setText] = useState<string>("")
  const [type, setType] = useState<AlertType>(AlertType.DEFAULT)

  const setAlert: SetAlertType = (text: string, type: AlertType) => {
    setText(text)
    setType(type)
    setTimeout(() => {
      setText("")
      setType(AlertType.DEFAULT)
    }, ALERT_TIME)
  }

  return (
    <AlertContext.Provider
      value={{
        text,
        type,
        setAlert
      }}
    >
      {children}
    </AlertContext.Provider>
  )
}

export default AlertContext
