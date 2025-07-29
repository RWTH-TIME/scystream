import { useState } from "react"

interface DropdownProps<T> {
  options: T[],
  selectedValue: T | undefined,
  onSelect: (value: T) => void,
  renderOption: (option: T) => React.ReactNode,
  renderSelected: (option: T) => React.ReactNode,
  placeholder?: string,
  disabled?: boolean,
}

export default function Dropdown<T>({
  options,
  selectedValue,
  onSelect,
  renderSelected,
  renderOption,
  placeholder = "Select an option",
  disabled = false,
}: DropdownProps<T>) {
  const [isOpen, setIsOpen] = useState(false)

  const handleSelectChange = (option: T) => {
    if (disabled) return
    onSelect(option)
    setIsOpen(false)
  }

  const toggleOpen = () => {
    if (disabled) return
    setIsOpen(prev => !prev)
  }

  return (
    <div className="relative">
      <div
        onClick={toggleOpen}
        className={`
          w-full p-2 border rounded bg-white flex justify-between items-center
          ${disabled
            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
            : "cursor-pointer focus:ring-blue-500 focus:border-blue-500"
          }
        `}
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
      >
        <span>
          {selectedValue !== undefined
            ? renderSelected(selectedValue)
            : placeholder}
        </span>
        <span className={`text-gray-500 text-xs ${disabled ? "opacity-50" : ""}`}>▼</span>
      </div>

      {isOpen && !disabled && (
        <div className="absolute w-full mt-1 bg-white border border-gray-300 rounded shadow-lg z-10 max-h-60 overflow-auto">
          {options.map((option, idx) => (
            <div
              key={idx}
              onClick={() => handleSelectChange(option)}
              className="p-2 hover:bg-blue-100 cursor-pointer"
              role="option"
            >
              {renderOption(option)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
};
