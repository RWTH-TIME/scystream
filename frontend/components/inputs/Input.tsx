import { ChangeEvent, HTMLInputTypeAttribute, InputHTMLAttributes } from "react"

type InputProps = {
  type: HTMLInputTypeAttribute,
  value: string,
  id?: string
  label?: string,
  onChange?: (text: string) => void
  onChangeEvent?: (event: ChangeEvent<HTMLInputElement>) => void,
} & Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "value" | "label" | "onChange">

/**
 * The state of the Input has to be managed by the parent
*/
export default function Input({
  type,
  value,
  id,
  label,
  onChange = () => undefined,
  onChangeEvent = () => undefined,
  ...rest
}: InputProps) {
  return (
    <div>
      {label ?? <label htmlFor={id} className="mb-4 text-sm text-gray-900 font-medium">{label}</label>}
      <input
        id={id}
        className="border w-full border-gray-300 text-sm rounded-lg block p-2.5"
        type={type}
        value={value}
        onChange={
          (e) => {
            onChange(e.target.value)
            onChangeEvent(e)
          }
        }
        {...rest} />
    </div>
  )
}
