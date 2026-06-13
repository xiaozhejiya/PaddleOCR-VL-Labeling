/**
 * 标注状态管理
 * 管理标注对象列表、选中状态、撤销/重做
 *
 * 标注对象结构对齐后端 annotation_json 契约：
 *   doc/开发文档/后端/backend_api_reference.md §7.3
 *   doc/开发文档/前端/annotation_workspace_interaction_spec.md §11
 */
import { ref, computed } from 'vue'
import type { AnnotationRevision, AnnotationDraft } from '@/api/annotations'

// ── 几何类型 ──

/** 四点框：4 个 [x, y] 顶点，顺时针从左上开始 */
export type Quad = [[number, number], [number, number], [number, number], [number, number]]

/** 多边形：至少 3 个 [x, y] 顶点 */
export type Polygon = [number, number][]

/** 几何数据，至少包含 bbox_xyxy、quad 或 polygon 之一 */
export interface AnnotationGeometry {
  bbox_xyxy?: [number, number, number, number]
  quad?: Quad
  polygon?: Polygon
  geometry_source?: 'manual' | 'auto_generated'
}

// ── 标注对象（对齐后端 k12_annotations 元素） ──

export interface AnnotationObject {
  id: string
  type: string                        // 标签类型，如 question_block、answer_area
  label_namespace: string             // 标签命名空间，K12 场景固定 'k12'
  geometry: AnnotationGeometry
  read_order?: number
  attributes: Record<string, unknown>
  source_refs: unknown[]
  status: 'draft' | 'active' | 'deleted'
  color: string                       // 前端展示用，不保存到后端
}

// ── 后端 annotation_json 中的单条标注（只读，用于解析） ──

interface BackendAnnotation {
  id: string
  type?: string
  label_name?: string
  label_namespace?: string
  geometry: {
    bbox_xyxy?: [number, number, number, number]
    quad?: Quad
    polygon?: Polygon
    geometry_source?: string
  }
  read_order?: number
  attributes?: Record<string, unknown>
  source_refs?: unknown[]
  status?: string
}

// ── 后端 annotation_json 整页结构 ──

export interface AnnotationJson {
  schema_version: string
  page_id: string
  k12_annotations: BackendAnnotation[]
  relations: unknown[]
  history?: unknown[]
}

// 默认标签颜色映射
const LABEL_COLORS: Record<string, string> = {
  question_block: '#5e6ad2',
  answer_area: '#24a148',
  option_block: '#0f62fe',
  option_image: '#0f62fe',
  stem_figure: '#da1e28',
  formula: '#dd5b00',
  table: '#0f62fe',
  noise_or_erasure: '#8c8c8c',
}

export function getDefaultColor(label: string): string {
  return LABEL_COLORS[label] || '#5e6ad2'
}

interface AnnotationLabelInput {
  name: string
  namespace: string
  color?: string | null
}

let nextId = 1
function generateId(): string {
  return `obj-${Date.now()}-${nextId++}`
}

// ── 几何工具 ──

