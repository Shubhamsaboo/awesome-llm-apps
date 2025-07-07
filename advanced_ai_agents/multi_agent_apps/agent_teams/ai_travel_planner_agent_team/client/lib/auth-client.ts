import { createAuthClient } from "better-auth/react"

export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_BASE_URL || "",
  redirects: {
    afterSignIn: "/plan",
    afterSignOut: "/auth"
  },
  fetchOptions: {
    credentials: "include"
  }
})