import { beforeEach, describe, expect, it, vi } from 'vitest'

import { labelsApi } from '../labels'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('labelsApi', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('listByProject 读取项目标签注册表', async () => {
    const payload = {
      items: [
        {
          id: 1,
          project_id: null,
          namespace: 'k12',
          name: 'question_block',
          display_name: 'Question',
          display_name_i18n: { 'zh-CN': '题目', 'en-US': 'Question' },
          geometry_types: ['bbox_xyxy', 'quad', 'polygon'],
          attributes_schema: {},
          default_color: '#5e6ad2',
          is_builtin: true,
          is_active: true,
        },
      ],
      total: 1,
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(payload),
    })

    const result = await labelsApi.listByProject('123')

    expect(result).toEqual(payload)
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/projects/123/labels', expect.any(Object))
  })
})
