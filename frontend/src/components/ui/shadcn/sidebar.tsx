import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { ComponentProps, CSSProperties, ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { PanelLeft } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useIsMobile } from '@/hooks/use-mobile'
import { Button } from './button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './tooltip'

const SIDEBAR_COOKIE_NAME = 'sidebar_state'
const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7
const SIDEBAR_WIDTH = '240px'
const SIDEBAR_WIDTH_ICON = '3rem'
const SIDEBAR_KEYBOARD_SHORTCUT = 'b'

type SidebarContextValue = {
  state: 'expanded' | 'collapsed'
  open: boolean
  setOpen: (open: boolean) => void
  openMobile: boolean
  setOpenMobile: (open: boolean) => void
  isMobile: boolean
  toggleSidebar: () => void
}

const SidebarContext = createContext<SidebarContextValue | null>(null)

export function useSidebar() {
  const context = useContext(SidebarContext)
  if (!context) {
    throw new Error('useSidebar must be used within a SidebarProvider.')
  }
  return context
}

export function SidebarProvider({
  defaultOpen = true,
  open: openProp,
  onOpenChange: setOpenProp,
  className,
  style,
  children,
  ...props
}: ComponentProps<'div'> & {
  defaultOpen?: boolean
  open?: boolean
  onOpenChange?: (open: boolean) => void
}) {
  const isMobile = useIsMobile()
  const [openMobile, setOpenMobile] = useState(false)
  const [_open, _setOpen] = useState(() => {
    if (typeof document === 'undefined') return defaultOpen
    const match = document.cookie.match(new RegExp(`(?:^|; )${SIDEBAR_COOKIE_NAME}=([^;]*)`))
    if (match) return match[1] === 'true'
    return defaultOpen
  })
  const open = openProp ?? _open

  const setOpen = useCallback(
    (value: boolean | ((value: boolean) => boolean)) => {
      const openState = typeof value === 'function' ? value(open) : value
      if (setOpenProp) {
        setOpenProp(openState)
      } else {
        _setOpen(openState)
      }
      document.cookie = `${SIDEBAR_COOKIE_NAME}=${openState}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`
    },
    [setOpenProp, open],
  )

  const toggleSidebar = useCallback(() => {
    return isMobile ? setOpenMobile((current) => !current) : setOpen((current) => !current)
  }, [isMobile, setOpen])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === SIDEBAR_KEYBOARD_SHORTCUT && (event.metaKey || event.ctrlKey)) {
        event.preventDefault()
        toggleSidebar()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [toggleSidebar])

  const state = open ? 'expanded' : 'collapsed'

  const contextValue = useMemo<SidebarContextValue>(
    () => ({
      state,
      open,
      setOpen,
      isMobile,
      openMobile,
      setOpenMobile,
      toggleSidebar,
    }),
    [state, open, setOpen, isMobile, openMobile, toggleSidebar],
  )

  return (
    <SidebarContext.Provider value={contextValue}>
      <TooltipProvider delayDuration={0}>
        <div
          data-slot="sidebar-wrapper"
          style={
            {
              '--sidebar-width': SIDEBAR_WIDTH,
              '--sidebar-width-icon': SIDEBAR_WIDTH_ICON,
              ...style,
            } as CSSProperties
          }
          className={cn('group/sidebar-wrapper flex min-h-svh w-full bg-base text-fg', className)}
          {...props}
        >
          {children}
        </div>
      </TooltipProvider>
    </SidebarContext.Provider>
  )
}

