/**
 * 认证状态 composable
 * 单一来源管理用户会话，供路由守卫和页面共用
 */
import { ref, readonly } from 'vue'
import { authApi, type User } from '@/api/auth'
import { ApiClientError, clearToken } from '@/api/client'

const user = ref<User | null>(null)
const loading = ref(false)
const initialized = ref(false)

export function useAuth() {
  /**
   * 恢复会话
   * 页面刷新后调用，从后端获取当前用户信息
   * 401 时静默清空用户态，不抛异常
   */
  async function fetchUser(): Promise<User | null> {
    if (loading.value) {
      return user.value
    }

    loading.value = true
    try {
      user.value = await authApi.me()
      initialized.value = true
      return user.value
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 401) {
        user.value = null
        clearToken()
        initialized.value = true
        return null
      }
      // 其他错误（网络、5xx 等）保留当前用户态，让后续有机会重试
      return user.value
    } finally {
      loading.value = false
    }
  }

  /**
   * 登录
   * 成功后设置用户态和 token，由调用方负责跳转
   */
  async function login(username: string, password: string): Promise<User> {
    loading.value = true
    try {
      const response = await authApi.login({ username, password })
      user.value = response.user
      initialized.value = true
      return response.user
    } finally {
      loading.value = false
    }
  }

  /**
   * 登出
   * 清空用户态和 token，由调用方负责跳转
   */
  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      // 即使后端调用失败，也要清空前端状态
    } finally {
      user.value = null
      clearToken()
    }
  }

  /**
   * 是否已登录
   */
  function isAuthenticated(): boolean {
    return user.value !== null
  }

  /**
   * 确保会话已初始化
   * 路由守卫调用，避免每次都请求后端
   */
  async function ensureSession(): Promise<boolean> {
    if (!initialized.value && !loading.value) {
      await fetchUser()
    }

    return isAuthenticated()
  }

  return {
    user: readonly(user),
    loading: readonly(loading),
    initialized: readonly(initialized),
    fetchUser,
    login,
    logout,
    isAuthenticated,
    ensureSession,
  }
}
