import { useMutation } from "@tanstack/react-query"

export function useRegisterMutation() {
  return useMutation({
    mutationFn: async function login() {
      console.log("user")
    }
  })
}
