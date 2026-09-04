import { createContext, useContext } from "react";
import type { AuthUser } from "@/lib/api/types";

export type AuthContextValue = {
    user: AuthUser | null
    isReady: boolean
    login: (email: string, password: string, keepSignedIn: boolean) => Promise<void>
    logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(){
    const ctx = useContext(AuthContext)

    if (!ctx) {
        throw new Error('useAuth must be used inside AuthProvider')
    }

    return ctx
}
