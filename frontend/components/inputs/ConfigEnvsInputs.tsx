import { useState } from "react"
import type { RecordValueType } from "../CreateComputeBlockModal"
import Input from "./Input"
import Dropdown from "./Dropdown"
import MultiSelectInput from "./MultiSelectInput"
import { ConfigBoxVariant } from "../ConfigBox"

type ConfigEnvsInputsProps = {
  pairs: Record<string, RecordValueType>,
  onUpdate: (key: string, value: RecordValueType) => void,
  configVariant?: ConfigBoxVariant,
  borderEnabled?: boolean,
};

export default function ConfigEnvsInputs({
  pairs,
  onUpdate,
  configVariant = ConfigBoxVariant.COMPLEX,
  borderEnabled = true,
}: ConfigEnvsInputsProps) {
  const [expanded, setExpanded] = useState(configVariant === ConfigBoxVariant.SIMPLE ? true : false)

  function handleChange(key: string, newValue: RecordValueType) {
    onUpdate(key, newValue)
  }

  function renderOption(val: boolean) {
    return (
      <div className="flex items-center">
        <span className={`px-3 py-1 text-black text-sm font-medium rounded-lg ${val ? "bg-green-500" : "bg-red-500"}`}>
          {val ? "True" : "False"}
        </span>
      </div>
    )
  }

  function getListTypeLabel(value: string[] | number[] | boolean[]): string {
    if (value.every((item) => typeof item === "string")) return " | string-list"
    if (value.every((item) => typeof item === "number")) return " | number-list"
    if (value.every((item) => typeof item === "boolean")) return " | boolean-list"
    return " | mixed-list"
  }

  return (
    <div className={`${borderEnabled ? "border border-gray-300 shadow-sm" : ""} rounded-lg p-4 `}>
      {
        configVariant === ConfigBoxVariant.COMPLEX ? (
          <div
            className="flex items-center justify-start cursor-pointer py-2 transition-all duration-300 border-gray-200"
            onClick={() => setExpanded(!expanded)}
          >
            <svg
              className={`w-4 h-4 transition-transform duration-300 ${expanded ? "rotate-180" : "rotate-0"}`}
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 3a1 1 0 011 1v12a1 1 0 01-2 0V4a1 1 0 011-1z"
                clipRule="evenodd"
              />
            </svg>
            <span className="ml-2 text-md font-medium">{expanded ? "Hide Configuration" : "Show Configuration"}</span>
          </div>
        ) : null
      }
      <div
        className={`overflow-auto transition-max-height duration-500 ease-in-out ${expanded ? "max-h-screen" : "max-h-0"}`}
      >
        {Object.entries(pairs).map(([key, value]) => (
          <div key={key} className="mb-4">
            <label className="block text-sm font-medium mb-1 text-gray-900">
              {key}
              {Array.isArray(value) ? (
                <span className="text-gray-500">{getListTypeLabel(value)}</span>
              ) : (
                ""
              )}
            </label>
            {typeof value === "boolean" ? (
              <Dropdown
                options={[true, false]}
                selectedValue={value ?? false}
                onSelect={(val: boolean) => handleChange(key, val)}
                renderOption={renderOption}
                renderSelected={renderOption}
              />
            ) : Array.isArray(value) ? (
              <MultiSelectInput<string | number | boolean>
                options={value ?? []}
                selectedValues={value}
                getValue={(value) => value.toString()}
                onChange={(updatedList) => handleChange(key, updatedList as RecordValueType)}
              />
            ) : typeof value === "number" ? (
              <Input
                value={value ?? NaN}
                onChange={(text) => handleChange(key, parseFloat(text))}
                type="number"
                min="0"
              />
            ) : (
              <Input
                value={value ?? ""}
                onChange={(text) => handleChange(key, text)}
                type="text"
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

