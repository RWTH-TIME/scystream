import type { PropsWithChildren } from "react"
import { Close } from "@mui/icons-material"

export type ModalProps = PropsWithChildren<{
  className?: string,
  onClose: () => void,
  isOpen: boolean,
}>;

export default function Modal({
  children,
  className = "",
  onClose,
  isOpen,
}: ModalProps) {
  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center transition-opacity ${isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
    >
      <div
        className={`fixed inset-0 bg-black/50 transition-opacity ${isOpen ? "opacity-100" : "opacity-0"
          }`}
        onClick={onClose}
      />

      <div
        className={`relative bg-white max-h-[90vh] overflow-y-auto rounded-lg shadow-xl max-w-3/4 w-full p-6 transition-transform transform ${isOpen ? "scale-100" : "scale-95"
          } ${className}`}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
        >
          <Close fontSize="medium" />
        </button>
        {children}
      </div>
    </div>
  )
}

