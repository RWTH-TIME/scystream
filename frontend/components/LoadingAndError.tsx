import type { PropsWithChildren } from "react"
import { CircularProgress } from "@mui/material"

export type LoadingAndErrorProps = PropsWithChildren<{
  loading?: boolean,
  error?: boolean,
  iconSize?: number,
}>

export default function LoadingAndError({ loading = false, error = false, iconSize = undefined, children }: LoadingAndErrorProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center">
        <CircularProgress size={iconSize} />
      </div>
    )
  }
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-full p-4 bg-red-100 rounded-lg">
        <svg className="w-16 h-16 mb-4 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
        <h2 className="text-2xl font-bold text-red-600">Something went wrong</h2>
        <p className="text-red-600 mt-2">{"We're having trouble processing your request. Please try again later."}</p>
      </div>
    )
  }
  return children
}
