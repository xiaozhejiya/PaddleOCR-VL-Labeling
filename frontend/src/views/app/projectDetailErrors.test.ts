import { describe, expect, it } from 'vitest'

import { ApiClientError } from '@/api/client'
import { formatProjectDetailError } from './projectDetailErrors'

const t = (key: string) => {
  const dict: Record<string, string> = {
    'errors.network': '网络错误',
    'errors.unauthorized': '未登录',
    'errors.forbidden': '权限不足',
    'errors.notFound': '资源不存在',
    'errors.conflict': '数据冲突',
    'errors.validation': '数据校验失败',
    'errors.server': '服务器错误',
    'errors.unknown': '未知错误',
    'errors.requestIdLabel': '请求 ID',
    'upload.failed': '上传失败',
  }
  return dict[key] || key
}

describe('formatProjectDetailError', () => {
  it('对带 requestId 的 ApiClientError 追加请求 ID', () => {
    const error = new ApiClientError({
      message: 'Permission denied',
      status: 403,
      request_id: 'req_123',
    })

    expect(formatProjectDetailError(t, error, 'upload.failed')).toBe(
      '权限不足 (请求 ID: req_123)',
    )
  })

  it('对非 ApiClientError 返回兜底文案', () => {
    expect(formatProjectDetailError(t, new Error('boom'), 'upload.failed')).toBe('上传失败')
  })

  it('对未知状态码使用页面兜底文案而不是原始英文 message', () => {
    const error = new ApiClientError({
      message: 'File too large',
      status: 413,
      request_id: 'req_413',
    })

    expect(formatProjectDetailError(t, error, 'upload.failed')).toBe(
      '上传失败 (请求 ID: req_413)',
    )
  })
})
