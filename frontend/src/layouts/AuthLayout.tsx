import { Outlet } from "react-router-dom"

export const AuthLayout = () => {
  return (
    <div className="min-h-screen bg-base text-fg">
      <Outlet />
    </div>
  )
}