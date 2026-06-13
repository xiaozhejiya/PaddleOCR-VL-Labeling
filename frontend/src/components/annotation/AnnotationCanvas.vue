<script setup lang="ts">
/**
 * 标注画布组件（Canvas 矩阵渲染架构）
 *
 * 渲染层：固定视口 Canvas（setTransform 矩阵渲染）
 * 交互层：SVG overlay（viewBox 与 Canvas 逻辑尺寸一致）
 * 标注层：BBoxOverlay（视口坐标系）
 *
 * 工具模式：select | bbox | read_order | pan
 * 快捷键：参见 annotation_workspace_interaction_spec.md §15.1
 */
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useCanvasRenderer } from '@/composables/useCanvasRenderer'
import { useAnnotationStore } from '@/composables/useAnnotationStore'
import BBoxOverlay from './BBoxOverlay.vue'

interface Props {
  imageUrl: string | null
  activeTool: 'select' | 'bbox' | 'read_order' | 'pan'
  activeLabel: {
    name: string
    namespace: string
    color?: string | null
  } | null
  qcOverlays?: Array<{
    issueId: string
    severity: 'passed' | 'warning' | 'failed'
    bbox: [number, number, number, number]
  }>
  activeQcIssueId?: string | null
  readonly: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:zoomLevel': [value: number]
  'object-selected': [id: string | null]
  'objects-changed': []
}>()

// ── 核心依赖 ──
const store = useAnnotationStore()
const renderer = useCanvasRenderer()

defineExpose({ store, renderer, redraw })

// ── DOM 引用 ──
const canvasRef = ref<HTMLCanvasElement | null>(null)
const imageLoaded = ref(false)

// ── 鼠标交互状态 ──
const isDragging = ref(false)
const dragType = ref<'move' | 'resize' | 'draw' | 'pan' | null>(null)
const dragStartScreen = ref({ x: 0, y: 0 })
const dragStartImage = ref({ x: 0, y: 0 })
const dragHandleIndex = ref(0)
const dragObjectId = ref<string | null>(null)
const drawStartViewport = ref({ x: 0, y: 0 })

// ── 画框临时矩形（视口坐标） ──
const tempRect = ref<{ x: number; y: number; w: number; h: number } | null>(null)

// ── SVG viewBox（与 Canvas 逻辑尺寸一致） ──
const svgViewBox = computed(() => `0 0 ${renderer.viewport.value.w} ${renderer.viewport.value.h}`)

// ── 将标注对象从原图坐标转换为视口坐标 ──
const viewportObjects = computed(() => {
  return store.objects.value.map(obj => {
    const bbox = obj.geometry.bbox_xyxy
    if (!bbox) return { ...obj, viewportBbox: [0, 0, 0, 0] as [number, number, number, number] }
    const [xmin, ymin, xmax, ymax] = bbox
    const tl = renderer.imageToViewport(xmin, ymin)
    const br = renderer.imageToViewport(xmax, ymax)
    return {
      ...obj,
      viewportBbox: [tl.x, tl.y, br.x, br.y] as [number, number, number, number],
    }
  })
})

const viewportQcOverlays = computed(() => {
  return (props.qcOverlays || []).map((overlay) => {
    const [xmin, ymin, xmax, ymax] = overlay.bbox
    const topLeft = renderer.imageToViewport(xmin, ymin)
    const bottomRight = renderer.imageToViewport(xmax, ymax)
    return {
      ...overlay,
      viewportBbox: [topLeft.x, topLeft.y, bottomRight.x, bottomRight.y] as [number, number, number, number],
    }
  })
})

function getQcOverlayStroke(severity: 'passed' | 'warning' | 'failed'): string {
  if (severity === 'failed') return '#da1e28'
  if (severity === 'warning') return '#dd5b00'
  return '#24a148'
}

// ── 视口坐标 → 原图坐标（标注存储用） ──
function viewportToImage(vpX: number, vpY: number): { x: number; y: number } | null {
  return renderer.screenToImage(vpX, vpY)
}

