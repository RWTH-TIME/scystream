import React from "react"

import VisibilityIcon from "@mui/icons-material/Visibility"
import EmailIcon from "@mui/icons-material/Email"
import LockIcon from "@mui/icons-material/Lock"
import { VisibilityOff } from "@mui/icons-material"

/**
 * This component can be passed to the Input Component as leading or trailing icon
 */

type InputAdornmentIconTypes = "email" | "password" | "visibility" | "visibilityOff"

export type InputAdornmentProps = {
  type: InputAdornmentIconTypes,
  onClick?: () => void,
}

function renderIcon(iconType: InputAdornmentIconTypes) {
  switch (iconType) {
    case "visibility":
      return <VisibilityIcon />
    case "visibilityOff":
      return <VisibilityOff />
    case "email":
      return <EmailIcon />
    case "password":
      return <LockIcon />
    default:
      return iconType
  }
}

export default function InputAdornment({
  type,
  onClick = () => undefined
}: InputAdornmentProps) {
  return (
    <div className="text-slate-700" onClick={() => onClick()}>
      {renderIcon(type)}
    </div>
  )
}
