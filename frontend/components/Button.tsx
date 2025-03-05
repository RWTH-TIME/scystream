import type { ButtonHTMLAttributes, MouseEventHandler, PropsWithChildren } from "react";

export enum ButtonSentiment {
  POSITIVE,
  NEGATIVE,
  NEUTRAL
}

type ButtonProps = PropsWithChildren<{
  className?: string,
  onClick?: MouseEventHandler<HTMLButtonElement>,
  sentiment?: ButtonSentiment,
}> &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, "onClick" | "className">;

export default function Button({
  children,
  className = "",
  disabled = false,
  onClick,
  sentiment = ButtonSentiment.NEUTRAL,
  ...rest
}: ButtonProps) {
  // Define styles based on sentiment
  let sentimentStyles = "";
  if (sentiment === ButtonSentiment.POSITIVE) {
    sentimentStyles = "bg-blue-500 hover:bg-blue-600 text-white";
  } else if (sentiment === ButtonSentiment.NEGATIVE) {
    sentimentStyles = "bg-red-500 hover:bg-red-600 text-white";
  } else {
    sentimentStyles = "bg-gray-200 hover:bg-gray-300 text-gray-500";
  }

  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      {...rest}
      className={`px-4 py-2 rounded-md shadow-xs transition-all ${disabled ? "opacity-50 cursor-not-allowed" : `hover:cursor-pointer ${sentimentStyles}`
        } ${className}`}
    >
      {children}
    </button>
  );
}

