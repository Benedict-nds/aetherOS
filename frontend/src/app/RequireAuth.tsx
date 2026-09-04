import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./useAuth";


export const RequireAuth = () =>{
    const {user, isReady} = useAuth()

    if (!isReady) return null
    if (!user) return <Navigate to="/login" replace/>

    return <Outlet />
}