function clampViewportToImage(vpX: number, vpY: number): { x: number; y: number } | null {
  const point = renderer.screenToImage(vpX, vpY)
  if (point) return point

  const scale = renderer.scale.value
  if (scale === 0) return null

  const maxX = Math.max(renderer.imageSize.value.x, 0)
  const maxY = Math.max(renderer.imageSize.value.y, 0)
  const imgX = (vpX - renderer.offset.value.x) / scale
  const imgY = (vpY - renderer.offset.value.y) / scale

  return {
    x: Math.min(Math.max(imgX, 0), maxX),
    y: Math.min(Math.max(imgY, 0), maxY),
  }
}

// ── 渲染 ──
function redraw() {
  if (!canvasRef.value) return
  renderer.render(canvasRef.value)
}

// ── 图片加载 ──
watch(() => props.imageUrl, async (url) => {
  if (!url) return
  imageLoaded.value = false

  try {
    await renderer.loadImage(url)
    imageLoaded.value = true

    await nextTick()
    if (canvasRef.value) {
      renderer.initCanvas(canvasRef.value)
      renderer.fitToContainer()
      redraw()
      emit('update:zoomLevel', renderer.zoomPercent.value)
    }
  } catch {
    console.error('图片加载失败')
  }
}, { immediate: true })

// ── 滚轮缩放 ──
function onWheel(e: WheelEvent) {
  e.preventDefault()
  const canvas = canvasRef.value
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top
  const delta = e.deltaY > 0 ? -0.1 : 0.1

  renderer.zoomAt(delta, screenX, screenY)
  redraw()
  emit('update:zoomLevel', renderer.zoomPercent.value)
}

// ── 鼠标按下 ──
function onMouseDown(e: MouseEvent) {
  if (e.button !== 0) return

  const canvas = canvasRef.value
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top
  const imgPt = viewportToImage(screenX, screenY)

  // Space 临时平移模式
  if (props.activeTool === 'pan' || spaceHeld.value) {
    dragStartScreen.value = { x: screenX, y: screenY }
    isDragging.value = true
    dragType.value = 'pan'
    return
  }

  // bbox 工具：画新框
  if (props.activeTool === 'bbox' && !props.readonly) {
    if (!imgPt) return
    isDragging.value = true
    dragType.value = 'draw'
    drawStartViewport.value = { x: screenX, y: screenY }
    tempRect.value = { x: screenX, y: screenY, w: 0, h: 0 }
    return
  }

  // 选择工具：点击空白取消选中
  if (props.activeTool === 'select') {
    store.select(null)
    emit('object-selected', null)
  }
}

// ── 鼠标移动 ──
function onMouseMove(e: MouseEvent) {
  if (!isDragging.value) return

  const canvas = canvasRef.value
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top

  if (dragType.value === 'pan') {
    const dx = screenX - dragStartScreen.value.x
    const dy = screenY - dragStartScreen.value.y
    renderer.pan(dx, dy)
    redraw()
    dragStartScreen.value = { x: screenX, y: screenY }
    emit('update:zoomLevel', renderer.zoomPercent.value)
    return
  }

  if (dragType.value === 'draw' && tempRect.value) {
    const sx = drawStartViewport.value.x
    const sy = drawStartViewport.value.y
    tempRect.value = {
      x: Math.min(sx, screenX),
      y: Math.min(sy, screenY),
      w: Math.abs(screenX - sx),
      h: Math.abs(screenY - sy),
    }
    return
  }

  if (dragType.value === 'move' && dragObjectId.value) {
    const imgPt = clampViewportToImage(screenX, screenY)
    if (!imgPt) return
    const dx = imgPt.x - dragStartImage.value.x
    const dy = imgPt.y - dragStartImage.value.y
    store.moveObject(dragObjectId.value, dx, dy)
    dragStartImage.value = imgPt
    emit('objects-changed')
    return
  }

  if (dragType.value === 'resize' && dragObjectId.value) {
    const imgPt = clampViewportToImage(screenX, screenY)
    if (!imgPt) return
    store.resizeObject(dragObjectId.value, dragHandleIndex.value, imgPt.x, imgPt.y)
    emit('objects-changed')
    return
  }
}

