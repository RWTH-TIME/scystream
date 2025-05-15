"use client"

import React, { createContext, useContext, useState, type PropsWithChildren } from "react"
import type { Project } from "@/utils/types"

type SelectedProjectContextType = {
  selectedProject: Project | undefined,
  setSelectedProject: (project: Project | undefined) => void,
}

const initialState: SelectedProjectContextType = {
  selectedProject: undefined,
  setSelectedProject: () => { }
}

const SelectedProjectContext = createContext<SelectedProjectContextType>({
  ...initialState
})

export function SelectedProjectProvider({ children }: PropsWithChildren) {
  const [selectedProject, setSelectedProject] = useState<Project | undefined>(undefined)

  return (
    <SelectedProjectContext.Provider value={{
      selectedProject,
      setSelectedProject
    }}
    >
      {children}
    </SelectedProjectContext.Provider>
  )
}

export const useSelectedProject = () => useContext(SelectedProjectContext)
