import type { ChangeEvent, InputHTMLAttributes } from "react"

type FileInputProps = {
  id?: string,
  label?: string,
  onChange?: (event: ChangeEvent<HTMLInputElement>) => void,
} & Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "value">

export default function FileInput({
  id = "file_input",
  onChange = () => undefined,
  ...rest
}: FileInputProps) {
  return (
    <div className="w-full">
      <input
        id={id}
        type="file"
        onChange={onChange}
        className={
          "block w-full text-sm text-gray-900 placeholder-gray-400 " +
          "border border-gray-300 rounded-md shadow-sm bg-white " +
          "file:bg-transparent file:border-0 file:text-sm file:text-gray-900 " +
          "file:mr-4 file:cursor-pointer py-1.5 px-4 " +
          "file:px-3 file:rounded-l-md file:border-r-1 file:border-gray-300"
        }
        {...rest}
      />
    </div>
  )
}

