import { describe, it, expect } from 'vitest'
import { formatFileSize, formatPercent, truncateText } from '../format'

describe('formatFileSize', () => {
  it('格式化 0 字节', () => {
    expect(formatFileSize(0)).toBe('0 B')
  })

  it('格式化 KB', () => {
    expect(formatFileSize(1024)).toBe('1.0 KB')
  })

  it('格式化 MB', () => {
    expect(formatFileSize(1024 * 1024)).toBe('1.0 MB')
  })
})

describe('formatPercent', () => {
  it('格式化百分比', () => {
    expect(formatPercent(0.5)).toBe('50.0%')
    expect(formatPercent(0.123, 2)).toBe('12.30%')
  })
})

describe('truncateText', () => {
  it('短文本不截断', () => {
    expect(truncateText('hello', 10)).toBe('hello')
  })

  it('长文本截断', () => {
    expect(truncateText('hello world', 5)).toBe('hello...')
  })
})
