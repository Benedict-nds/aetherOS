import { Outlet } from 'react-router-dom'
import { Box, Inbox, LayoutGrid, ShoppingBag, Sparkles } from 'lucide-react'
import { SidebarNavItem } from '@/components/ui'


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

export const AppShell = () => {
  return (
    <div className="flex min-h-screen bg-base text-fg">
      <aside className="flex w-sidebar shrink-0 flex-col justify-between border-r border-subtle bg-surface px-4 py-5">
        <div className="flex flex-col gap-7">
          <div className="flex items-center gap-2 px-1">
            <img src="/assets/logo.png" alt="" className='h-6 w-auto object-contain'/>
            <span className="text-h2 font-semibold text-fg">AetherQore</span>
          </div>
          <nav className="flex flex-col gap-6">
            {NAV_SECTIONS.map((section) => (
              <div key={section.heading} className="flex flex-col gap-1">
                <div className="px-3.5 pb-1.5 text-caption font-normal tracking-wider text-muted uppercase">{section.heading}</div>
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
        <div className="flex items-center gap-2.5 py-2 pr-2 pl-1">
          <div className="size-9 shrink-0 rounded-full bg-elevated" aria-hidden="true" />
          <div>
            <div className="text-body text-fg">Pharmacy Admin</div>
            <div className="text-caption text-muted">Owner</div>
          </div>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="flex-1 px-8 py-7">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

