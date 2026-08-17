import { Outlet, useLocation } from 'react-router-dom'
import { Box, Inbox, LayoutGrid, ShoppingBag, Sparkles } from 'lucide-react'
import { SidebarNavItem } from '@/components/ui'
import './AppShell.css'

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
      { to: '/pos', label: 'Point of Sale', icon: <ShoppingBag {...NAV_ICON_PROPS} /> },
      { to: '/purchases/receive', label: 'Receive Shipment', icon: <Inbox {...NAV_ICON_PROPS} /> },
    ],
  },
  {
    heading: 'Intelligence',
    items: [{ to: '/copilot', label: 'AI Copilot', icon: <Sparkles {...NAV_ICON_PROPS} /> }],
  },
]

const PAGE_TITLES: Record<string, string> = {
  '/': 'Command Center',
  '/inventory': 'Inventory',
  '/pos': 'Point of Sale',
  '/purchases/receive': 'Receive Shipment',
  '/copilot': 'AI Copilot',
}

export const AppShell = () => {
  const { pathname } = useLocation()
  const title = PAGE_TITLES[pathname] ?? 'AetherQore'

  return (
    <div className="app-shell">
      <aside className="app-shell__sidebar">
        <div className="app-shell__sidebar-top">
          <div className="app-shell__wordmark">
            <img src="/assets/logo.png" alt="" />
            <span>AetherQore</span>
          </div>
          <nav className="app-shell__nav">
            {NAV_SECTIONS.map((section) => (
              <div key={section.heading} className="app-shell__section">
                <div className="app-shell__section-label">{section.heading}</div>
                {section.items.map((item) => (
                  <SidebarNavItem
                    key={item.to}
                    to={item.to}
                    label={item.label}
                    icon={item.icon}
                  />
                ))}
              </div>
            ))}
          </nav>
        </div>
        <div className="app-shell__profile">
          <div className="app-shell__avatar" aria-hidden="true" />
          <div>
            <div className="app-shell__profile-name">Pharmacy Admin</div>
            <div className="app-shell__profile-role">Owner</div>
          </div>
        </div>
      </aside>
      <div className="app-shell__body">
        <header className="app-shell__topbar">
          <h1>{title}</h1>
        </header>
        <main className="app-shell__content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
