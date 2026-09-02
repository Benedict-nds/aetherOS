import type { ReactNode } from "react"
import { AuthProvider } from "./auth"

export const Providers = ({ children }: { children: ReactNode }) => {
  return <AuthProvider>{children}</AuthProvider>
}