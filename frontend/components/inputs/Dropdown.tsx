import { useState } from "react";

interface DropdownProps<T> {
  options: T[],
  selectedValue: string | undefined,
  onSelect: (value: T) => void,
  renderOption: (option: T) => React.ReactNode, // Function to render each option
  getValue: (option: T) => string, // Function to extract value from each option
  placeholder?: string,
}

export default function Dropdown<T>({
  options,
  selectedValue,
  onSelect,
  renderOption,
  getValue,
  placeholder = "Select an option",
}: DropdownProps<T>) {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelectChange = (option: T) => {
    onSelect(option);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      {/* Custom Dropdown */}
      <div
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-full p-2 border rounded bg-white cursor-pointer flex justify-between items-center focus:ring-blue-500 focus:border-blue-500"
      >
        <span>{selectedValue || placeholder}</span>
        <span className="text-gray-500 text-xs">▼</span>
      </div>

      {/* Dropdown Options */}
      {isOpen && (
        <div className="absolute w-full mt-1 bg-white border border-gray-300 rounded shadow-lg z-10">
          {options.map((option) => (
            <div
              key={getValue(option)}
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
