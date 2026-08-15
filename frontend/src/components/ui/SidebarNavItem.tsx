import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

type SidebarNavItemProps = {
  to: string
  label: string
  icon?: ReactNode
}

function navItemClassName({ isActive }: { isActive: boolean }) {
  return isActive ? 'sidebar-nav-item sidebar-nav-item--active' : 'sidebar-nav-item'
}

export const SidebarNavItem = ({ to, label, icon }: SidebarNavItemProps) => {
  return (
    <NavLink to={to} end={true} className={navItemClassName}>
      {icon ? <span className="sidebar-nav-item__icon">{icon}</span> : null}
      <span>{label}</span>
    </NavLink>
  )
}
