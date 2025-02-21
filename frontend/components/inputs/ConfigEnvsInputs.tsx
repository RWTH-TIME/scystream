import { useState } from "react";
import type { RecordValueType } from "../CreateComputeBlockModal";
import Input from "./Input";
import Dropdown from "./Dropdown";
import MultiSelectInput from "./MultiSelectInput"; // Import the new component

type ConfigEnvsInputsProps = {
  pairs: Record<string, RecordValueType>,
};

export default function ConfigEnvsInputs({ pairs }: ConfigEnvsInputsProps) {
  const [values, setValues] = useState<Record<string, RecordValueType>>(
    Object.fromEntries(Object.entries(pairs).map(([key, value]) => [key, value ?? ""]))
  );

  function handleChange(key: string, newValue: RecordValueType) {
    setValues((prev) => ({ ...prev, [key]: newValue }));
  }

  function renderOption(val: boolean) {
    return (
      <div className="flex items-center">
        <span className={`px-3 py-1 text-black text-sm font-medium rounded-lg ${val ? "bg-green-300" : "bg-red-300"}`}>
          {val ? "True" : "False"}
        </span>
      </div>
    );
  }

  function getListTypeLabel(value: string[] | number[] | boolean[]): string {
    if (value.every((item) => typeof item === "string")) return " | string-list";
    if (value.every((item) => typeof item === "number")) return " | number-list";
    if (value.every((item) => typeof item === "boolean")) return " | boolean-list";
    return " | mixed-list";
  }

  return (
    <div>
      {Object.entries(values).map(([key, value]) => (
        <div key={key} className="mb-4">
          <label className="block text-sm font-medium mb-1 text-gray-600">
            {key}
            {Array.isArray(value) ? (
              <span className="text-gray-400">{getListTypeLabel(value)}</span>
            ) : ""}
          </label>
          {typeof value === "boolean" ? (
            <Dropdown
              options={[true, false]}
              selectedValue={value}
              onSelect={(val: boolean) => handleChange(key, val)}
              renderOption={renderOption}
              renderSelected={renderOption}
            />
          ) : Array.isArray(value) ? (
            <MultiSelectInput<string | number | boolean>
              options={value}
              selectedValues={value}
              getValue={(value) => value.toString()}
              onChange={(updatedList) => handleChange(key, updatedList as RecordValueType)}
            />
          ) : (
            <Input
              value={value as string}
              onChange={(text) => handleChange(key, text)}
              type="text"
            />
          )}
        </div>
      ))}
    </div>
  );
}
