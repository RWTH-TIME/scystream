import { useMutation } from "@tanstack/react-query"

type User = {
  email: string,
  password: string
}

export function useRegisterMutation() {
  return useMutation({
    mutationFn: async function login(user: User) {
      console.log("user")
    }
  })
}
