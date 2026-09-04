import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { AuthUser } from "@/lib/api/types";
import { getMeRequest, loginRequest, logoutRequest, setOnUnauthorized } from "@/lib/api/client";
import { clearToken, getToken, setToken } from "@/lib/api/auth/token";
import { AuthContext } from "./useAuth";


export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<AuthUser | null>(null)
    const [isReady, setIsReady] = useState(() => !getToken())


    useEffect(() => {
        setOnUnauthorized(() => setUser(null))

        const token = getToken()
        if (!token) {
            return () => setOnUnauthorized(null)
        }

        getMeRequest()
            .then((res) => {
                setUser(res.data)
            })
            .catch(() => { clearToken() }).
            finally(() => {
                setIsReady(true)
            })

        return () => setOnUnauthorized(null)
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