/** 从 bbox_xyxy 生成 quad（顺时针 4 点） */
function bboxToQuad(bbox: [number, number, number, number]): Quad {
  const [xmin, ymin, xmax, ymax] = bbox
  return [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
}

/** 从 bbox_xyxy 生成 polygon（矩形 4 点） */
function bboxToPolygon(bbox: [number, number, number, number]): Polygon {
  const [xmin, ymin, xmax, ymax] = bbox
  return [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
}

/** 确保 bbox_xyxy 的 xmin < xmax, ymin < ymax（严格小于，对齐后端校验） */
function normalizeBbox(bbox: [number, number, number, number]): [number, number, number, number] {
  let [xmin, ymin, xmax, ymax] = bbox
  if (xmin > xmax) [xmin, xmax] = [xmax, xmin]
  if (ymin > ymax) [ymin, ymax] = [ymax, ymin]
  // 后端要求 xmin < xmax 且 ymin < ymax（严格不等），退化时扩大 1px
  if (xmin >= xmax) xmax = xmin + 1
  if (ymin >= ymax) ymax = ymin + 1
  return [xmin, ymin, xmax, ymax]
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

function clampBboxToBounds(
  bbox: [number, number, number, number],
  bounds: { width: number; height: number } | null,
): [number, number, number, number] {
  const normalized = normalizeBbox(bbox)
  if (!bounds) return normalized

  const maxX = Math.max(bounds.width, 0)
  const maxY = Math.max(bounds.height, 0)

  let [xmin, ymin, xmax, ymax] = [
    clamp(normalized[0], 0, maxX),
    clamp(normalized[1], 0, maxY),
    clamp(normalized[2], 0, maxX),
    clamp(normalized[3], 0, maxY),
  ]

  // clamp 后可能退化（如全部 clamp 到同一边界），确保严格不等
  if (xmin >= xmax) xmax = Math.min(xmin + 1, maxX)
  if (ymin >= ymax) ymax = Math.min(ymin + 1, maxY)
  // 极端情况：maxX=0 时 xmin=xmax=0，expand 到 1
  if (xmin >= xmax) xmax = xmin + 1
  if (ymin >= ymax) ymax = ymin + 1

  return [xmin, ymin, xmax, ymax]
}

/** 从 bbox 重建完整 geometry（quad + polygon + geometry_source） */
function buildGeometry(
  bbox: [number, number, number, number],
  geometrySource: 'manual' | 'auto_generated' = 'manual',
): AnnotationGeometry {
  return {
    bbox_xyxy: bbox,
    quad: bboxToQuad(bbox),
    polygon: bboxToPolygon(bbox),
    geometry_source: geometrySource,
  }
}

export function useAnnotationStore() {
  const objects = ref<AnnotationObject[]>([])
  const selectedId = ref<string | null>(null)
  const baseRevisionId = ref<string | undefined>(undefined)
  const revisionNo = ref(0)
  const imageBounds = ref<{ width: number; height: number } | null>(null)
  const readOrderSession = ref<{ active: boolean; counter: number }>({
    active: false,
    counter: 0,
  })

  // ── 撤销/重做 ──
  const undoStack = ref<string[]>([])  // JSON snapshots
  const redoStack = ref<string[]>([])
  const MAX_HISTORY = 50

  function saveSnapshot() {
    const snap = JSON.stringify(objects.value)
    undoStack.value.push(snap)
    if (undoStack.value.length > MAX_HISTORY) undoStack.value.shift()
    redoStack.value = []  // 新操作清空 redo 栈
  }

  function undo() {
    if (undoStack.value.length === 0) return
    const current = JSON.stringify(objects.value)
    redoStack.value.push(current)
    const prev = undoStack.value.pop()!
    objects.value = JSON.parse(prev)
    // 清除选中（可能已不存在）
    if (selectedId.value && !objects.value.find(o => o.id === selectedId.value)) {
      selectedId.value = null
    }
  }

  function redo() {
    if (redoStack.value.length === 0) return
    const current = JSON.stringify(objects.value)
    undoStack.value.push(current)
    const next = redoStack.value.pop()!
    objects.value = JSON.parse(next)
  }

  const canUndo = computed(() => undoStack.value.length > 0)
  const canRedo = computed(() => redoStack.value.length > 0)

  // ── 选中对象 ──
  const selectedObject = computed(() =>
    objects.value.find(o => o.id === selectedId.value) || null
  )

  function select(id: string | null) {
    selectedId.value = id
  }

  // ── 增删改 ──
  function setImageBounds(width: number, height: number) {
    imageBounds.value = { width, height }
  }

  function addObject(bbox: [number, number, number, number], label: AnnotationLabelInput) {
    saveSnapshot()
    const normalized = clampBboxToBounds(bbox, imageBounds.value)
    const obj: AnnotationObject = {
      id: generateId(),
      type: label.name,
      label_namespace: label.namespace,
      geometry: buildGeometry(normalized),
      attributes: {},
      source_refs: [],
      status: 'draft',
      color: label.color || getDefaultColor(label.name),
    }
    objects.value.push(obj)
    selectedId.value = obj.id
    return obj
  }

  function updateObject(
    id: string,
    patch: Partial<Pick<AnnotationObject, 'type' | 'label_namespace' | 'read_order' | 'color'>> & { bbox_xyxy?: [number, number, number, number] },
  ) {
    saveSnapshot()
    const obj = objects.value.find(o => o.id === id)
    if (!obj) return
    if (patch.type !== undefined) {
      obj.type = patch.type
      obj.color = getDefaultColor(patch.type)
    }
    if (patch.label_namespace !== undefined) obj.label_namespace = patch.label_namespace
    if (patch.bbox_xyxy !== undefined) {
      obj.geometry = buildGeometry(clampBboxToBounds(patch.bbox_xyxy, imageBounds.value))
    }
    if (patch.read_order !== undefined) obj.read_order = patch.read_order
    if (patch.color !== undefined) obj.color = patch.color
  }

  function deleteObject(id: string) {
    saveSnapshot()
    objects.value = objects.value.filter(o => o.id !== id)
    if (selectedId.value === id) selectedId.value = null
  }

  function deleteSelected() {
    if (selectedId.value) deleteObject(selectedId.value)
  }

  /** 移动 bbox（增量，图片坐标） */
  function moveObject(id: string, dx: number, dy: number) {
    const obj = objects.value.find(o => o.id === id)
    if (!obj || !obj.geometry.bbox_xyxy) return
    const [xmin, ymin, xmax, ymax] = obj.geometry.bbox_xyxy
    const width = xmax - xmin
    const height = ymax - ymin

    if (imageBounds.value) {
      const maxX = Math.max(imageBounds.value.width - width, 0)
      const maxY = Math.max(imageBounds.value.height - height, 0)
      const nextXmin = clamp(xmin + dx, 0, maxX)
      const nextYmin = clamp(ymin + dy, 0, maxY)
      obj.geometry = buildGeometry([nextXmin, nextYmin, nextXmin + width, nextYmin + height])
      return
    }

    const newBbox: [number, number, number, number] = [xmin + dx, ymin + dy, xmax + dx, ymax + dy]
    obj.geometry = buildGeometry(normalizeBbox(newBbox))
  }

  /** 开始拖拽前保存快照（供 AnnotationCanvas 在 mousedown 时调用） */
  function savePreDragSnapshot() {
    saveSnapshot()
  }

  /** 调整 bbox 大小（通过控制点索引 0-7） */
  function resizeObject(id: string, handleIndex: number, imgX: number, imgY: number) {
    const obj = objects.value.find(o => o.id === id)
    if (!obj || !obj.geometry.bbox_xyxy) return
    let [xmin, ymin, xmax, ymax] = obj.geometry.bbox_xyxy

    // 控制点: 0=上中, 1=右上, 2=右中, 3=右下, 4=下中, 5=左下, 6=左中, 7=左上
    if (handleIndex === 0 || handleIndex === 7 || handleIndex === 6) ymin = imgY  // 上边
    if (handleIndex === 1 || handleIndex === 2 || handleIndex === 3) xmax = imgX  // 右边
    if (handleIndex === 3 || handleIndex === 4 || handleIndex === 5) ymax = imgY  // 下边
    if (handleIndex === 5 || handleIndex === 6 || handleIndex === 7) xmin = imgX  // 左边

    obj.geometry = buildGeometry(clampBboxToBounds([xmin, ymin, xmax, ymax], imageBounds.value))
  }

  /** 设置阅读顺序 */
  function setReadOrder(id: string, order: number) {
    saveSnapshot()
    const obj = objects.value.find(o => o.id === id)
    if (obj) obj.read_order = order
  }

  function clearReadOrder() {
    const hasReadOrder = objects.value.some(obj => (obj.read_order ?? 0) > 0)
    if (hasReadOrder) {
      saveSnapshot()
      for (const obj of objects.value) {
        delete obj.read_order
      }
    }
    readOrderSession.value.counter = 0
  }

  function startReadOrderSession() {
    if (readOrderSession.value.active) return
    clearReadOrder()
    readOrderSession.value = {
      active: true,
      counter: 0,
    }
  }

  function assignNextReadOrder(id: string): number | null {
    if (!readOrderSession.value.active) return null
    const obj = objects.value.find(o => o.id === id)
    if (!obj) return null
    if ((obj.read_order ?? 0) > 0) {
      return obj.read_order ?? null
    }
    saveSnapshot()
    const nextOrder = readOrderSession.value.counter + 1
    obj.read_order = nextOrder
    readOrderSession.value.counter = nextOrder
    return nextOrder
  }

  function endReadOrderSession() {
    readOrderSession.value = {
      active: false,
      counter: 0,
    }
  }

  // ── 从 revision 加载 ──
  function loadFromRevision(revision: AnnotationRevision | null) {
    if (!revision) {
      objects.value = []
      baseRevisionId.value = undefined
      revisionNo.value = 0
      return
    }

    baseRevisionId.value = revision.id
    revisionNo.value = revision.revision_no

    const data = revision.data as unknown as AnnotationJson
    const annotations = data.k12_annotations || []
    objects.value = annotations.map((a: BackendAnnotation) => ({
      id: a.id,
      type: a.type || a.label_name || 'question_block',
      label_namespace: a.label_namespace || 'k12',
      geometry: {
        bbox_xyxy: a.geometry?.bbox_xyxy,
        quad: a.geometry?.quad,
        polygon: a.geometry?.polygon,
        geometry_source: (a.geometry?.geometry_source as 'manual' | 'auto_generated') || 'auto_generated',
      },
      read_order: (a.read_order != null && a.read_order > 0) ? a.read_order : undefined,
      attributes: a.attributes || {},
      source_refs: a.source_refs || [],
      status: (a.status as 'draft' | 'active' | 'deleted') || 'active',
      color: getDefaultColor(a.type || a.label_name || 'question_block'),
    }))

    undoStack.value = []
    redoStack.value = []
    selectedId.value = null
    endReadOrderSession()
  }

  /** 导出为 AnnotationDraft（对齐后端 annotation_json 契约） */
  function toDraft(pageId: string): AnnotationDraft {
    const annotationJson: AnnotationJson = {
      schema_version: 'k12_annotation_v0.1',
      page_id: pageId,
      k12_annotations: objects.value.map(o => {
        const ann: BackendAnnotation = {
          id: o.id,
          type: o.type,
          label_namespace: o.label_namespace,
          geometry: {
            bbox_xyxy: o.geometry.bbox_xyxy,
            quad: o.geometry.quad,
            polygon: o.geometry.polygon,
            geometry_source: o.geometry.geometry_source,
          },
          attributes: o.attributes,
          source_refs: o.source_refs,
          status: o.status,
        }
        // 后端要求 read_order 为正整数或不传；0/负数/undefined/NaN 一律省略
        if (o.read_order != null && o.read_order > 0) {
          ann.read_order = o.read_order
        }
        return ann
      }),
      relations: [],
    }
    return {
      page_id: pageId,
      base_revision_id: baseRevisionId.value ?? null,
      data: annotationJson as unknown as Record<string, unknown>,
    }
  }

  return {
    objects,
    selectedId,
    selectedObject,
    baseRevisionId,
    revisionNo,
    imageBounds,
    readOrderSession,
    canUndo,
    canRedo,
    setImageBounds,
    select,
    addObject,
    updateObject,
    deleteObject,
    deleteSelected,
    moveObject,
    resizeObject,
    setReadOrder,
    clearReadOrder,
    startReadOrderSession,
    assignNextReadOrder,
    endReadOrderSession,
    savePreDragSnapshot,
    loadFromRevision,
    toDraft,
    undo,
    redo,
  }
}
