import { beforeEach, describe, expect, it, vi } from 'vitest'
import { revokeObjectUrl, syncThumbnailObjectUrls } from '../workspaceImageUrls'

describe('workspaceImageUrls', () => {
  beforeEach(() => {
    vi.stubGlobal('URL', {
      revokeObjectURL: vi.fn(),
      createObjectURL: vi.fn(),
    })
  })

  it('revokeObjectUrl 仅释放 blob URL', () => {
    revokeObjectUrl('blob:test')
    revokeObjectUrl('/static/image.png')
    revokeObjectUrl(null)

    expect(URL.revokeObjectURL).toHaveBeenCalledTimes(1)
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test')
  })

  it('syncThumbnailObjectUrls 会释放已移出列表的缩略图 URL', () => {
    const result = syncThumbnailObjectUrls({
      current: {
        page1: 'blob:1',
        page2: 'blob:2',
      },
      nextPageIds: ['page2', 'page3'],
    })

    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:1')
    expect(result).toEqual({ page2: 'blob:2' })
  })
})