// ── 鼠标释放 ──
function onMouseUp() {
  if (dragType.value === 'draw' && tempRect.value) {
    const { x, y, w, h } = tempRect.value
    // 最小面积检查（视口坐标像素）
    if (w > 3 && h > 3) {
      // 图片外释放时按图像边界 clamp，禁止把视口坐标写成原图坐标。
      const topLeft = clampViewportToImage(x, y)
      const bottomRight = clampViewportToImage(x + w, y + h)
      if (topLeft && bottomRight && Math.abs(bottomRight.x - topLeft.x) > 0 && Math.abs(bottomRight.y - topLeft.y) > 0) {
        if (!props.activeLabel) {
          tempRect.value = null
          return
        }
        store.addObject([topLeft.x, topLeft.y, bottomRight.x, bottomRight.y], props.activeLabel)
        emit('objects-changed')
      }
    }
    tempRect.value = null
  }

  isDragging.value = false
  dragType.value = null
  dragObjectId.value = null
}

// ── BBox 事件处理 ──
function onBBoxSelect(id: string) {
  store.select(id)
  emit('object-selected', id)

  if (props.activeTool === 'read_order') {
    if (props.readonly) return
    const nextOrder = store.assignNextReadOrder(id)
    if (nextOrder !== null) {
      emit('objects-changed')
    }
  }
}

function onBBoxDragStart(id: string, e: MouseEvent) {
  if (props.readonly) return
  if (props.activeTool !== 'select') return
  e.stopPropagation()

  const canvas = canvasRef.value
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top
  const imgPt = viewportToImage(screenX, screenY)
  if (!imgPt) return

  store.savePreDragSnapshot()
  isDragging.value = true
  dragType.value = 'move'
  dragObjectId.value = id
  dragStartImage.value = imgPt
}

function onBBoxHandleDragStart(id: string, handleIndex: number, e: MouseEvent) {
  if (props.readonly) return
  if (props.activeTool !== 'select') return
  e.stopPropagation()
  store.savePreDragSnapshot()
  isDragging.value = true
  dragType.value = 'resize'
  dragObjectId.value = id
  dragHandleIndex.value = handleIndex
}

// ── 键盘快捷键（对齐 annotation_workspace_interaction_spec.md §15.1） ──
const spaceHeld = ref(false)

function onKeyDown(e: KeyboardEvent) {
  // 忽略输入框内的按键（§15.3）
  const tag = (e.target as HTMLElement)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
  if (e.defaultPrevented) return

  // Space: 临时平移
  if (e.key === ' ') {
    e.preventDefault()
    spaceHeld.value = true
  }

  // Delete/Backspace: 删除选中对象（§15.1）
  if (!props.readonly && (e.key === 'Delete' || e.key === 'Backspace' || e.key === 'Del' || e.code === 'Delete')) {
    e.preventDefault()
    if (store.selectedId.value) {
      store.deleteSelected()
      emit('objects-changed')
    }
  }

  // Ctrl+Z: 撤销（§15.1）
  if (!props.readonly && e.ctrlKey && e.key === 'z') {
    e.preventDefault()
    store.undo()
    emit('objects-changed')
  }

  // Ctrl+Y / Ctrl+Shift+Z: 重做（§15.1）
  if (!props.readonly && e.ctrlKey && (e.key === 'y' || (e.shiftKey && e.key === 'Z'))) {
    e.preventDefault()
    store.redo()
    emit('objects-changed')
  }

  // 方向键: 微调选中 bbox 1px, Shift+方向键 10px（§15.1, §9）
  if (!props.readonly && ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key) && store.selectedId.value) {
    e.preventDefault()
    const step = e.shiftKey ? 10 : 1
    let dx = 0, dy = 0
    if (e.key === 'ArrowUp') dy = -step
    if (e.key === 'ArrowDown') dy = step
    if (e.key === 'ArrowLeft') dx = -step
    if (e.key === 'ArrowRight') dx = step
    store.savePreDragSnapshot()
    store.moveObject(store.selectedId.value, dx, dy)
    emit('objects-changed')
  }

  // Esc: 取消选择（§15.1）
  if (e.key === 'Escape') {
    store.select(null)
    emit('object-selected', null)
    tempRect.value = null
    isDragging.value = false
    dragType.value = null
  }
}

