import { beforeEach, describe, expect, it, vi } from 'vitest'
import { annotationsApi } from '../annotations'
import { clearToken } from '../client'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('annotationsApi', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    clearToken()
  })

  it('getLatest 在页面尚无标注时返回 null', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        data: null,
        request_id: 'req_123',
      }),
    })

    await expect(annotationsApi.getLatest('page_1')).resolves.toBeNull()
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/pages/page_1/annotation/latest',
      expect.any(Object),
    )
  })

  it('getRevision 继续解包非空 revision 数据', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        data: {
          revision_id: 'rev_1',
          page_id: 'page_1',
          revision_no: 2,
          status: 'draft',
          qc_status: 'pending',
          sha256: null,
          size_bytes: null,
          annotation_json: {
            page_id: 'page_1',
            k12_annotations: [],
            relations: [],
          },
        },
        request_id: 'req_124',
      }),
    })

    await expect(annotationsApi.getRevision('page_1', 'rev_1')).resolves.toEqual({
      id: 'rev_1',
      page_id: 'page_1',
      revision_no: 2,
      status: 'draft',
      qc_status: 'pending',
      data: {
        page_id: 'page_1',
        k12_annotations: [],
        relations: [],
      },
    })
  })
})
