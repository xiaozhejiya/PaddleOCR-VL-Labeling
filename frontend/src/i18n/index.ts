import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'

// locale 解析顺序：用户显式选择 > 浏览器语言 > VITE_DEFAULT_LOCALE > zh-CN
function getDefaultLocale(): string {
  const saved = localStorage.getItem('k12.locale')
  if (saved) return saved

  const browserLang = navigator.language
  if (browserLang.startsWith('zh')) return 'zh-CN'
  if (browserLang.startsWith('en')) return 'en-US'

  return import.meta.env.VITE_DEFAULT_LOCALE || 'zh-CN'
}

const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
})

export default i18n