export function Sidebar({
  side = 'left',
  variant = 'sidebar',
  collapsible = 'offcanvas',
  className,
  children,
  ...props
}: ComponentProps<'div'> & {
  side?: 'left' | 'right'
  variant?: 'sidebar' | 'floating' | 'inset'
  collapsible?: 'offcanvas' | 'icon' | 'none'
}) {
  const { isMobile, state, openMobile, setOpenMobile } = useSidebar()

  if (collapsible === 'none') {
    return (
      <div
        data-slot="sidebar"
        className={cn(
          'flex w-sidebar shrink-0 flex-col border-r border-subtle bg-surface',
          className,
        )}
        {...props}
      >
        {children}
      </div>
    )
  }

  if (isMobile) {
    return (
      <>
        {openMobile ? (
          <button
            type="button"
            aria-label="Close sidebar"
            className="fixed inset-0 z-40 bg-base/80 duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 md:hidden"
            onClick={() => setOpenMobile(false)}
          />
        ) : null}
        <div
          data-slot="sidebar"
          data-mobile="true"
          data-state={openMobile ? 'expanded' : 'collapsed'}
          className={cn(
            'fixed inset-y-0 z-50 flex w-sidebar flex-col border-r border-subtle bg-surface duration-200 md:hidden',
            'data-[state=open]:animate-in data-[state=closed]:animate-out',
            side === 'left' ? 'left-0' : 'right-0',
            openMobile
              ? 'translate-x-0'
              : side === 'left'
                ? '-translate-x-full'
                : 'translate-x-full',
            className,
          )}
          {...props}
        >
          {children}
        </div>
      </>
    )
  }

  return (
    <div
      data-slot="sidebar"
      data-state={state}
      data-collapsible={state === 'collapsed' ? collapsible : ''}
      data-variant={variant}
      data-side={side}
      className={cn(
        'group/sidebar relative hidden shrink-0 flex-col border-r border-subtle bg-surface transition-[width] duration-200 ease-linear md:flex',
        state === 'collapsed' && collapsible === 'offcanvas' && 'w-0 overflow-hidden border-0',
        state === 'collapsed' && collapsible === 'icon' ? 'w-sidebar-icon' : 'w-sidebar',
        className,
      )}
      {...props}
    >
      {children}
      <SidebarRail />
    </div>
  )
}

export function SidebarTrigger({
  className,
  onClick,
  ...props
}: ComponentProps<typeof Button>) {
  const { toggleSidebar } = useSidebar()

  return (
    <Button
      data-slot="sidebar-trigger"
      variant="ghost"
      className={cn('size-9 shrink-0 px-0 py-0', className)}
      onClick={(event) => {
        onClick?.(event)
        toggleSidebar()
      }}
      {...props}
    >
      <PanelLeft className="size-4" />
      <span className="sr-only">Toggle Sidebar</span>
    </Button>
  )
}

export function SidebarRail({ className, ...props }: ComponentProps<'button'>) {
  const { toggleSidebar } = useSidebar()

  return (
    <button
      type="button"
      data-slot="sidebar-rail"
      aria-label="Toggle Sidebar"
      tabIndex={-1}
      onClick={toggleSidebar}
      className={cn(
        'absolute inset-y-0 -right-2 z-20 hidden w-4 cursor-w-resize sm:flex',
        'after:absolute after:inset-y-0 after:left-1/2 after:w-px hover:after:bg-subtle',
        className,
      )}
      {...props}
    />
  )
}

export function SidebarInset({ className, ...props }: ComponentProps<'main'>) {
  return (
    <main
      data-slot="sidebar-inset"
      className={cn('relative flex min-w-0 flex-1 flex-col overflow-hidden bg-base', className)}
      {...props}
    />
  )
}

export function SidebarHeader({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="sidebar-header"
      className={cn(
        'flex flex-col gap-2 px-4 pt-5 group-data-[collapsible=icon]/sidebar:px-2',
        className,
      )}
      {...props}
    />
  )
}

export function SidebarFooter({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="sidebar-footer"
      className={cn(
        'mt-auto flex flex-col gap-2 px-4 pb-5 group-data-[collapsible=icon]/sidebar:px-2',
        className,
      )}
      {...props}
    />
  )
}

export function SidebarContent({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="sidebar-content"
      className={cn(
        'flex min-h-0 flex-1 flex-col gap-6 overflow-x-hidden overflow-y-auto px-4 py-5 group-data-[collapsible=icon]/sidebar:overflow-hidden group-data-[collapsible=icon]/sidebar:px-2',
        className,
      )}
      {...props}
    />
  )
}

export function SidebarGroup({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div
      data-slot="sidebar-group"
      className={cn('relative flex w-full min-w-0 flex-col', className)}
      {...props}
    />
  )
}

