type IconProps = {
  className?: string
}

const svgProps = {
  width: 18,
  height: 18,
  viewBox: '0 0 18 18',
  fill: 'currentColor',
  'aria-hidden': true as const,
}

export const IconGrid = ({ className }: IconProps) => (
  <svg {...svgProps} className={className}>
    <rect x="2.25" y="2.25" width="5.25" height="5.25" rx="0.75" />
    <rect x="10.5" y="2.25" width="5.25" height="5.25" rx="0.75" />
    <rect x="2.25" y="10.5" width="5.25" height="5.25" rx="0.75" />
    <rect x="10.5" y="10.5" width="5.25" height="5.25" rx="0.75" />
  </svg>
)

export const IconBox = ({ className }: IconProps) => (
  <svg {...svgProps} className={className}>
    <path d="M9 1.75 15.25 5v8L9 16.25 2.75 13V5L9 1.75Zm0 1.7L4.25 6.1v5.8L9 14.55l4.75-2.65V6.1L9 3.45Z" />
  </svg>
)

export const IconShoppingBag = ({ className }: IconProps) => (
  <svg {...svgProps} className={className}>
    <path d="M5.25 5.5V4.75A3.75 3.75 0 0 1 9 1a3.75 3.75 0 0 1 3.75 3.75V5.5h2.4c.47 0 .85.38.85.85v8.9A1.75 1.75 0 0 1 14.25 17H3.75A1.75 1.75 0 0 1 2 15.25v-8.9c0-.47.38-.85.85-.85h2.4Zm1.5 0h4.5V4.75A2.25 2.25 0 0 0 9 2.5a2.25 2.25 0 0 0-2.25 2.25V5.5Z" />
  </svg>
)

export const IconInboxDownload = ({ className }: IconProps) => (
  <svg {...svgProps} className={className}>
    <path d="M9 2.25a.75.75 0 0 1 .75.75v6.19l1.72-1.72a.75.75 0 1 1 1.06 1.06l-3 3a.75.75 0 0 1-1.06 0l-3-3a.75.75 0 0 1 1.06-1.06l1.72 1.72V3A.75.75 0 0 1 9 2.25Zm-6 8.5h3.1l.97.97a2.25 2.25 0 0 0 3.18 0l.97-.97H15a.75.75 0 0 1 .75.75v3A1.75 1.75 0 0 1 14 16.25H4A1.75 1.75 0 0 1 2.25 14.5v-3a.75.75 0 0 1 .75-.75Z" />
  </svg>
)

export const IconSparkle = ({ className }: IconProps) => (
  <svg {...svgProps} className={className}>
    <path d="M9 1.5 10.4 6.6 15.5 8 10.4 9.4 9 14.5 7.6 9.4 2.5 8l5.1-1.4L9 1.5Z" />
  </svg>
)
