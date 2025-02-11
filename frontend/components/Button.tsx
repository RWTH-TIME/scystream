import type { ButtonHTMLAttributes, MouseEventHandler, PropsWithChildren } from "react"

type ButtonProps = PropsWithChildren<{
  className?: string,
  onClick?: MouseEventHandler<HTMLButtonElement>,
}> & Omit<ButtonHTMLAttributes<Element>, "onClick" | "className">

export default function Button({
  children,
  className = undefined,
  disabled = false,
  onClick,
  ...rest
}: ButtonProps) {
  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      {...rest}
      className={className + " border p-1 rounded-md shadow-sm bg-white"}
    >
      {children}
    </button>
  )
}