function onKeyUp(e: KeyboardEvent) {
  if (e.key === ' ') {
    spaceHeld.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
})

// ── 光标样式 ──
const cursorClass = computed(() => {
  if (spaceHeld.value || props.activeTool === 'pan') return 'cursor-grab'
  if (props.activeTool === 'bbox') return 'cursor-crosshair'
  if (props.activeTool === 'read_order') return 'cursor-pointer'
  return 'cursor-default'
})
</script>

<template>
  <div
    :class="['relative w-full h-full overflow-hidden bg-bg-canvas select-none flex items-center justify-center', cursorClass]"
    @wheel.prevent="onWheel">
    <!-- 加载中 -->
    <div v-if="!imageLoaded" class="absolute inset-0 flex items-center justify-center text-text-muted">
      <div class="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Canvas + SVG 叠加层（固定视口） -->
    <div v-show="imageLoaded" class="relative" style="width: 800px; height: 600px;">
      <!-- 渲染层：Canvas（物理尺寸锁定，矩阵变换绘图） -->
      <canvas ref="canvasRef" class="block" style="width: 800px; height: 600px;" />

      <!-- 交互层：SVG overlay（viewBox 与 Canvas 逻辑尺寸一致） -->
      <svg class="absolute top-0 left-0" style="width: 800px; height: 600px;" :viewBox="svgViewBox"
        xmlns="http://www.w3.org/2000/svg" @mousedown.left="onMouseDown" @mousemove="onMouseMove"
        @mouseup.left="onMouseUp" @mouseleave="onMouseUp">
        <rect v-for="overlay in viewportQcOverlays" :key="`qc-${overlay.issueId}`" :x="overlay.viewportBbox[0]"
          :y="overlay.viewportBbox[1]" :width="Math.max(overlay.viewportBbox[2] - overlay.viewportBbox[0], 1)"
          :height="Math.max(overlay.viewportBbox[3] - overlay.viewportBbox[1], 1)" fill="none"
          :stroke="getQcOverlayStroke(overlay.severity)"
          :stroke-width="props.activeQcIssueId === overlay.issueId ? 3 : 2"
          :stroke-dasharray="props.activeQcIssueId === overlay.issueId ? '8 4' : '4 3'" opacity="0.9"
          pointer-events="none" />

        <!-- 已有标注对象（视口坐标） -->
        <BBoxOverlay v-for="obj in viewportObjects" :key="obj.id" :obj="obj"
          :selected="store.selectedId.value === obj.id" :label-name="obj.type" :active-tool="props.activeTool"
          @select="onBBoxSelect(obj.id)" @drag-start="(e) => onBBoxDragStart(obj.id, e)"
          @handle-drag-start="(idx, e) => onBBoxHandleDragStart(obj.id, idx, e)" />

        <!-- 画框临时矩形（视口坐标） -->
        <rect v-if="tempRect" :x="tempRect.x" :y="tempRect.y" :width="tempRect.w" :height="tempRect.h"
          fill="rgba(94, 106, 210, 0.1)" stroke="#5e6ad2" stroke-width="2" stroke-dasharray="6 3"
          pointer-events="none" />
      </svg>
    </div>
  </div>
</template>
