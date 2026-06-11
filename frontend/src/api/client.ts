/**
 * API 客户端基础模块
 * 封装 HTTP 请求、响应转换和错误对象
 */

export interface ApiError {
  message: string
  status: number
  code?: string
  request_id?: string
  details?: unknown
}

export class ApiClientError extends Error {
  status: number
  code?: string
  requestId?: string
  details?: unknown

  constructor(error: ApiError) {
    super(error.message)
    this.name = 'ApiClientError'
    this.status = error.status
    this.code = error.code
    this.requestId = error.request_id
    this.details = error.details
  }
}

const BASE_URL = '/api/v1'
// ── Bearer token：仅保存在内存中 ──
let accessToken: string | null = null

export function setToken(token: string) {
  accessToken = token
}

export function getToken(): string | null {
  return accessToken
}

export function clearToken() {
  accessToken = null
}

/**
 * HTTP 状态码对应的 i18n key
 * 前端使用 code 映射本地化文案，不直接展示英文异常
 */
const STATUS_I18N_KEYS: Record<number, string> = {
  400: 'errors.badRequest',
  401: 'errors.unauthorized',
  403: 'errors.forbidden',
  404: 'errors.notFound',
  409: 'errors.conflict',
  422: 'errors.validation',
  500: 'errors.server',
}

function getFallbackMessage(status: number): string {
  return STATUS_I18N_KEYS[status] || 'errors.unknown'
}

export function getAuthorizationHeader(): string | null {
  const token = getToken()
  return token ? `Bearer ${token}` : null
}

export function withAuthorizationHeader(headers: Record<string, string> = {}): Record<string, string> {
  const authHeader = getAuthorizationHeader()
  if (!authHeader) return headers
  return {
    ...headers,
    Authorization: authHeader,
  }
}

export function parseApiErrorBody(body: any, status: number): ApiError {
  const bizError = body?.error
  return {
    message: bizError?.message || body?.detail || body?.message || getFallbackMessage(status),
    status,
    code: bizError?.code || body?.code,
    request_id: body?.request_id || body?.requestId,
    details: bizError?.details || body?.details,
  }
}

export async function parseApiErrorResponse(response: Pick<Response, 'status' | 'json'>): Promise<ApiError> {
  try {
    const body = await response.json()
    return parseApiErrorBody(body, response.status)
  } catch {
    return {
      message: getFallbackMessage(response.status),
      status: response.status,
    }
  }
}

export async function fetchWithAuth(input: string, init: RequestInit = {}): Promise<Response> {
  const headers = withAuthorizationHeader({
    ...(init.headers as Record<string, string> | undefined),
  })
  return fetch(input, {
    ...init,
    headers,
    credentials: init.credentials ?? 'include',
  })
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`

  const isFormData = options.body instanceof FormData
  const baseHeaders: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers as Record<string, string>),
  }

  const config: RequestInit = {
    ...options,
    headers: withAuthorizationHeader(baseHeaders),
    credentials: options.credentials ?? 'include',
  }

  try {
    const response = await fetch(url, config)

    if (!response.ok) {
      throw new ApiClientError(await parseApiErrorResponse(response))
    }

    // 204 No Content
    if (response.status === 204) {
      return undefined as T
    }

    return await response.json()
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error
    }
    // 网络错误
    throw new ApiClientError({
      message: 'errors.network',
      status: 0,
    })
  }
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),

  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: 'DELETE' }),

  /** multipart/form-data 上传（不设 Content-Type，由浏览器自动带 boundary） */
  upload: <T>(endpoint: string, formData: FormData) =>
    request<T>(endpoint, {
      method: 'POST',
      body: formData,
      headers: {},
    }),
}
