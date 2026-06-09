/**
 * 认证相关 API
 * 后端：POST /auth/login, GET /auth/me
 */
import { api, mockFallback, setToken, clearToken } from './client'
import { mockUser, mockDelay } from './mock'

/** 后端 AuthenticatedUser: { id: int, username: string, display_name: string, is_system_admin: bool } */
export interface User {
  id: string
  username: string
  display_name: string
  is_system_admin: boolean
}

export interface LoginRequest {
  username: string
  password: string
}

/** 后端 LoginResponse: { access_token, token_type, expires_in, user } */
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

/** 将后端 User 适配为前端统一格式（id 转 string） */
function adaptUser(raw: { id: number | string; username: string; display_name: string; is_system_admin?: boolean }): User {
  return {
    id: String(raw.id),
    username: raw.username,
    display_name: raw.display_name,
    is_system_admin: raw.is_system_admin ?? false,
  }
}

export const authApi = {
  /** 获取当前用户信息 */
  me: () => mockFallback(
    async () => {
      const raw = await api.get<{ id: number; username: string; display_name: string; is_system_admin?: boolean }>('/auth/me')
      return adaptUser(raw)
    },
    () => mockDelay({ id: mockUser.id, username: mockUser.username, display_name: mockUser.display_name, is_system_admin: true }),
  ),

  /** 登录，成功后自动存储 token */
  login: (data: LoginRequest) => mockFallback(
    async () => {
      const res = await api.post<LoginResponse>('/auth/login', data)
      setToken(res.access_token)
      return {
        access_token: res.access_token,
        token_type: res.token_type,
        expires_in: res.expires_in,
        user: adaptUser(res.user),
      }
    },
    async () => {
      const mockRes = {
        access_token: 'mock-token',
        token_type: 'bearer',
        expires_in: 86400,
        user: adaptUser({ id: mockUser.id, username: data.username || mockUser.username, display_name: data.username || mockUser.username, is_system_admin: true }),
      }
      setToken(mockRes.access_token)
      return mockRes
    },
  ),

  /** 登出（后端无此端点，清空本地 token） */
  logout: async () => {
    clearToken()
  },
}
