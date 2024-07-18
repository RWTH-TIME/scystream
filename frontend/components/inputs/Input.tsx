import type { InputAdornmentProps } from "@mui/material"
import type { ChangeEvent, HTMLInputTypeAttribute, InputHTMLAttributes } from "react"

type InputProps = {
  type: HTMLInputTypeAttribute,
  value: string,
  id?: string,
  label?: string,
  leftAdornment?: React.ReactElement<InputAdornmentProps>,
  rightAdornment?: React.ReactElement<InputAdornmentProps>,
  onChange?: (text: string) => void,
  onChangeEvent?: (event: ChangeEvent<HTMLInputElement>) => void
} & Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "value" | "label" | "onChange">

/**
 * The state of the Input has to be managed by the parent
*/
export default function Input({
  type,
  value,
  id,
  label,
  rightAdornment,
  leftAdornment,
  onChange = () => undefined,
  onChangeEvent = () => undefined,
  ...rest
}: InputProps) {
  return (
    <div>
      {label ?? <label htmlFor={id} className="mb-4 text-sm text-gray-900 font-medium">{label}</label>}
      <div className="relative mt-2 rounded-md shadow-sm">
        {leftAdornment !== undefined ? (<span className="absolute inset-y-0 left-0 flex items-center pl-3">{leftAdornment}</span>) : null}
        <input
          type={type}
          id={id}
          className={"block w-full rounded-md border-0 py-1.5 " + (leftAdornment !== undefined ? "pl-11 " : "pl-5 ") + "pr-20 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400"}
          value={value}
          onChange={
            (e) => {
              onChange(e.target.value)
              onChangeEvent(e)
            }
          }
          {...rest}
        />
        {rightAdornment !== undefined ? (<span className="absolute inset-y-0 right-0 flex items-center pr-3">{rightAdornment}</span>) : null}
      </div>
    </div >
  )
}
