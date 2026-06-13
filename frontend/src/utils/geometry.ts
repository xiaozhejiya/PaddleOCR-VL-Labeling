/**
 * 几何工具函数
 * 坐标转换、bbox 校验等
 *
 * 参考：doc/开发文档/前端/frontend_development_spec.md 第 12 章
 */

/** bbox_xyxy: [xmin, ymin, xmax, ymax] */
export type BBox = [number, number, number, number]

/** quad: 四点坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] */
export type Quad = [[number, number], [number, number], [number, number], [number, number]]

/** polygon: 多点轮廓 */
export type Polygon = [number, number][]

/**
 * 校验 bbox 是否合法
 * 要求 xmin < xmax, ymin < ymax
 */
export function isValidBBox(bbox: BBox): boolean {
  const [xmin, ymin, xmax, ymax] = bbox
  return xmin < xmax && ymin < ymax
}

/**
 * 规范化 bbox，确保 xmin < xmax, ymin < ymax
 */
export function normalizeBBox(bbox: BBox): BBox {
  const [x1, y1, x2, y2] = bbox
  return [
    Math.min(x1, x2),
    Math.min(y1, y2),
    Math.max(x1, x2),
    Math.max(y1, y2),
  ]
}

/**
 * 计算 bbox 面积
 */
export function bboxArea(bbox: BBox): number {
  const [xmin, ymin, xmax, ymax] = bbox
  return (xmax - xmin) * (ymax - ymin)
}

/**
 * bbox 转 quad
 */
export function bboxToQuad(bbox: BBox): Quad {
  const [xmin, ymin, xmax, ymax] = bbox
  return [
    [xmin, ymin],
    [xmax, ymin],
    [xmax, ymax],
    [xmin, ymax],
  ]
}

/**
 * 屏幕坐标转页面原始坐标
 * @param screenX 屏幕 X
 * @param screenY 屏幕 Y
 * @param scale 缩放比例
 * @param offsetX 偏移 X
 * @param offsetY 偏移 Y
 */
export function screenToPage(
  screenX: number,
  screenY: number,
  scale: number,
  offsetX: number,
  offsetY: number
): [number, number] {
  return [
    (screenX - offsetX) / scale,
    (screenY - offsetY) / scale,
  ]
}

/**
 * 页面原始坐标转屏幕坐标
 * @param pageX 页面 X
 * @param pageY 页面 Y
 * @param scale 缩放比例
 * @param offsetX 偏移 X
 * @param offsetY 偏移 Y
 */
export function pageToScreen(
  pageX: number,
  pageY: number,
  scale: number,
  offsetX: number,
  offsetY: number
): [number, number] {
  return [
    pageX * scale + offsetX,
    pageY * scale + offsetY,
  ]
}
