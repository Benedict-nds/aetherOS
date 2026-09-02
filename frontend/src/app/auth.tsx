import { Children, createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { AuthUser } from "@/lib/api/types";
import { getMeRequest, loginRequest, logoutRequest } from "@/lib/api/client";
import { clearToken, getToken, setToken } from "@/lib/api/auth/token";

type AuthContextValue = {
    user: AuthUser | null
    isReady: boolean
    login: (email: string, password: string, keepSignedIn: boolean) => Promise<void>
    logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)


export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<AuthUser | null>(null)
    const [isReady, setIsReady] = useState(false)


    useEffect(() => {
        const token = getToken()
        if (!token) {
            setIsReady(true)
            return
        }

        getMeRequest()
            .then((res) => {
                setUser(res.data)
            })
            .catch(() => { clearToken() }).
            finally(() => {
                setIsReady(true)
            })
    }, [])

    const login = async (email: string, password: string, keepSignedIn: boolean) => {
        const res = await loginRequest(email, password)
        if (!res.data) {
            throw new Error(res.message || "Invalid credentials")
        }
        setToken(res.data.access_token, keepSignedIn)
        setUser(res.data.user)
    }


    const logout = async () => {
        try {
            await logoutRequest()
        } catch {
            // Token may already be invalid; still clear local session.
        } finally {
            clearToken()
            setUser(null)
        }
    }

    const value = useMemo(
        () => ({user, isReady, login, logout}),
        [user,isReady]
    )

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}



export function useAuth(){
    const ctx = useContext(AuthContext)

    if (!ctx) {
        throw new Error('useAuth must be used inside AuthProvider')
    }

    return ctx
}