export function SidebarGroupLabel({
  className,
  asChild = false,
  ...props
}: ComponentProps<'div'> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : 'div'
  return (
    <Comp
      data-slot="sidebar-group-label"
      className={cn(
        'px-3.5 pb-1.5 text-caption font-normal tracking-wider text-muted uppercase',
        'group-data-[collapsible=icon]/sidebar:hidden',
        className,
      )}
      {...props}
    />
  )
}

export function SidebarGroupContent({ className, ...props }: ComponentProps<'div'>) {
  return <div data-slot="sidebar-group-content" className={cn('w-full', className)} {...props} />
}

export function SidebarMenu({ className, ...props }: ComponentProps<'ul'>) {
  return (
    <ul
      data-slot="sidebar-menu"
      className={cn('flex w-full min-w-0 flex-col gap-1', className)}
      {...props}
    />
  )
}

export function SidebarMenuItem({ className, ...props }: ComponentProps<'li'>) {
  return (
    <li
      data-slot="sidebar-menu-item"
      className={cn('group/menu-item relative', className)}
      {...props}
    />
  )
}

const sidebarMenuButtonVariants = cva(
  'flex w-full min-h-10 items-center gap-2.5 overflow-hidden rounded-lg px-3.5 py-2.5 text-left text-body outline-none focus-visible:outline-2 focus-visible:outline-accent disabled:pointer-events-none disabled:opacity-50 group-data-[collapsible=icon]/sidebar:size-8 group-data-[collapsible=icon]/sidebar:min-h-8 group-data-[collapsible=icon]/sidebar:justify-center group-data-[collapsible=icon]/sidebar:p-2 [&>span:last-child]:truncate group-data-[collapsible=icon]/sidebar:[&>span]:hidden [&>svg]:size-[18px] [&>svg]:shrink-0',
  {
    variants: {
      variant: {
        default: 'bg-transparent text-muted hover:bg-elevated hover:text-fg',
        outline: 'border border-subtle bg-transparent text-muted hover:bg-elevated hover:text-fg',
      },
      size: {
        default: 'min-h-10',
        sm: 'min-h-8 px-2.5 py-1.5',
        lg: 'min-h-12 group-data-[collapsible=icon]/sidebar:size-8 group-data-[collapsible=icon]/sidebar:min-h-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export function SidebarMenuButton({
  asChild = false,
  isActive = false,
  variant = 'default',
  size = 'default',
  tooltip,
  className,
  ...props
}: ComponentProps<'button'> & {
  asChild?: boolean
  isActive?: boolean
  tooltip?: string | ComponentProps<typeof TooltipContent>
} & VariantProps<typeof sidebarMenuButtonVariants>) {
  const Comp = asChild ? Slot : 'button'
  const { isMobile, state } = useSidebar()

  const button = (
    <Comp
      data-slot="sidebar-menu-button"
      data-active={isActive}
      {...(!asChild ? { type: 'button' as const } : {})}
      className={cn(
        sidebarMenuButtonVariants({ variant, size }),
        isActive && 'bg-elevated text-fg [&_svg]:text-accent',
        className,
      )}
      {...props}
    />
  )

  if (!tooltip) return button

  const tooltipProps = typeof tooltip === 'string' ? { children: tooltip } : tooltip

  return (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent
        side="right"
        align="center"
        hidden={state !== 'collapsed' || isMobile}
        {...tooltipProps}
      />
    </Tooltip>
  )
}

type SidebarNavItemProps = {
  to: string
  label: string
  icon?: ReactNode
}

export function SidebarNavItem({ to, label, icon }: SidebarNavItemProps) {
  const { isMobile, setOpenMobile } = useSidebar()

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild tooltip={label}>
        <NavLink
          to={to}
          end
          onClick={() => {
            if (isMobile) setOpenMobile(false)
          }}
          className={({ isActive }) =>
            cn(isActive && 'bg-elevated text-fg [&_svg]:text-accent')
          }
        >
          {icon}
          <span>{label}</span>
        </NavLink>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}
