import React, { createContext, useContext, useState, type PropsWithChildren } from "react"
import type { ComputeBlock } from "@/components/nodes/ComputeBlockNode"

type SelectedComputeBlockContextType = {
  selectedComputeBlock: ComputeBlock | undefined,
  setSelectedComputeBlock: (computeBlock: ComputeBlock | undefined) => void
}

const initialState: SelectedComputeBlockContextType = {
  selectedComputeBlock: undefined,
  setSelectedComputeBlock: () => { }
}

const SelectedComputeBlockContext = createContext<SelectedComputeBlockContextType>({
  ...initialState
})

export function SelectedComputeBlockProvider({ children }: PropsWithChildren) {
  const [selectedComputeBlock, setSelectedComputeBlock] = useState<ComputeBlock | undefined>(undefined)

  return (
    <SelectedComputeBlockContext.Provider value={{
      selectedComputeBlock,
      setSelectedComputeBlock
    }}
    >
      {children}
    </SelectedComputeBlockContext.Provider>
  )
}

export const useSelectedComputeBlock = () => useContext(SelectedComputeBlockContext)
