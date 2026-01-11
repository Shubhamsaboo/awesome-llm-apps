import { createAuthClient } from "better-auth/react"
import { getBaseUrl } from "./utils"

export const authClient = createAuthClient({
  baseURL: getBaseUrl(),
  redirects: {
    afterSignIn: "/plan",
    afterSignOut: "/auth"
  },
  fetchOptions: {
    credentials: "include"
  }
})