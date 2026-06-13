import { ApiClientError } from '@/api/client'

type Translate = (key: string) => string

function getLocalizedMessage(t: Translate, error: ApiClientError, fallbackKey: string): string {
  if (error.status === 0) return t('errors.network')
  if (error.status === 401) return t('errors.unauthorized')
  if (error.status === 403) return t('errors.forbidden')
  if (error.status === 404) return t('errors.notFound')
  if (error.status === 409) return t('errors.conflict')
  if (error.status === 422) return t('errors.validation')
  if (error.status >= 500) return t('errors.server')
  if (typeof error.message === 'string' && error.message.startsWith('errors.')) {
    return t(error.message)
  }
  return t(fallbackKey)
}

export function formatProjectDetailError(
  t: Translate,
  error: unknown,
  fallbackKey: string,
): string {
  if (!(error instanceof ApiClientError)) {
    return t(fallbackKey)
  }

  const message = getLocalizedMessage(t, error, fallbackKey)
  if (!error.requestId) {
    return message
  }
  return `${message} (${t('errors.requestIdLabel')}: ${error.requestId})`
}
