import { Outlet, NavLink } from "react-router-dom"

export const AppShell = () => {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-base)', color: 'var(--text-primary)' }}>
    <aside style={{ width: 240, background: 'var(--bg-surface)', borderRight: '1px solid var(--border-subtle)' }}>
      <div>AetherQore</div>
      <nav>
        <NavLink to="/">Command Center</NavLink>
        {/* Inventory, POS, Receive Shipment — add as routes exist */}
      </nav>
    </aside>
    <div style={{ flex: 1 }}>
      <header style={{ borderBottom: '1px solid var(--border-subtle)' }}>Top bar</header>
      <main><Outlet /></main>
    </div>
  </div>
  )
}