/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DEFAULT_LOCALE: string
  readonly VITE_SUPPORTED_LOCALES: string
  readonly VITE_ENABLE_MOCK_AUTH?: string
  readonly VITE_ENABLE_REGISTRATION?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
