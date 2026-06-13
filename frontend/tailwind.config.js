/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        /* 基础语义 token */
        'bg-app': 'var(--color-bg-app)',
        'bg-canvas': 'var(--color-bg-canvas)',
        surface: {
          DEFAULT: 'var(--color-surface)',
          muted: 'var(--color-surface-muted)',
          alt: 'var(--color-surface-alt)',
          strong: 'var(--color-surface-strong)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          soft: 'var(--color-border-soft)',
          strong: 'var(--color-border-strong)',
        },
        text: {
          DEFAULT: 'var(--color-text)',
          secondary: 'var(--color-text-secondary)',
          tertiary: 'var(--color-text-tertiary)',
          muted: 'var(--color-text-muted)',
          warm: 'var(--color-text-warm)',
        },
        /* 操作颜色 */
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          active: 'var(--color-primary-active)',
        },
        link: {
          DEFAULT: 'var(--color-link)',
          hover: 'var(--color-link-hover)',
        },
        focus: 'var(--color-focus-ring)',
        /* 语义颜色 */
        success: {
          DEFAULT: 'var(--color-success)',
          bg: 'var(--color-success-bg)',
        },
        warning: {
          DEFAULT: 'var(--color-warning)',
          bg: 'var(--color-warning-bg)',
        },
        danger: {
          DEFAULT: 'var(--color-danger)',
          bg: 'var(--color-danger-bg)',
        },
        info: {
          DEFAULT: 'var(--color-info)',
          bg: 'var(--color-info-bg)',
        },
        /* overlay */
        overlay: {
          manual: 'var(--overlay-manual)',
          candidate: 'var(--overlay-candidate)',
          selected: 'var(--overlay-selected)',
          'qc-error': 'var(--overlay-qc-error)',
          'qc-warning': 'var(--overlay-qc-warning)',
          relation: 'var(--overlay-relation)',
        },
        /* 兼容旧名 */
        background: 'var(--color-background)',
        accent: 'var(--color-accent)',
        muted: 'var(--color-muted)',
      },
      fontFamily: {
        sans: ['Inter', 'Geist', 'IBM Plex Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Geist Mono', 'ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      fontSize: {
        'display': ['32px', { lineHeight: '1.25', fontWeight: '600' }],
        'title': ['24px', { lineHeight: '1.30', fontWeight: '600' }],
        'heading': ['20px', { lineHeight: '1.35', fontWeight: '600' }],
        'subheading': ['16px', { lineHeight: '1.45', fontWeight: '600' }],
        'body': ['14px', { lineHeight: '1.50', fontWeight: '400' }],
        'body-medium': ['14px', { lineHeight: '1.50', fontWeight: '500' }],
        'caption': ['12px', { lineHeight: '1.40', fontWeight: '400' }],
        'micro': ['11px', { lineHeight: '1.30', fontWeight: '500' }],
        'mono': ['12px', { lineHeight: '1.45', fontWeight: '400' }],
      },
      borderRadius: {
        'none': '0px',
        'xs': '2px',
        'sm': '4px',
        'md': '6px',
        'lg': '8px',
        'pill': '9999px',
      },
      boxShadow: {
        'popover': '0 8px 24px rgba(15, 15, 15, 0.12)',
        'modal': '0 16px 48px rgba(15, 15, 15, 0.16)',
      },
      spacing: {
        /* 4px grid 扩展，不覆盖默认 Tailwind spacing */
        '0': '0px',
        '0.5': '2px',
        '1': '4px',
        '1.5': '6px',
        '2': '8px',
        '2.5': '10px',
        '3': '12px',
        '3.5': '14px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '7': '28px',
        '8': '32px',
        '9': '36px',
        '10': '40px',
        '12': '48px',
      },
      zIndex: {
        'canvas': '0',
        'sticky': '10',
        'toolbar': '20',
        'dropdown': '30',
        'drawer': '35',
        'modal': '40',
        'toast': '50',
      },
      transitionDuration: {
        'fast': '120ms',
        'base': '160ms',
        'slow': '220ms',
      },
      transitionTimingFunction: {
        'standard': 'cubic-bezier(0.2, 0, 0, 1)',
      },
    },
  },
  plugins: [],
}
