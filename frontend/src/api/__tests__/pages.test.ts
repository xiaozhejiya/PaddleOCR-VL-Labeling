import { describe, it, expect, vi, beforeEach } from 'vitest'
import { pagesApi } from '../pages'
import { clearToken, setToken } from '../client'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('pagesApi', () => {
  const createObjectURL = vi.fn(() => 'blob:test-url')

  beforeEach(() => {
    mockFetch.mockReset()
    createObjectURL.mockClear()
    clearToken()
    vi.stubGlobal('URL', {
      createObjectURL,
      revokeObjectURL: vi.fn(),
    })
  })

  it('getCapabilities 透传规范字段布尔映射', async () => {
    const data = {
      can_view_project: true,
      can_create_annotation_revision: false,
      can_submit_revision: false,
      can_review_revision: false,
      can_create_export_job: false,
      can_download_export: false,
      can_manage_project_members: false,
      can_manage_labels: false,
      can_manage_relations: false,
      can_lock_revision: false,
      can_unlock_revision: false,
      can_rollback_revision: false,
      can_upload_assets: false,
      can_import_pages: false,
      can_view_audit_log: false,
      can_manage_system_users: false,
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(data),
    })

    const result = await pagesApi.getCapabilities('123')
    expect(result).toEqual(data)
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/projects/123/me/capabilities', expect.any(Object))
  })

  it('fetchImageBlob 通过签名 URL 拉取 blob，并携带 Authorization header', async () => {
    setToken('token_123')
    const blob = new Blob(['image'])

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ url: '/signed/image', expires_at: '2026-01-01T00:00:00Z' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        blob: () => Promise.resolve(blob),
      })

    const result = await pagesApi.fetchImageBlob('page_1')

    expect(result).toBe('blob:test-url')
    expect(mockFetch).toHaveBeenNthCalledWith(1, '/api/v1/pages/page_1/image', expect.any(Object))
    expect(mockFetch).toHaveBeenNthCalledWith(2, '/signed/image', {
      credentials: 'include',
      headers: { Authorization: 'Bearer token_123' },
    })
    expect(createObjectURL).toHaveBeenCalledWith(blob)
  })

  it('fetchImageBlob 保留后端业务错误包装', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ url: '/signed/image', expires_at: '2026-01-01T00:00:00Z' }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({
          error: {
            code: 'IMAGE_NOT_FOUND',
            message: 'Page has no image asset',
            details: { page_id: 'page_1' },
          },
          request_id: 'req_123',
        }),
      })

    await expect(pagesApi.fetchImageBlob('page_1')).rejects.toMatchObject({
      status: 404,
      code: 'IMAGE_NOT_FOUND',
      requestId: 'req_123',
      details: { page_id: 'page_1' },
    })
  })
})
