/**
 * Geometry 工具测试
 * 覆盖 bbox 校验、规范化、坐标转换等场景
 */
import { describe, it, expect } from 'vitest'
import {
  isValidBBox,
  normalizeBBox,
  bboxArea,
  bboxToQuad,
  screenToPage,
  pageToScreen,
} from '../geometry'

describe('isValidBBox', () => {
  it('合法 bbox 返回 true', () => {
    expect(isValidBBox([10, 20, 100, 200])).toBe(true)
  })

  it('xmin >= xmax 返回 false', () => {
    expect(isValidBBox([100, 20, 10, 200])).toBe(false)
    expect(isValidBBox([10, 20, 10, 200])).toBe(false)
  })

  it('ymin >= ymax 返回 false', () => {
    expect(isValidBBox([10, 200, 100, 20])).toBe(false)
    expect(isValidBBox([10, 20, 100, 20])).toBe(false)
  })
})

describe('normalizeBBox', () => {
  it('已规范化的 bbox 不变', () => {
    expect(normalizeBBox([10, 20, 100, 200])).toEqual([10, 20, 100, 200])
  })

  it('反转的 bbox 被规范化', () => {
    expect(normalizeBBox([100, 200, 10, 20])).toEqual([10, 20, 100, 200])
  })

  it('部分反转的 bbox 被规范化', () => {
    expect(normalizeBBox([100, 20, 10, 200])).toEqual([10, 20, 100, 200])
  })
})

describe('bboxArea', () => {
  it('计算面积', () => {
    expect(bboxArea([0, 0, 10, 20])).toBe(200)
  })

  it('零面积', () => {
    expect(bboxArea([10, 20, 10, 20])).toBe(0)
  })
})

describe('bboxToQuad', () => {
  it('bbox 转四点坐标', () => {
    const bbox: [number, number, number, number] = [10, 20, 100, 200]
    const quad = bboxToQuad(bbox)
    expect(quad).toEqual([
      [10, 20],   // 左上
      [100, 20],  // 右上
      [100, 200], // 右下
      [10, 200],  // 左下
    ])
  })
})

describe('screenToPage', () => {
  it('无偏移无缩放', () => {
    const [x, y] = screenToPage(100, 200, 1, 0, 0)
    expect(x).toBe(100)
    expect(y).toBe(200)
  })

  it('有缩放', () => {
    const [x, y] = screenToPage(200, 400, 2, 0, 0)
    expect(x).toBe(100)
    expect(y).toBe(200)
  })

  it('有偏移', () => {
    const [x, y] = screenToPage(150, 250, 1, 50, 50)
    expect(x).toBe(100)
    expect(y).toBe(200)
  })

  it('有缩放和偏移', () => {
    const [x, y] = screenToPage(250, 450, 2, 50, 50)
    expect(x).toBe(100)
    expect(y).toBe(200)
  })
})

describe('pageToScreen', () => {
  it('无偏移无缩放', () => {
    const [x, y] = pageToScreen(100, 200, 1, 0, 0)
    expect(x).toBe(100)
    expect(y).toBe(200)
  })

  it('有缩放', () => {
    const [x, y] = pageToScreen(100, 200, 2, 0, 0)
    expect(x).toBe(200)
    expect(y).toBe(400)
  })

  it('有偏移', () => {
    const [x, y] = pageToScreen(100, 200, 1, 50, 50)
    expect(x).toBe(150)
    expect(y).toBe(250)
  })

  it('坐标转换可逆', () => {
    const pageX = 123.456
    const pageY = 789.012
    const scale = 1.5
    const offsetX = 50
    const offsetY = 100

    const [screenX, screenY] = pageToScreen(pageX, pageY, scale, offsetX, offsetY)
    const [backX, backY] = screenToPage(screenX, screenY, scale, offsetX, offsetY)

    expect(backX).toBeCloseTo(pageX)
    expect(backY).toBeCloseTo(pageY)
  })
})
