import type { RecordValueType } from "../CreateComputeBlockModal";
import Input from "./Input";
import Dropdown from "./Dropdown";
import MultiSelectInput from "./MultiSelectInput";

type ConfigEnvsInputsProps = {
  pairs: Record<string, RecordValueType>,
  onUpdate: (key: string, value: RecordValueType) => void,
};

export default function ConfigEnvsInputs({ pairs, onUpdate }: ConfigEnvsInputsProps) {
  function handleChange(key: string, newValue: RecordValueType) {
    onUpdate(key, newValue)
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
      {Object.entries(pairs).map(([key, value]) => (
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
  );
}
