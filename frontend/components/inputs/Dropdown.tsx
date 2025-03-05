import { useState } from "react";

interface DropdownProps<T> {
  options: T[],
  selectedValue: T | undefined,
  onSelect: (value: T) => void,
  renderOption: (option: T) => React.ReactNode,
  renderSelected: (option: T) => React.ReactNode,
  placeholder?: string,
}

export default function Dropdown<T>({
  options,
  selectedValue,
  onSelect,
  renderSelected,
  renderOption,
  placeholder = "Select an option",
}: DropdownProps<T>) {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelectChange = (option: T) => {
    onSelect(option);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <div
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-full p-2 border rounded bg-white cursor-pointer flex justify-between items-center focus:ring-blue-500 focus:border-blue-500"
      >
        <span>
          {selectedValue !== undefined
            ? renderSelected(selectedValue)
            : placeholder}
        </span>
        <span className="text-gray-500 text-xs">▼</span>
      </div>

      {isOpen && (
        <div className="absolute w-full mt-1 bg-white border border-gray-300 rounded shadow-lg z-10">
          {options.map((option, idx) => (
            <div
              key={idx}
              onClick={() => handleSelectChange(option)}
              className="p-2 hover:bg-blue-100 cursor-pointer"
            >
              {renderOption(option)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
