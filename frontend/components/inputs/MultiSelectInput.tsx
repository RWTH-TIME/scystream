import { useState } from "react";
import { TextField, Chip, Autocomplete } from "@mui/material";

interface MultiSelectInputProps<T extends string | number | boolean> {
  options: T[],
  selectedValues: T[],
  onChange: (values: T[]) => void,
  getValue: (option: string | T) => string,
  placeholder?: string,
}

export default function MultiSelectInput<T extends string | number | boolean>({
  options,
  selectedValues,
  onChange,
  getValue,
}: MultiSelectInputProps<T>) {
  const [inputValue, setInputValue] = useState("");

  function isValidValue(value: string): boolean {
    if (typeof selectedValues[0] === "boolean") {
      return value.toLowerCase() === "true" || value.toLowerCase() === "false";
    }
    if (typeof selectedValues[0] === "number") {
      return !isNaN(Number(value));
    }
    return true; // Allow anything for string[]
  }

  function handleChange(_: React.SyntheticEvent, newValue: (string | T)[]) {
    const filteredValues = newValue.filter((val) =>
      isValidValue(typeof val === "string" ? val : getValue(val))
    );

    const convertedValues = filteredValues.map((val) => {
      if (typeof selectedValues[0] === "boolean") {
        return (val.toString().toLowerCase() === "true") as T;
      }
      if (typeof selectedValues[0] === "number") {
        return Number(val) as T;
      }
      return val as T;
    });

    onChange(convertedValues);
  }

  return (
    <Autocomplete
      multiple
      freeSolo
      options={options}
      getOptionLabel={getValue}
      value={selectedValues}
      onChange={handleChange}
      inputValue={inputValue}
      isOptionEqualToValue={() => false}
      onInputChange={(_, newInputValue) => setInputValue(newInputValue)}
      renderTags={(value) =>
        value.map((option, idx) => {
          return <Chip key={idx} label={getValue(option)} />;
        })
      }
      renderOption={(props, option, { index }) => (
        <li
          {...props}
          key={`${getValue(option)}-${index}`}
          className="flex items-center px-3 py-2 hover:bg-blue-100 rounded-lg cursor-pointer transition"
        >
          <span className="text-gray-800 font-medium">{getValue(option)}</span>
        </li>
      )}
      renderInput={(params) => <TextField {...params} placeholder="Add values" />}
    />
  );
}

