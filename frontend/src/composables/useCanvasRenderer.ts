/**
 * 固定视口 Canvas 渲染器
 *
 * 核心原则：
 * 1. Canvas 物理/逻辑尺寸在初始化时锁定，绝不因图片尺寸而改变
 * 2. 使用 setTransform 一次性设置变换矩阵，禁止 scale()/translate() 累积
 * 3. 绘制图片后立即重置矩阵，确保标注 UI 在原始矩阵下绘制
 * 4. 提供精确的屏幕坐标 → 原图坐标反算函数
 */
import { ref, computed } from 'vue'

export interface Point {
  x: number
  y: number
}

/** 固定视口尺寸（逻辑像素） */
const VIEWPORT_W = 800
const VIEWPORT_H = 600

export function useCanvasRenderer() {
  // ── 状态 ──
  const scale = ref(1)
  const offset = ref<Point>({ x: 0, y: 0 })
  const imageSize = ref<Point>({ x: 0, y: 0 })
  const imageSource = ref<HTMLImageElement | null>(null)
  const dpr = ref(1)

  // ── 视口边界（基于逻辑像素，用于 SVG viewBox） ──
  const viewport = computed(() => ({ w: VIEWPORT_W, h: VIEWPORT_H }))

  // ── 缩放约束 ──
  const MIN_SCALE = 0.05
  const MAX_SCALE = 20

  /**
   * 初始化 Canvas
   *
   * 物理尺寸 = 逻辑尺寸 × DPR，写死后不再改变。
   * CSS 尺寸 = 逻辑尺寸，写死后不再改变。
   *
   * @returns DPR 值，供外部调试用
   */
  function initCanvas(canvas: HTMLCanvasElement): number {
    const currentDpr = window.devicePixelRatio || 1
    dpr.value = currentDpr

    // 物理像素：写死，与图片无关
    canvas.width = VIEWPORT_W * currentDpr
    canvas.height = VIEWPORT_H * currentDpr

    // CSS 像素：写死，与图片无关
    canvas.style.width = `${VIEWPORT_W}px`
    canvas.style.height = `${VIEWPORT_H}px`

    return currentDpr
  }

  /**
   * 将图片适配到固定视口
   *
   * 计算等比缩放比例和居中偏移量，不修改任何 Canvas 尺寸。
   */
  function fitImageToViewport(imgW: number, imgH: number): void {
    const scaleX = VIEWPORT_W / imgW
    const scaleY = VIEWPORT_H / imgH
    const s = Math.min(scaleX, scaleY) * 0.95 // 留 5% 边距

    scale.value = s
    offset.value = {
      x: (VIEWPORT_W - imgW * s) / 2,
      y: (VIEWPORT_H - imgH * s) / 2,
    }
  }

  /**
   * 核心渲染函数
   *
   * 第一阶段：setTransform 一次性设置矩阵 → 绘制图片
   * 第二阶段：重置矩阵 → 绘制标注 UI（不累积变换）
   *
   * @param canvas  目标 Canvas 元素
   * @param drawUI  可选的 UI 绘制回调，在矩阵重置后调用
   */
  function render(canvas: HTMLCanvasElement, drawUI?: (ctx: CanvasRenderingContext2D) => void): void {
    const ctx = canvas.getContext('2d')
    if (!ctx || !imageSource.value) return

    const currentDpr = dpr.value
    const s = scale.value
    const ox = offset.value.x
    const oy = offset.value.y

    // ── 阶段 1：清除并绘制图片 ──
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 一次性设置：DPR × 缩放 + DPR × 偏移
    // 禁止使用 ctx.scale() / ctx.translate() 累积矩阵
    ctx.setTransform(
      currentDpr * s, 0,              // 水平缩放
      0, currentDpr * s,              // 垂直缩放
      currentDpr * ox, currentDpr * oy // 偏移
    )
    ctx.drawImage(imageSource.value, 0, 0)

    // ── 阶段 2：重置矩阵，绘制标注 UI ──
    // 重置为 DPR 缩放（逻辑坐标 1:1 映射，高清屏清晰）
    ctx.setTransform(currentDpr, 0, 0, currentDpr, 0, 0)
    drawUI?.(ctx)
  }

  /**
   * 屏幕坐标 → 原图坐标
   *
   * 逆矩阵推导：
   *   screenX = imgX * scale + offsetX
   *   imgX = (screenX - offsetX) / scale
   *
   * @param screenX  鼠标相对于 Canvas 左上角的 X（CSS 像素）
   * @param screenY  鼠标相对于 Canvas 左上角的 Y（CSS 像素）
   * @returns 原图像素坐标，若在图片外则返回 null
   */
  function screenToImage(screenX: number, screenY: number): Point | null {
    const s = scale.value
    if (s === 0) return null

    const imgX = (screenX - offset.value.x) / s
    const imgY = (screenY - offset.value.y) / s

    // 边界检查
    const { x: imgW, y: imgH } = imageSize.value
    if (imgX < 0 || imgY < 0 || imgX > imgW || imgY > imgH) return null

    return { x: imgX, y: imgY }
  }

  /**
   * 屏幕坐标 → 视口坐标（不做边界检查）
   *
   * 用于标注绘制：鼠标事件坐标直接就是视口坐标（Canvas 逻辑像素），
   * 标注 SVG 的 viewBox 与 Canvas 逻辑尺寸一致，所以直接透传。
   */
  function screenToViewport(screenX: number, screenY: number): Point {
    return { x: screenX, y: screenY }
  }

  /**
   * 原图坐标 → 视口坐标
   *
   * 用于将存储的标注坐标（原图像素）转换为 SVG 绘制坐标（视口像素）。
   *
   *   vpX = imgX * scale + offsetX
   */
  function imageToViewport(imgX: number, imgY: number): Point {
    return {
      x: imgX * scale.value + offset.value.x,
      y: imgY * scale.value + offset.value.y,
    }
  }

  // ── 缩放操作 ──

  /**
   * 以指定视口坐标为中心缩放
   *
   * 缩放时保持 center 对应的图片点不变（锚点缩放）。
   */
  function zoomAt(delta: number, centerX: number, centerY: number): void {
    const oldScale = scale.value
    const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, oldScale * (1 + delta)))
    if (newScale === oldScale) return

    // 锚点：center 对应的图片坐标在缩放前后不变
    const imgX = (centerX - offset.value.x) / oldScale
    const imgY = (centerY - offset.value.y) / oldScale

    offset.value = {
      x: centerX - imgX * newScale,
      y: centerY - imgY * newScale,
    }
    scale.value = newScale
  }

  function pan(dx: number, dy: number): void {
    offset.value = {
      x: offset.value.x + dx,
      y: offset.value.y + dy,
    }
  }

  function fitToWidth(): void {
    const imgW = imageSize.value.x
    if (imgW === 0) return

    const s = VIEWPORT_W / imgW
    scale.value = Math.max(MIN_SCALE, Math.min(MAX_SCALE, s))
    offset.value = {
      x: 0,
      y: (VIEWPORT_H - imageSize.value.y * scale.value) / 2,
    }
  }

  function fitToContainer(): void {
    const { x: imgW, y: imgH } = imageSize.value
    if (imgW === 0 || imgH === 0) return
    fitImageToViewport(imgW, imgH)
  }

  function zoomIn(): void {
    zoomAt(0.1, VIEWPORT_W / 2, VIEWPORT_H / 2)
  }

  function zoomOut(): void {
    zoomAt(-0.1, VIEWPORT_W / 2, VIEWPORT_H / 2)
  }

  // ── 加载图片 ──

  /**
   * 从 URL 加载图片
   *
   * 仅设置 imageSize 和 imageSource，不触碰 Canvas 尺寸。
   * 返回 Promise，外部调用后自行调用 render()。
   */
  function loadImage(url: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => {
        imageSize.value = { x: img.naturalWidth, y: img.naturalHeight }
        imageSource.value = img
        resolve(img)
      }
      img.onerror = reject
      img.src = url
    })
  }

  // ── 计算属性 ──

  const zoomPercent = computed(() => Math.round(scale.value * 100))

  return {
    // 状态
    scale,
    offset,
    imageSize,
    imageSource,
    dpr,
    viewport,
    zoomPercent,

    // Canvas 初始化
    initCanvas,

    // 图片加载
    loadImage,

    // 渲染
    render,
    fitImageToViewport,

    // 坐标转换
    screenToImage,
    screenToViewport,
    imageToViewport,

    // 缩放操作
    zoomAt,
    pan,
    fitToWidth,
    fitToContainer,
    zoomIn,
    zoomOut,
  }
}
