import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '@/layouts/AppShell'
import { AuthLayout } from '@/layouts/AuthLayout'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { CommandCenterPage } from '@/features/command-center/pages/CommandCenterPage'
import { InventoryPage } from '@/features/inventory/pages/InventoryPage'
import { PosPage } from '@/features/pos/pages/PosPage'
import { ReceiveShipmentPage } from '@/features/purchases/pages/ReceiveShipmentPage'
import { CopilotPage } from '@/features/ai-copilot/pages/CopilotPage'
import { RequireAuth } from './RequireAuth'

export const router = createBrowserRouter([
  {
    element: <AuthLayout />,
    children: [{ path: '/login', element: <LoginPage /> }],
  },
  {
    element: <RequireAuth />,
    children: [{
      element: <AppShell />,
      children: [
        { path: '/', element: <CommandCenterPage /> },
        { path: '/inventory', element: <InventoryPage /> },
        { path: '/pos', element: <PosPage /> },
        { path: '/purchases/receive', element: <ReceiveShipmentPage /> },
        { path: '/copilot', element: <CopilotPage /> },
      ],
    }]
  },
])
