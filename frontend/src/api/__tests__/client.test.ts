/**
 * API Client 测试
 * 覆盖成功响应、错误响应、网络错误、204 等场景
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api, ApiClientError, setToken, getToken, clearToken } from '../client'

// Mock fetch
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('ApiClient', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    clearToken()
  })

  describe('成功响应', () => {
    it('GET 返回 JSON 数据', async () => {
      const data = { id: '1', name: 'test' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(data),
      })

      const result = await api.get('/test')
      expect(result).toEqual(data)
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/test', expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      }))
    })

    it('POST 发送 JSON 数据', async () => {
      const body = { name: 'new' }
      const data = { id: '2', name: 'new' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: () => Promise.resolve(data),
      })

      const result = await api.post('/test', body)
      expect(result).toEqual(data)
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/test', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(body),
      }))
    })

    it('204 No Content 返回 undefined', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      const result = await api.delete('/test/1')
      expect(result).toBeUndefined()
    })
  })

  describe('错误响应', () => {
    it('400 抛出 ApiClientError', async () => {
      const errorData = { message: 'Invalid request', code: 'BAD_REQUEST', status: 400 }
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve(errorData),
      })

      try {
        await api.get('/test')
        expect.fail('Should have thrown')
      } catch (e) {
        expect(e).toBeInstanceOf(ApiClientError)
        const err = e as ApiClientError
        expect(err.status).toBe(400)
        expect(err.code).toBe('BAD_REQUEST')
      }
    })

    it('401 抛出 ApiClientError', async () => {
      const errorData = { message: 'Unauthorized', status: 401 }
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve(errorData),
      })

      try {
        await api.get('/test')
        expect.fail('Should have thrown')
      } catch (e) {
        const err = e as ApiClientError
        expect(err.status).toBe(401)
      }
    })

    it('409 抛出 ApiClientError', async () => {
      const errorData = { message: 'Conflict', code: 'REVISION_CONFLICT', status: 409 }
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: () => Promise.resolve(errorData),
      })

      try {
        await api.get('/test')
        expect.fail('Should have thrown')
      } catch (e) {
        const err = e as ApiClientError
        expect(err.status).toBe(409)
        expect(err.code).toBe('REVISION_CONFLICT')
      }
    })

    it('非 JSON 错误响应使用 i18n key', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error('Not JSON')),
      })

      try {
        await api.get('/test')
        expect.fail('Should have thrown')
      } catch (e) {
        const err = e as ApiClientError
        expect(err.status).toBe(500)
        expect(err.message).toBe('errors.server')
      }
    })

    it('后端业务错误包装 { error, request_id } 会被正确解析', async () => {
      const errorData = {
        error: {
          code: 'PAGE_NOT_FOUND',
          message: 'Page not found',
          details: { page_id: 'p1' },
        },
        request_id: 'req_123',
      }
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve(errorData),
      })

      try {
        await api.get('/pages/p1')
        expect.fail('Should have thrown')
      } catch (e) {
        const err = e as ApiClientError
        expect(err.status).toBe(404)
        expect(err.code).toBe('PAGE_NOT_FOUND')
        expect(err.requestId).toBe('req_123')
        expect(err.details).toEqual({ page_id: 'p1' })
        expect(err.message).toBe('Page not found')
      }
    })
  })

  describe('网络错误', () => {
    it('网络错误抛出 status 0', async () => {
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      try {
        await api.get('/test')
        expect.fail('Should have thrown')
      } catch (e) {
        const err = e as ApiClientError
        expect(err.status).toBe(0)
        expect(err.message).toBe('errors.network')
      }
    })
  })

  describe('token 存储', () => {
    it('token 仅保存在内存中', () => {
      setToken('token_123')
      expect(getToken()).toBe('token_123')

      clearToken()
      expect(getToken()).toBeNull()
    })
  })
})
