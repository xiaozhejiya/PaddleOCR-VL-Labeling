/**
 * 认证相关 API
 * 后端：POST /auth/login, POST /auth/logout, GET /auth/me
 */
import { api, clearToken } from './client'

/** 后端 AuthenticatedUser */
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

/** 后端 LoginResponse */
export interface LoginResponse {
  expires_in: number
  user: User
}

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
  me: async () => {
    const raw = await api.get<{ id: number; username: string; display_name: string; is_system_admin: boolean }>('/auth/me')
    return adaptUser(raw)
  },

  /** 登录，成功后由 HttpOnly Cookie 持久化会话 */
  login: async (data: LoginRequest) => {
    const res = await api.post<LoginResponse>('/auth/login', data)
    return {
      expires_in: res.expires_in,
      user: adaptUser(res.user),
    }
  },

  /** 登出（清空服务端 Cookie 会话） */
  logout: async () => {
    await api.post<void>('/auth/logout')
    clearToken()
  },
}
