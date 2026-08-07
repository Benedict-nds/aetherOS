import { createBrowserRouter } from "react-router-dom"
import { AppShell } from "../layouts/AppShell"
import { AuthLayout } from "../layouts/AuthLayout"
import { LoginPage } from "../features/auth/pages/LoginPage"
import { CommandCenterPage } from "../features/command-center/pages/CommandCenterPage"

export const router = createBrowserRouter([
    {
        element: <AuthLayout />,
        children: [{ path: '/login', element: <LoginPage /> }],
      },
      {
        element: <AppShell />,
        children: [{ path: '/', element: <CommandCenterPage /> }],
      },
])