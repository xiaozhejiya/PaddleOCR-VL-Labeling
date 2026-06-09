/**
 * 标注状态管理
 * 管理标注对象列表、选中状态、撤销/重做
 */
import { ref, computed } from 'vue'
import type { AnnotationRevision, AnnotationDraft } from '@/api/annotations'

export interface AnnotationObject {
  id: string
  label: string
  bbox_xyxy: [number, number, number, number]  // [xmin, ymin, xmax, ymax]
  read_order: number
  color: string
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

let nextId = 1
function generateId(): string {
  return `obj-${Date.now()}-${nextId++}`
}

export function useAnnotationStore() {
  const objects = ref<AnnotationObject[]>([])
  const selectedId = ref<string | null>(null)
  const baseRevisionId = ref<string | undefined>(undefined)
  const revisionNo = ref(0)

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
  function addObject(bbox: [number, number, number, number], label: string) {
    saveSnapshot()
    const maxOrder = objects.value.reduce((max, o) => Math.max(max, o.read_order), 0)
    const obj: AnnotationObject = {
      id: generateId(),
      label,
      bbox_xyxy: bbox,
      read_order: maxOrder + 1,
      color: getDefaultColor(label),
    }
    objects.value.push(obj)
    selectedId.value = obj.id
    return obj
  }

  function updateObject(id: string, patch: Partial<Pick<AnnotationObject, 'label' | 'bbox_xyxy' | 'read_order' | 'color'>>) {
    saveSnapshot()
    const obj = objects.value.find(o => o.id === id)
    if (!obj) return
    if (patch.label !== undefined) obj.label = patch.label
    if (patch.bbox_xyxy !== undefined) obj.bbox_xyxy = patch.bbox_xyxy
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
    if (!obj) return
    const [xmin, ymin, xmax, ymax] = obj.bbox_xyxy
    obj.bbox_xyxy = [xmin + dx, ymin + dy, xmax + dx, ymax + dy]
  }

  /** 开始拖拽前保存快照（供 AnnotationCanvas 在 mousedown 时调用） */
  function savePreDragSnapshot() {
    saveSnapshot()
  }

  /** 调整 bbox 大小（通过控制点索引 0-7） */
  function resizeObject(id: string, handleIndex: number, imgX: number, imgY: number) {
    const obj = objects.value.find(o => o.id === id)
    if (!obj) return
    let [xmin, ymin, xmax, ymax] = obj.bbox_xyxy

    // 控制点: 0=上中, 1=右上, 2=右中, 3=右下, 4=下中, 5=左下, 6=左中, 7=左上
    if (handleIndex === 0 || handleIndex === 7 || handleIndex === 6) ymin = imgY  // 上边
    if (handleIndex === 1 || handleIndex === 2 || handleIndex === 3) xmax = imgX  // 右边
    if (handleIndex === 3 || handleIndex === 4 || handleIndex === 5) ymax = imgY  // 下边
    if (handleIndex === 5 || handleIndex === 6 || handleIndex === 7) xmin = imgX  // 左边

    // 确保 xmin < xmax, ymin < ymax
    if (xmin > xmax) [xmin, xmax] = [xmax, xmin]
    if (ymin > ymax) [ymin, ymax] = [ymax, ymin]

    obj.bbox_xyxy = [xmin, ymin, xmax, ymax]
  }

  /** 设置阅读顺序 */
  function setReadOrder(id: string, order: number) {
    saveSnapshot()
    const obj = objects.value.find(o => o.id === id)
    if (obj) obj.read_order = order
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

    const data = revision.data as { objects?: Array<{ id: string; label: string; geometry: { bbox_xyxy: [number, number, number, number] }; read_order: number }> }
    objects.value = (data.objects || []).map(o => ({
      id: o.id,
      label: o.label,
      bbox_xyxy: o.geometry.bbox_xyxy,
      read_order: o.read_order || 0,
      color: getDefaultColor(o.label),
    }))

    undoStack.value = []
    redoStack.value = []
    selectedId.value = null
  }

  /** 导出为 AnnotationDraft */
  function toDraft(pageId: string): AnnotationDraft {
    return {
      page_id: pageId,
      base_revision_id: baseRevisionId.value || '',
      data: {
        objects: objects.value.map(o => ({
          id: o.id,
          label: o.label,
          geometry: { bbox_xyxy: o.bbox_xyxy },
          read_order: o.read_order,
        })),
      },
    }
  }

  return {
    objects,
    selectedId,
    selectedObject,
    baseRevisionId,
    revisionNo,
    canUndo,
    canRedo,
    select,
    addObject,
    updateObject,
    deleteObject,
    deleteSelected,
    moveObject,
    resizeObject,
    setReadOrder,
    savePreDragSnapshot,
    loadFromRevision,
    toDraft,
    undo,
    redo,
  }
}