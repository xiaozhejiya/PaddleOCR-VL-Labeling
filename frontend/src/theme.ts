/**
 * Naive UI 主题配置
 * 将现有 CSS 变量 token 映射到 Naive UI theme-overrides
 */
import type { GlobalThemeOverrides } from 'naive-ui'

export const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#5e6ad2',
    primaryColorHover: '#828fff',
    primaryColorPressed: '#5e69d1',
    primaryColorSuppl: '#5e6ad2',
    infoColor: '#0f62fe',
    successColor: '#24a148',
    warningColor: '#dd5b00',
    errorColor: '#da1e28',
    textColorBase: '#161616',
    textColor1: '#161616',
    textColor2: '#525252',
    textColor3: '#787671',
    borderColor: '#e0e0e0',
    dividerColor: '#e0e0e0',
    hoverColor: '#f6f5f4',
    clearColor: '#8c8c8c',
    clearColorHover: '#525252',
    clearColorPressed: '#161616',
    placeholderColor: '#8c8c8c',
    placeholderColorDisabled: '#c8c4be',
    bodyColor: '#ffffff',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    popoverColor: '#ffffff',
    tableColor: '#ffffff',
    inputColor: '#ffffff',
    codeColor: '#f6f5f4',
    tabColor: '#ffffff',
    actionColor: '#f6f5f4',
    borderRadius: '6px',
    borderRadiusSmall: '4px',
    fontFamily: "'Inter', 'Geist', 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontFamilyMono: "'JetBrains Mono', 'Geist Mono', ui-monospace, SFMono-Regular, Consolas, monospace",
    fontSize: '14px',
    fontSizeMini: '11px',
    fontSizeTiny: '12px',
    fontSizeSmall: '12px',
    fontSizeMedium: '14px',
    fontSizeLarge: '16px',
    fontSizeHuge: '20px',
    heightMini: '24px',
    heightTiny: '28px',
    heightSmall: '32px',
    heightMedium: '32px',
    heightLarge: '40px',
  },
  Button: {
    borderRadiusMedium: '6px',
    borderRadiusSmall: '6px',
    borderRadiusLarge: '6px',
    fontWeight: '500',
  },
  Input: {
    borderRadius: '6px',
    borderHover: '#5e6ad2',
    borderFocus: '#5e6ad2',
    boxShadowFocus: '0 0 0 2px rgba(94, 106, 210, 0.2)',
  },
  Tabs: {
    tabTextColorActiveLine: '#5e6ad2',
    tabTextColorHoverLine: '#5e6ad2',
    barColor: '#5e6ad2',
  },
  Message: {
    borderRadius: '8px',
  },
  Notification: {
    borderRadius: '8px',
  },
  Empty: {
    textColor: '#8c8c8c',
    fontSize: '14px',
  },
  Tag: {
    borderRadius: '4px',
  },
  Upload: {
    borderRadius: '8px',
  },
}
