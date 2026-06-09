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

// ── Bearer JWT token 管理（sessionStorage 持久化，刷新不丢失） ──
const TOKEN_KEY = 'k12.access_token'
let accessToken: string | null = null

export function setToken(token: string) {
  accessToken = token
  try { sessionStorage.setItem(TOKEN_KEY, token) } catch { /* quota exceeded */ }
}

export function getToken(): string | null {
  if (accessToken) return accessToken
  try { accessToken = sessionStorage.getItem(TOKEN_KEY) } catch { /* private mode */ }
  return accessToken
}

export function clearToken() {
  accessToken = null
  try { sessionStorage.removeItem(TOKEN_KEY) } catch { /* ignore */ }
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

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`

  const isFormData = options.body instanceof FormData
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers as Record<string, string>),
  }

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const config: RequestInit = {
    ...options,
    headers,
  }

  try {
    const response = await fetch(url, config)

    if (!response.ok) {
      let errorData: ApiError
      try {
        const body = await response.json()
        // FastAPI 返回 {"detail": "..."} 格式，需要适配
        errorData = {
          message: body.detail || body.message || STATUS_I18N_KEYS[response.status] || 'errors.unknown',
          status: response.status,
          code: body.code,
          request_id: body.request_id || body.requestId,
          details: body.details,
        }
      } catch {
        errorData = {
          message: STATUS_I18N_KEYS[response.status] || 'errors.unknown',
          status: response.status,
        }
      }
      throw new ApiClientError(errorData)
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

/**
 * Mock fallback 工具
 * 当后端不可用时，自动 fallback 到 mock 数据
 * 首次失败后记录状态，后续请求直接走 mock，避免重复请求失败的延迟
 */
let backendAvailable: boolean | null = null

export async function mockFallback<T>(
  apiCall: () => Promise<T>,
  mockData: T | (() => Promise<T> | T),
): Promise<T> {
  // 如果已确认后端不可用，直接走 mock
  if (backendAvailable === false) {
    return typeof mockData === 'function'
      ? (mockData as () => Promise<T> | T)()
      : structuredClone(mockData) as T
  }

  try {
    const result = await apiCall()
    backendAvailable = true
    return result
  } catch {
    // 后端不可用，切换到 mock 模式
    backendAvailable = false
    console.info('[Mock] Backend unavailable, using mock data')
    return typeof mockData === 'function'
      ? (mockData as () => Promise<T> | T)()
      : structuredClone(mockData) as T
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
