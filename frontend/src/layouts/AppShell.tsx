import { Outlet, useNavigate } from 'react-router-dom'
import { Box, ChevronsUpDown, FileBarChart, Inbox, LayoutGrid, LogOut, ShoppingBag, Sparkles } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarNavItem,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui'
import { useAuth } from '@/app/useAuth'

const NAV_ICON_PROPS = { size: 18, strokeWidth: 1.75, 'aria-hidden': true } as const

const NAV_SECTIONS = [
  {
    heading: 'Workspace',
    items: [{ to: '/', label: 'Command Center', icon: <LayoutGrid {...NAV_ICON_PROPS} /> }],
  },
  {
    heading: 'Manage',
    items: [
      { to: '/inventory', label: 'Inventory', icon: <Box {...NAV_ICON_PROPS} /> },
      { to: '/reports', label: 'Reports', icon: <FileBarChart {...NAV_ICON_PROPS} /> },
      { to: '/pos', label: 'Point of Sale', icon: <ShoppingBag {...NAV_ICON_PROPS} /> },
      { to: '/purchases/receive', label: 'Receive Shipment', icon: <Inbox {...NAV_ICON_PROPS} /> },
    ],
  },
  {
    heading: 'Intelligence',
    items: [{ to: '/copilot', label: 'AI Copilot', icon: <Sparkles {...NAV_ICON_PROPS} /> }],
  },
]

function AppSidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <Sidebar>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" className="hover:bg-transparent hover:text-fg">
              <img src="/assets/logo.png" alt="" className="h-6 w-auto object-contain" />
              <div className="grid flex-1 text-left leading-tight">
                <span className="truncate text-h2 font-semibold text-fg">AetherQore</span>
                <span className="truncate text-caption text-muted">Pharmacy OS</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        {NAV_SECTIONS.map((section) => (
          <SidebarGroup key={section.heading}>
            <SidebarGroupLabel>{section.heading}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {section.items.map((item) => (
                  <SidebarNavItem
                    key={item.to}
                    to={item.to}
                    label={item.label}
                    icon={item.icon}
                  />
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton size="lg" className="data-[state=open]:bg-elevated">
                  <div className="size-8 shrink-0 rounded-full bg-elevated" aria-hidden="true" />
                  <div className="grid flex-1 text-left leading-tight">
                    <span className="truncate text-body text-fg">
                      {user?.full_name ?? 'Pharmacy Admin'}
                    </span>
                    <span className="truncate text-caption text-muted">{user?.role ?? 'Owner'}</span>
                  </div>
                  <ChevronsUpDown className="ml-auto size-4 text-muted" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="min-w-56" side="right" align="end" sideOffset={4}>
                <DropdownMenuLabel>
                  <div className="text-body text-fg">{user?.full_name ?? 'Pharmacy Admin'}</div>
                  <div>{user?.email ?? user?.role ?? 'Owner'}</div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onSelect={() => void handleLogout()}>
                  <LogOut className="size-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}

export const AppShell = () => {
  return (
    <SidebarProvider className="h-screen overflow-hidden">
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-12 items-center gap-2 border-b border-subtle px-4 md:hidden">
          <SidebarTrigger />
          <span className="text-h2 font-semibold text-fg">AetherQore</span>
        </header>
        <div className="flex-1 overflow-y-auto">
          <div className="px-8 py-7">
            <Outlet />
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
